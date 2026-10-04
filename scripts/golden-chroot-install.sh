#!/usr/bin/env bash
# Runs INSIDE the golden-image chroot as root: installs Fieldkit, enables the
# services without starting them, and optionally syspreps the image.
#
# GOLDEN_MODE=install  -> install everything (slow apt phase)
# GOLDEN_MODE=sysprep  -> sysprep only (used on refresh builds)
# GOLDEN_MODE=all      -> both (default)
#
# BASE_PROFILE:
#   rpi-os        Raspberry Pi OS Lite 64-bit (Trixie): MBR p1 boot / p2 root,
#                 NetworkManager, native first-boot resize + SSH keygen.
#   debian-cloud  legacy Debian cloud image (GPT root p1 / boot p15).
set -euo pipefail

export DEBIAN_FRONTEND=noninteractive
GOLDEN_MODE=${GOLDEN_MODE:-all}
BASE_PROFILE=${BASE_PROFILE:-rpi-os}
FIELDKIT_ROOT=${FIELDKIT_ROOT:-/opt/fieldkit}

log() {
  printf '\n==> %s\n' "$*"
}

# systemctl shim: package postinst scripts and the installer call `systemctl`
# during a chroot where no systemd is running. Offline unit-state operations
# (enable/disable/mask/...) are delegated to the real systemctl in --root mode;
# operations that need a running systemd are no-ops. The strict helper `sysd`
# below is used for the final state enforcement so those errors are NOT hidden.
systemctl() {
  local cmd="$1"
  shift || true
  case "${cmd}" in
    daemon-reload) return 0 ;;
    enable|disable|mask|unmask|preset|is-enabled)
      local args=()
      local a
      for a in "$@"; do
        [[ "${a}" == "--now" ]] && continue
        args+=("${a}")
      done
      /usr/bin/systemctl --root=/ "${cmd}" "${args[@]}" 2>/dev/null || true
      return 0 ;;
    *) return 0 ;;
  esac
}
export -f systemctl

# Strict offline systemctl: bypasses the shim and propagates failures.
sysd() {
  /usr/bin/systemctl --root=/ "$@"
}

# hostnamectl shim: no systemd bus inside the chroot.
hostnamectl() {
  if [[ "$1" == "set-hostname" ]]; then
    printf '%s\n' "$2" > /etc/hostname
  fi
  return 0
}
export -f hostnamectl

install_fieldkit() {
  log "OS packages (${BASE_PROFILE})"
  apt-get update
  if [[ "${BASE_PROFILE}" == "rpi-os" ]]; then
    # gdisk/cloud-guest-utils belong to the retired custom growroot path; the
    # RPi OS profile uses the native first-boot resize instead.
    apt-get install -y --no-install-recommends \
      ca-certificates curl e2fsprogs git sudo
  else
    apt-get install -y --no-install-recommends \
      ca-certificates cloud-guest-utils curl e2fsprogs gdisk git sudo
  fi

  log "Installing Fieldkit"
  FIELDKIT_USER=service \
  FIELDKIT_PASS=service \
  FIELDKIT_HOSTNAME=fieldkit \
  INSTALL_OS_PACKAGES=1 \
  INSTALL_AP_SUPPORT=1 \
  INSTALL_TRANSFER_SUPPORT=1 \
  START_SERVICES=0 \
  bash "${FIELDKIT_ROOT}/scripts/install_fieldkit.sh"

  log "First-boot SSH: password login on, host keys regenerated on boot"
  if [[ -f /etc/ssh/sshd_config ]]; then
    sed -i 's/^#\?PasswordAuthentication.*/PasswordAuthentication yes/' /etc/ssh/sshd_config
  fi
}

enforce_image_state() {
  if [[ "${BASE_PROFILE}" == "rpi-os" ]]; then
    enforce_image_state_rpi
  else
    enforce_image_state_debian
  fi
}

enforce_image_state_rpi() {
  log "Enforcing offline service state (rpi-os)"
  # Required services. Errors here are fatal: a wrong state is a broken image.
  sysd enable \
    rpi-resize.service regenerate_ssh_host_keys.service sshd-keygen.service \
    ssh.service NetworkManager.service wpa_supplicant.service \
    avahi-daemon.service getty@tty1.service nginx.service \
    fieldkit-web.service fieldkit-startup-network.timer \
    fieldkit-server-sync.timer fieldkit-tls-cert.service

  # Units Fieldkit starts itself at runtime must be installed disabled.
  sysd disable fieldkit-ap-hostapd.service fieldkit-ap-dnsmasq.service

  # Fieldkit owns network management; make sure only one manager is active and
  # the console/getty can never wait on the network.
  sysd disable \
    systemd-networkd.service systemd-networkd-wait-online.service \
    NetworkManager-wait-online.service e2scrub_reap.service e2scrub_all.timer
  if [[ -e /lib/systemd/system/dhcpcd.service ]]; then
    sysd disable dhcpcd.service || true
  fi

  # Mask the units that must never run: distro AP daemons (Fieldkit uses its
  # own), the interactive user rename dialog, ssh-switch helper, automated
  # EEPROM/scrub work, and cloud-init (seedless here and only adds boot risk).
  sysd mask \
    systemd-networkd.service systemd-networkd-wait-online.service \
    NetworkManager-wait-online.service hostapd.service dnsmasq.service \
    userconfig.service sshswitch.service rpi-eeprom-update.service \
    e2scrub_reap.service \
    cloud-init-local.service cloud-init-main.service \
    cloud-init-network.service cloud-config.service cloud-final.service \
    cloud-init-hotplugd.socket
  # The interactive systemd-firstboot wizard runs on the console because we keep
  # /etc/machine-id as `uninitialized` for the native resize + SSH keygen. It
  # must never prompt on a field kit.
  sysd mask systemd-firstboot.service
}

enforce_image_state_debian() {
  log "Enforcing offline service state (debian-cloud)"
  sysd enable \
    ssh.service sshd-keygen.service nginx.service NetworkManager.service \
    avahi-daemon.service getty@tty1.service fieldkit-web.service \
    fieldkit-startup-network.timer fieldkit-server-sync.timer \
    fieldkit-growroot.timer || true
  sysd disable systemd-networkd.service systemd-networkd-wait-online.service || true
  sysd mask hostapd.service dnsmasq.service || true
}

seed_nm_wired() {
  # Explicit DHCP profile for the wired NIC. Interface naming is preserved as
  # the kernel name (the RPi OS /etc/systemd/network/99-default.link policy
  # keeps eth0/wlan0), so this keyfile matches the onboard Ethernet.
  mkdir -p /etc/NetworkManager/system-connections
  cat > /etc/NetworkManager/system-connections/fieldkit-wired.nmconnection <<'EOF'
[connection]
id=fieldkit-wired
type=ethernet
interface-name=eth0
autoconnect=true
autoconnect-priority=100

[ipv4]
method=auto

[ipv6]
method=auto
EOF
  chmod 0600 /etc/NetworkManager/system-connections/fieldkit-wired.nmconnection
}

seed_nginx_config() {
  # Refresh builds never re-run the installer, so re-seed the nginx site from
  # the repo (HTTP 80 + self-signed HTTPS 443). The per-device TLS key is
  # generated on first boot by fieldkit-tls-cert.service.
  local conf=/etc/nginx/sites-available/fieldkit
  [[ -f "${FIELDKIT_ROOT}/deploy/nginx/fieldkit.conf" ]] || return 0
  install -D -m 0644 "${FIELDKIT_ROOT}/deploy/nginx/fieldkit.conf" "${conf}"
  mkdir -p /etc/nginx/sites-enabled
  ln -sf "${conf}" /etc/nginx/sites-enabled/fieldkit
  rm -f /etc/nginx/sites-enabled/default
}

patch_boot_config() {
  if [[ "${BASE_PROFILE}" == "rpi-os" ]]; then
    patch_boot_config_rpi
  else
    patch_boot_config_debian
  fi
}

patch_boot_config_rpi() {
  # Raspberry Pi OS already boots a console on serial0 and tty1 and has the
  # `resize` first-boot grow token. Assert them rather than rewriting, and add
  # the UART enable so the serial console works on Pi 3/4/5.
  local cmdline=/boot/firmware/cmdline.txt
  local config=/boot/firmware/config.txt
  [[ -f "${cmdline}" ]] || { echo "missing ${cmdline}"; exit 1; }
  [[ -f "${config}" ]] || { echo "missing ${config}"; exit 1; }
  grep -qw 'console=serial0,115200' "${cmdline}" || { echo "cmdline lost console=serial0,115200"; exit 1; }
  grep -qw 'console=tty1' "${cmdline}" || { echo "cmdline lost console=tty1"; exit 1; }
  grep -qw 'resize' "${cmdline}" || { echo "cmdline lost resize"; exit 1; }
  grep -q '^enable_uart=1' "${config}" || \
    printf '\n[all]\nenable_uart=1\n' >> "${config}"

  # Keep the initramfs coherent (it must keep resize_early). A failure here is
  # fatal: finding resize_early in a stale initramfs does not prove the kernel
  # and initramfs match after the install.
  command -v update-initramfs >/dev/null 2>&1 || { echo "update-initramfs is required"; exit 1; }
  update-initramfs -u -k all
}

patch_boot_config_debian() {
  for cmdline in /boot/firmware/cmdline.txt /boot/cmdline.txt; do
    [[ -f "${cmdline}" ]] || continue
    sed -i 's/console=tty0/console=tty1/' "${cmdline}"
    sed -i 's/console=ttyS1,115200/console=serial0,115200/' "${cmdline}"
    grep -q 'console=tty1' "${cmdline}" || sed -i '1s/^/console=tty1 /' "${cmdline}"
  done
  for config in /boot/firmware/config.txt /boot/config.txt; do
    [[ -f "${config}" ]] || continue
    grep -q '^enable_uart=1' "${config}" || printf '\n# Fieldkit serial console\nenable_uart=1\n' >> "${config}"
  done
}

sysprep() {
  log "Sysprep (${BASE_PROFILE})"
  # Remove host keys so the first boot regenerates unique ones.
  rm -f /etc/ssh/ssh_host_*_key /etc/ssh/ssh_host_*_key.pub

  if [[ "${BASE_PROFILE}" != "rpi-os" ]]; then
    install_growroot
  else
    # The native RPi OS resize path is authoritative; drop any stale custom
    # growroot from a previous image build.
    rm -f /etc/fieldkit-growroot /usr/local/sbin/fieldkit-growroot.sh \
      /etc/systemd/system/fieldkit-growroot.service \
      /etc/systemd/system/fieldkit-growroot.timer
  fi

  # Refresh the Fieldkit systemd units from the current repo: refresh builds run
  # only sysprep (not the installer), so changed/new units must be reinstalled.
  for unit in \
    fieldkit-web.service fieldkit-startup-network.service \
    fieldkit-startup-network.timer fieldkit-post-update.service \
    fieldkit-server-sync.service fieldkit-server-sync.timer \
    fieldkit-ap-hostapd.service fieldkit-ap-dnsmasq.service \
    fieldkit-tls-cert.service fieldkit-rollback.service; do
    if [[ ! -f "${FIELDKIT_ROOT}/deploy/systemd/${unit}" ]]; then
      echo "missing required unit file: ${unit}"
      exit 1
    fi
    install -D -m 0644 "${FIELDKIT_ROOT}/deploy/systemd/${unit}" "/etc/systemd/system/${unit}"
  done
  install -D -m 0644 "${FIELDKIT_ROOT}/deploy/systemd/nginx-fieldkit-tls.conf" \
    /etc/systemd/system/nginx.service.d/10-fieldkit-tls.conf

  # Pin the intended unit state against first-boot systemd presets.
  install -D -m 0644 "${FIELDKIT_ROOT}/deploy/systemd/00-fieldkit.preset" \
    /etc/systemd/system-preset/00-fieldkit.preset

  enforce_image_state
  seed_nm_wired
  seed_nginx_config
  patch_boot_config

  if [[ "${BASE_PROFILE}" == "rpi-os" ]]; then
    # Disable cloud-init and the interactive user-rename dialog; make sure the
    # service account can log in over SSH with a password.
    touch /etc/cloud/cloud-init.disabled
    rm -f /etc/ssh/sshd_config.d/rename_user.conf
    install -d -m 0755 /etc/ssh/sshd_config.d
    printf 'PasswordAuthentication yes\n' > /etc/ssh/sshd_config.d/00-fieldkit.conf
    chmod 0644 /etc/ssh/sshd_config.d/00-fieldkit.conf
    # No leftover Imager seed should steer first boot.
    rm -f /boot/firmware/user-data /boot/firmware/meta-data \
      /boot/firmware/network-config /boot/firmware/ssh /boot/firmware/ssh.txt \
      /boot/firmware/firstrun.sh 2>/dev/null || true
    # Do not ship a shared build-time TLS key: the first boot regenerates a
    # unique cert via fieldkit-tls-cert.service before nginx starts.
    rm -f /etc/nginx/ssl/fieldkit.crt /etc/nginx/ssl/fieldkit.key
  else
    touch /etc/cloud/cloud-init.disabled 2>/dev/null || true
  fi

  # Keep the journal across boots so a failed first boot can be diagnosed from
  # the SD card.
  mkdir -p /etc/systemd/journald.conf.d
  printf '[Journal]\nStorage=persistent\n' > /etc/systemd/journald.conf.d/fieldkit.conf

  find /var/log -type f -delete 2>/dev/null || true
  rm -rf /tmp/* /var/tmp/* 2>/dev/null || true
  rm -f /root/.bash_history /home/service/.bash_history 2>/dev/null || true
  rm -rf "${FIELDKIT_ROOT}/runtime/content"/* "${FIELDKIT_ROOT}/runtime/state"/* 2>/dev/null || true

  # Re-assert the groups the app user needs (vcgencmd/input voltage, serial,
  # networking): refresh builds run only sysprep, so they never re-run the
  # installer's usermod. Idempotent.
  for grp in sudo dialout netdev plugdev video render gpio i2c; do
    getent group "${grp}" >/dev/null 2>&1 && usermod -aG "${grp}" service || true
  done

  # Recreate the runtime layout owned by the web account. The cleanup above
  # removes the data/personal/usb/export dirs, and a refresh `rsync -a` can
  # stamp the tree with the builder's uid, so re-assert ownership and rebuild
  # the dirs here (the app runs as `service` and cannot mkdir under a
  # root-owned runtime/content).
  chown -R service:service "${FIELDKIT_ROOT}"
  chown -R root:root "${FIELDKIT_ROOT}/scripts" "${FIELDKIT_ROOT}/deploy"
  chmod 0755 "${FIELDKIT_ROOT}/scripts" "${FIELDKIT_ROOT}/deploy"
  find "${FIELDKIT_ROOT}/scripts" -maxdepth 1 -name '*.sh' -exec chmod 0755 {} + 2>/dev/null || true
  install -d -o service -g service -m 0755 \
    "${FIELDKIT_ROOT}/runtime/content/data" \
    "${FIELDKIT_ROOT}/runtime/content/personal" \
    "${FIELDKIT_ROOT}/runtime/content/usb" \
    "${FIELDKIT_ROOT}/runtime/content/fieldkit"
  install -d -o service -g service -m 0700 "${FIELDKIT_ROOT}/runtime/state"

  # Seed a default settings.json so the first boot brings up the Wi-Fi AP and
  # applies the hostname (the startup-network unit needs this file).
  FIELDKIT_ROOT="${FIELDKIT_ROOT}" "${FIELDKIT_ROOT}/.venv/bin/python" - <<'PY'
import json
import os
from pathlib import Path

from app.core.models import AppSettingsPayload

root = Path(os.environ["FIELDKIT_ROOT"])
path = root / "runtime/state/settings.json"
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text(json.dumps(AppSettingsPayload().model_dump(), indent=2))
PY
  chown service:service "${FIELDKIT_ROOT}/runtime/state/settings.json"
  chmod 0600 "${FIELDKIT_ROOT}/runtime/state/settings.json"

  find "${FIELDKIT_ROOT}" -name '__pycache__' -type d -prune -exec rm -rf {} + 2>/dev/null || true

  # Last identity action: force the systemd first-boot marker so the native
  # resize and SSH host-key generation run exactly once on first boot.
  printf 'uninitialized\n' > /etc/machine-id
  rm -f /var/lib/dbus/machine-id 2>/dev/null || true

  sync
}

install_growroot() {
  log "Arming first-boot root partition grow (debian-cloud)"
  install -D -m 0755 "${FIELDKIT_ROOT}/scripts/fieldkit-growroot.sh" /usr/local/sbin/fieldkit-growroot.sh
  install -D -m 0644 "${FIELDKIT_ROOT}/deploy/systemd/fieldkit-growroot.service" /etc/systemd/system/fieldkit-growroot.service
  install -D -m 0644 "${FIELDKIT_ROOT}/deploy/systemd/fieldkit-growroot.timer" /etc/systemd/system/fieldkit-growroot.timer
  sysd enable fieldkit-growroot.timer
  touch /etc/fieldkit-growroot
}

case "${GOLDEN_MODE}" in
  install) install_fieldkit ;;
  sysprep) sysprep ;;
  *) install_fieldkit; sysprep ;;
esac

log "Golden chroot step complete (${GOLDEN_MODE}, ${BASE_PROFILE})"
