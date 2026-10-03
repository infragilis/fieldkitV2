#!/usr/bin/env bash
# Runs INSIDE the golden-image chroot as root: installs Fieldkit, enables the
# services without starting them, and optionally syspreps the image.
#
# GOLDEN_MODE=install  -> install everything (slow apt phase)
# GOLDEN_MODE=sysprep  -> sysprep only (used on refresh builds)
# GOLDEN_MODE=all      -> both (default)
set -euo pipefail

export DEBIAN_FRONTEND=noninteractive
GOLDEN_MODE=${GOLDEN_MODE:-all}
FIELDKIT_ROOT=${FIELDKIT_ROOT:-/opt/fieldkit}

log() {
  printf '\n==> %s\n' "$*"
}

# systemctl shim: offline unit-state operations (enable/disable/mask/...) are
# delegated to the real systemctl in --root mode, which resolves units from
# /usr/lib/systemd/system, handles templates/aliases, and implements masking.
# Operations that need a running systemd are no-ops inside the chroot.
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

# hostnamectl shim: no systemd bus inside the chroot.
hostnamectl() {
  if [[ "$1" == "set-hostname" ]]; then
    printf '%s\n' "$2" > /etc/hostname
  fi
  return 0
}
export -f hostnamectl

install_fieldkit() {
  log "OS packages"
  apt-get update
  apt-get install -y --no-install-recommends \
    ca-certificates cloud-guest-utils curl e2fsprogs gdisk git sudo

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
  log "Enforcing offline service state"
  # Real offline systemd operations (the shim delegates to --root=/).
  systemctl enable \
    ssh.service sshd-keygen.service nginx.service NetworkManager.service \
    avahi-daemon.service getty@tty1.service fieldkit-web.service \
    fieldkit-server-sync.timer fieldkit-startup-network.timer \
    fieldkit-growroot.timer
  # One network manager only: NetworkManager (Fieldkit's UI uses nmcli).
  systemctl disable systemd-networkd.service systemd-networkd-wait-online.service
  # Fieldkit uses its own fieldkit-ap-* units; block the distro daemons.
  systemctl mask hostapd.service dnsmasq.service
}

seed_nm_wired() {
  # Explicit DHCP profile for the wired NIC (interface is eth0: net.ifnames=0),
  # so Ethernet works even with networkd disabled and netplan unused.
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

patch_boot_config() {
  # Ensure an HDMI login on tty1 and a model-independent serial console.
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
  log "Sysprep"
  # Remove host keys so the first boot regenerates unique ones via sshd-keygen.
  rm -f /etc/ssh/ssh_host_*_key /etc/ssh/ssh_host_*_key.pub
  install_growroot
  enforce_image_state
  seed_nm_wired
  patch_boot_config
  # Keep the journal across boots so a failed first boot can be diagnosed from
  # the SD card.
  mkdir -p /etc/systemd/journald.conf.d
  printf '[Journal]\nStorage=persistent\n' > /etc/systemd/journald.conf.d/fieldkit.conf
  touch /etc/cloud/cloud-init.disabled 2>/dev/null || true
  find /var/log -type f -delete 2>/dev/null || true
  rm -rf /tmp/* /var/tmp/* 2>/dev/null || true
  rm -f /root/.bash_history /home/service/.bash_history 2>/dev/null || true
  rm -rf "${FIELDKIT_ROOT}/runtime/content"/* "${FIELDKIT_ROOT}/runtime/state"/* 2>/dev/null || true
  # Seed a default settings.json so the first boot brings up the Wi-Fi AP and
  # applies the hostname (the startup-network unit needs this file). Without
  # it the unit skips and a fresh kit is unreachable until a UI visit.
  FIELDKIT_ROOT="${FIELDKIT_ROOT}" "${FIELDKIT_ROOT}/.venv/bin/python" - <<'PY' 2>/dev/null || true
import json
import os
from pathlib import Path

from app.core.models import AppSettingsPayload

root = Path(os.environ["FIELDKIT_ROOT"])
path = root / "runtime/state/settings.json"
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text(json.dumps(AppSettingsPayload().model_dump(), indent=2))
PY
  chown service:service "${FIELDKIT_ROOT}/runtime/state/settings.json" 2>/dev/null || true
  chmod 0600 "${FIELDKIT_ROOT}/runtime/state/settings.json" 2>/dev/null || true
  find "${FIELDKIT_ROOT}" -name '__pycache__' -type d -prune -exec rm -rf {} + 2>/dev/null || true
  sync
}

install_growroot() {
  log "Arming first-boot root partition grow"
  install -D -m 0755 "${FIELDKIT_ROOT}/scripts/fieldkit-growroot.sh" /usr/local/sbin/fieldkit-growroot.sh
  install -D -m 0644 "${FIELDKIT_ROOT}/deploy/systemd/fieldkit-growroot.service" /etc/systemd/system/fieldkit-growroot.service
  install -D -m 0644 "${FIELDKIT_ROOT}/deploy/systemd/fieldkit-growroot.timer" /etc/systemd/system/fieldkit-growroot.timer
  systemctl enable fieldkit-growroot.timer
  touch /etc/fieldkit-growroot
}

case "${GOLDEN_MODE}" in
  install) install_fieldkit ;;
  sysprep) sysprep ;;
  *) install_fieldkit; sysprep ;;
esac

log "Golden chroot step complete (${GOLDEN_MODE})"

