#!/usr/bin/env bash
# Strict, fail-closed offline audit of a built Fieldkit golden image.
#
# Runs the assertions the Codex team required before an image may be published:
# the intended unit state, the MBR layout / PARTUUIDs, the boot cmdline, the
# serial console, first-boot resize hooks, the machine-id first-boot marker, and
# the network plumbing. ANY mismatch, missing tool, or unreadable target aborts
# non-zero so the build/refresh script cannot silently ship a bad image.
#
# Environment:
#   GOLDEN_MNT     mount point of the root filesystem (required)
#   GOLDEN_IMG     path to the raw (uncompressed) image file (required)
#   GOLDEN_LOOP    loop device backing GOLDEN_IMG (required for rpi-os)
#   BASE_PROFILE   rpi-os (default) or debian-cloud
#
# See docs/golden-image-build.md.
set -euo pipefail

M=${GOLDEN_MNT:?GOLDEN_MNT is required}
IMG=${GOLDEN_IMG:?GOLDEN_IMG is required}
LOOP=${GOLDEN_LOOP:-}
PROFILE=${BASE_PROFILE:-rpi-os}
DISK_ID=0x4d8fd085

fail() {
  printf 'AUDIT FAIL: %s\n' "$*" >&2
  exit 1
}

note() {
  printf '  audit: %s\n' "$*"
}

expect_state() {
  local unit=$1 expected=$2 actual
  actual="$(/usr/bin/systemctl --root="${M}" is-enabled "${unit}" 2>/dev/null || true)"
  [[ "${actual}" == "${expected}" ]] || \
    fail "${unit}: expected '${expected}', got '${actual:-not-found}'"
}

expect_enabled() { expect_state "$1" enabled; }
expect_disabled() { expect_state "$1" disabled; }
expect_masked() { expect_state "$1" masked; }

initramfs_has() {
  # Capture the listing once: under `set -o pipefail`, `lsinitramfs | grep -q`
  # returns 141 (SIGPIPE) when grep exits on the first match. Propagate an
  # lsinitramfs failure explicitly so a partial listing cannot pass the check.
  local listing rc=0
  listing="$(lsinitramfs "$1" 2>/dev/null)" || rc=$?
  [[ ${rc} -eq 0 ]] || return "${rc}"
  grep -qx "$2" <<<"${listing}"
}

# --- Required tooling and target ------------------------------------------------
case "${PROFILE}" in
  rpi-os) ;;
  *) fail "audit does not support BASE_PROFILE='${PROFILE}' (only rpi-os is publishable)" ;;
esac

note "required tooling and mounted target"
for tool in /usr/bin/systemctl sfdisk blkid dumpe2fs lsinitramfs chroot systemd-analyze; do
  command -v "${tool}" >/dev/null 2>&1 || [[ -x "${tool}" ]] || fail "required tool missing: ${tool}"
done
[[ -d "${M}/etc" ]] || fail "GOLDEN_MNT (${M}) does not look like a root filesystem"
chroot "${M}" /bin/true 2>/dev/null || fail "chroot into the image failed (need qemu-user-static/binfmt)"
if [[ "${PROFILE}" == "rpi-os" ]]; then
  [[ -n "${LOOP}" && -b "${LOOP}" ]] || fail "GOLDEN_LOOP must be a block device for rpi-os"
  mountpoint -q "${M}" || fail "${M} is not a mount point"
fi

# --- MBR layout / PARTUUIDs -----------------------------------------------------
if [[ "${PROFILE}" == "rpi-os" ]]; then
  note "MBR label, disk-id, partition types, PARTUUIDs"
  sfdisk_out="$(sfdisk -d "${IMG}")" || fail "sfdisk -d failed on ${IMG}"
  grep -q '^label: dos' <<<"${sfdisk_out}" || fail "image is not an MBR (dos) disk"
  # Trim whitespace: util-linux 2.39 pads `--part-type` output with a leading space.
  [[ "$(sfdisk --disk-id "${IMG}" | tr -d '[:space:]')" == "${DISK_ID}" ]] || fail "unexpected disk id"
  [[ "$(sfdisk --part-type "${IMG}" 1 | tr -d '[:space:]')" == "c" ]] || fail "p1 is not FAT (type c)"
  [[ "$(sfdisk --part-type "${IMG}" 2 | tr -d '[:space:]')" == "83" ]] || fail "p2 is not Linux (type 83)"
  mapfile -t parts < <(grep -E ' : start=' <<<"${sfdisk_out}")
  [[ "${#parts[@]}" -eq 2 ]] || fail "expected exactly 2 partitions, found ${#parts[@]}"
  grep -q 'start= *1064960,' <<<"${parts[1]}" || fail "p2 does not start at the expected sector"
  [[ "$(blkid -s PARTUUID -o value "${LOOP}p1")" == "4d8fd085-01" ]] || fail "p1 PARTUUID changed"
  [[ "$(blkid -s PARTUUID -o value "${LOOP}p2")" == "4d8fd085-02" ]] || fail "p2 PARTUUID changed"

  # p2 must extend to the end of the working image, and the ext4 filesystem must
  # fill p2 (proves the build-time root expansion actually took effect).
  img_sectors=$(( $(stat -c %s "${IMG}") / 512 ))
  p2_start="$(sed -n 's/.*start= *\([0-9]*\),.*/\1/p' <<<"${parts[1]}")"
  p2_size="$(sed -n 's/.*size= *\([0-9]*\).*/\1/p' <<<"${parts[1]}")"
  [[ -n "${p2_start}" && -n "${p2_size}" ]] || fail "could not parse p2 geometry"
  [[ $(( p2_start + p2_size )) -eq "${img_sectors}" ]] || fail "p2 does not extend to the image end"
  p2_bytes=$(( p2_size * 512 ))
  block_size="$(dumpe2fs -h "${LOOP}p2" 2>/dev/null | awk -F: '/Block size/ {gsub(/ /,"",$2); print $2}')"
  block_count="$(dumpe2fs -h "${LOOP}p2" 2>/dev/null | awk -F: '/Block count/ {gsub(/ /,"",$2); print $2}')"
  [[ -n "${block_size}" && -n "${block_count}" ]] || fail "could not read ext4 geometry from p2"
  fs_bytes=$(( block_size * block_count ))
  if [[ ${fs_bytes} -gt ${p2_bytes} || $(( p2_bytes - fs_bytes )) -ge ${block_size} ]]; then
    fail "root filesystem does not fill p2"
  fi

  note "fstab references the expected PARTUUIDs"
  grep -Fx 'PARTUUID=4d8fd085-01  /boot/firmware  vfat    defaults          0       2' "${M}/etc/fstab" \
    || fail "/etc/fstab boot entry changed"
  grep -Fx 'PARTUUID=4d8fd085-02  /               ext4    defaults,noatime  0       1' "${M}/etc/fstab" \
    || fail "/etc/fstab root entry changed"
fi

# --- Unit state -----------------------------------------------------------------
if [[ "${PROFILE}" == "rpi-os" ]]; then
  note "required units enabled"
  for unit in \
    rpi-resize.service regenerate_ssh_host_keys.service sshd-keygen.service \
    ssh.service NetworkManager.service wpa_supplicant.service \
    avahi-daemon.service getty@tty1.service nginx.service \
    fieldkit-web.service fieldkit-startup-network.timer \
    fieldkit-server-sync.timer fieldkit-tls-cert.service
  do
    expect_enabled "$unit"
  done

  note "AP units disabled (Fieldkit starts them at runtime)"
  expect_disabled fieldkit-ap-hostapd.service
  expect_disabled fieldkit-ap-dnsmasq.service

  note "unwanted units masked"
  for unit in \
    systemd-networkd.service systemd-networkd-wait-online.service \
    NetworkManager-wait-online.service hostapd.service dnsmasq.service \
    userconfig.service systemd-firstboot.service sshswitch.service \
    rpi-eeprom-update.service \
    e2scrub_reap.service cloud-init-local.service cloud-init-main.service \
    cloud-init-network.service cloud-config.service cloud-final.service \
    cloud-init-hotplugd.socket
  do
    expect_masked "$unit"
  done

  expect_disabled e2scrub_all.timer

  note "no Fieldkit growroot (native RPi resize is authoritative)"
  [[ ! -e "${M}/etc/fieldkit-growroot" ]] || fail "/etc/fieldkit-growroot must not be armed"
  [[ ! -e "${M}/etc/systemd/system/fieldkit-growroot.service" ]] || fail "fieldkit-growroot.service must not be installed"
  [[ ! -e "${M}/etc/systemd/system/fieldkit-growroot.timer" ]] || fail "fieldkit-growroot.timer must not be installed"
fi

# --- Boot cmdline / config.txt --------------------------------------------------
if [[ "${PROFILE}" == "rpi-os" ]]; then
  note "boot cmdline and serial console"
  cmdline="${M}/boot/firmware/cmdline.txt"
  [[ -f "${cmdline}" ]] || fail "missing ${cmdline}"
  grep -qw 'console=serial0,115200' "${cmdline}" || fail "cmdline missing console=serial0,115200"
  grep -qw 'console=tty1' "${cmdline}" || fail "cmdline missing console=tty1"
  grep -qw 'root=PARTUUID=4d8fd085-02' "${cmdline}" || fail "cmdline root= is not the root PARTUUID"
  grep -qw 'rootwait' "${cmdline}" || fail "cmdline missing rootwait"
  grep -qw 'resize' "${cmdline}" || fail "cmdline missing resize (first-boot partition grow disabled)"

  config="${M}/boot/firmware/config.txt"
  [[ -f "${config}" ]] || fail "missing ${config}"
  awk '
    $0 == "[all]" { in_all=1; next }
    /^\[/ { in_all=0 }
    in_all && $0 == "enable_uart=1" { found=1 }
    END { exit !found }
  ' "${config}" || fail "config.txt is missing enable_uart=1 under [all]"

  note "first-boot resize hooks present in both initramfs images"
  for initrd in initramfs8 initramfs_2712; do
    f="${M}/boot/firmware/${initrd}"
    [[ -s "${f}" ]] || fail "missing ${initrd}"
    initramfs_has "${f}" 'scripts/local-premount/resize_early' || fail "${initrd} lacks resize_early"
    initramfs_has "${f}" 'usr/bin/parted' || fail "${initrd} lacks parted"
    initramfs_has "${f}" 'usr/bin/lsblk' || fail "${initrd} lacks lsblk"
  done

  note "first boot will happen (machine-id uninitialized)"
  [[ "$(cat "${M}/etc/machine-id" 2>/dev/null)" == "uninitialized" ]] || \
    fail "/etc/machine-id is not 'uninitialized'"

  note "cloud-init disabled and rename banner removed"
  [[ -e "${M}/etc/cloud/cloud-init.disabled" ]] || fail "cloud-init.disabled marker missing"
  [[ ! -e "${M}/etc/ssh/sshd_config.d/rename_user.conf" ]] || fail "rename_user.conf still present"

  note "wired DHCP keyfile"
  nm="${M}/etc/NetworkManager/system-connections/fieldkit-wired.nmconnection"
  [[ -f "${nm}" ]] || fail "fieldkit-wired.nmconnection missing"
  [[ "$(stat -c %a "${nm}")" == "600" ]] || fail "fieldkit-wired.nmconnection not mode 0600"
  grep -qx 'interface-name=eth0' "${nm}" || fail "wired keyfile not bound to eth0"
  grep -qx 'method=auto' "${nm}" || fail "wired keyfile not DHCP"

  note "runtime layout exists and is owned by the web account"
  svc_uid="$(awk -F: '$1 == "service" {print $3}' "${M}/etc/passwd")"
  [[ -n "${svc_uid}" ]] || fail "image has no 'service' account"
  for d in data personal usb fieldkit; do
    [[ -d "${M}/opt/fieldkit/runtime/content/${d}" ]] || fail "missing runtime/content/${d}"
  done
  for p in runtime runtime/content runtime/content/data runtime/content/personal \
           runtime/content/usb runtime/content/fieldkit runtime/state; do
    [[ "$(stat -c %u "${M}/opt/fieldkit/${p}")" == "${svc_uid}" ]] || \
      fail "opt/fieldkit/${p} is not owned by service (uid ${svc_uid})"
  done
  [[ "$(stat -c %u "${M}/opt/fieldkit/scripts")" == "0" ]] || fail "opt/fieldkit/scripts is not root-owned"
  [[ "$(stat -c %u "${M}/opt/fieldkit/deploy")" == "0" ]] || fail "opt/fieldkit/deploy is not root-owned"

  # service must be in the `video` group for vcgencmd (/dev/vchiq is root:video).
  awk -F: '$1 == "video" { n = split($4, a, ","); for (i = 1; i <= n; i++) if (a[i] == "service") f = 1 } END { exit !f }' \
    "${M}/etc/group" || fail "service is not in the video group (vcgencmd will be unavailable)"

  note "web assets are self-hosted (no third-party runtime fetches)"
  if grep -rqE 'fonts\.googleapis\.com|fonts\.gstatic\.com' "${M}/opt/fieldkit/app/static" 2>/dev/null; then
    fail "app/static references third-party fonts (must be self-hosted)"
  fi
  [[ -f "${M}/opt/fieldkit/app/static/fonts.css" ]] || fail "missing app/static/fonts.css"
  for f in inter-latin.woff2 space-grotesk-latin.woff2 jetbrains-mono-latin.woff2; do
    [[ -s "${M}/opt/fieldkit/app/static/fonts/${f}" ]] || fail "missing self-hosted font ${f}"
  done

  note "seeded settings.json defaults to AP"
  python3 - "${M}/opt/fieldkit/runtime/state/settings.json" <<'PY' || fail "settings.json wifi.mode is not ap"
import json
import sys

with open(sys.argv[1], encoding="utf-8") as handle:
    data = json.load(handle)
sys.exit(0 if data.get("wifi", {}).get("mode") == "ap" else 1)
PY

  note "unit dependency graph verifies"
  systemd-analyze --root="${M}" verify \
    fieldkit-web.service fieldkit-startup-network.service \
    fieldkit-startup-network.timer fieldkit-ap-hostapd.service \
    fieldkit-ap-dnsmasq.service fieldkit-server-sync.service \
    fieldkit-server-sync.timer >/dev/null || fail "systemd-analyze verify failed"

  note "nginx serves HTTP and self-signed HTTPS"
  nginx_conf="${M}/etc/nginx/sites-available/fieldkit"
  [[ -f "${nginx_conf}" ]] || fail "nginx config missing"
  grep -q 'listen 80' "${nginx_conf}" || fail "nginx config lacks an 80 listener"
  grep -q 'listen 443 ssl' "${nginx_conf}" || fail "nginx config lacks a 443 ssl listener"
  grep -q 'ssl_certificate /etc/nginx/ssl/fieldkit.crt' "${nginx_conf}" || fail "nginx 443 cert path missing"

  note "nginx and sshd config validation"
  install -d -m 0755 "${M}/run/sshd"
  chroot "${M}" ssh-keygen -q -t ed25519 -N '' -f /run/fieldkit-audit-hostkey || \
    fail "ssh-keygen in image failed"
  chroot "${M}" /usr/sbin/sshd -t -h /run/fieldkit-audit-hostkey || fail "sshd -t failed"
  # Capture sshd -T output and its status explicitly: a pipe would SIGPIPE (141)
  # under `set -o pipefail`, and process substitution would hide a producer
  # failure so a partial listing could still pass.
  sshd_out="$(chroot "${M}" /usr/sbin/sshd -T -h /run/fieldkit-audit-hostkey 2>/dev/null)" \
    || fail "sshd -T failed"
  grep -qx 'passwordauthentication yes' <<<"${sshd_out}" \
    || fail "sshd password authentication is not enabled"
  # The image intentionally ships no TLS key (the first boot generates a unique
  # one); provide a throwaway cert so `nginx -t` can validate the 443 server,
  # then remove it so nothing private ships.
  tls_cert="${M}/etc/nginx/ssl/fieldkit.crt"
  tls_key="${M}/etc/nginx/ssl/fieldkit.key"
  tls_temp=0
  if [[ ! -s "${tls_cert}" ]]; then
    install -d -m 0755 "${M}/etc/nginx/ssl"
    chroot "${M}" openssl req -x509 -nodes -newkey rsa:2048 -days 1 \
      -keyout /etc/nginx/ssl/fieldkit.key -out /etc/nginx/ssl/fieldkit.crt \
      -subj /CN=fieldkit >/dev/null 2>&1 || fail "could not generate a temp TLS cert for nginx -t"
    tls_temp=1
  fi
  chroot "${M}" nginx -t || fail "nginx -t failed"
  if [[ ${tls_temp} -eq 1 ]]; then
    rm -f "${tls_cert}" "${tls_key}"
  fi
  rm -f "${M}"/run/fieldkit-audit-hostkey*

  # Guard against any chroot command having consumed the first-boot marker.
  printf 'uninitialized\n' > "${M}/etc/machine-id"
  [[ "$(cat "${M}/etc/machine-id")" == "uninitialized" ]] || fail "machine-id was consumed during audit"
fi

note "all checks passed (${PROFILE})"
