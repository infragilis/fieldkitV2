#!/usr/bin/env bash
# Runs INSIDE the golden-image chroot as root: installs Fieldkit, enables the
# services without starting them, and syspreps the image for first boot.
set -euo pipefail

export DEBIAN_FRONTEND=noninteractive
FIELDKIT_ROOT=${FIELDKIT_ROOT:-/opt/fieldkit}

log() {
  printf '\n==> %s\n' "$*"
}

# systemctl shim: daemon-reload/enable/disable work on unit symlinks; the rest
# are no-ops because nothing is running inside the chroot.
systemctl() {
  local cmd="$1"
  shift || true
  case "${cmd}" in
    daemon-reload) return 0 ;;
    enable)
      for unit in "$@"; do
        if [[ -f "/etc/systemd/system/${unit}" ]]; then
          local wanted
          while read -r line; do
            case "${line}" in
              WantedBy=*)
                wanted="${line#WantedBy=}"
                mkdir -p "/etc/systemd/system/${wanted}.wants"
                ln -sf "/etc/systemd/system/${unit}" "/etc/systemd/system/${wanted}.wants/${unit}"
                ;;
            esac
          done < "/etc/systemd/system/${unit}"
        fi
      done
      return 0 ;;
    disable)
      for unit in "$@"; do
        find /etc/systemd/system -name "${unit}" -delete 2>/dev/null || true
      done
      return 0 ;;
    *) return 0 ;;
  esac
}
export -f systemctl

log "OS packages"
apt-get update
apt-get install -y --no-install-recommends \
  ca-certificates curl git sudo

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
rm -f /etc/ssh/ssh_host_*_key /etc/ssh/ssh_host_*_key.pub
if [[ -d /etc/systemd/system/multi-user.target.wants ]]; then
  for unit in ssh.service sshd.service regenerate_ssh_host_keys.service; do
    [[ -f "/etc/systemd/system/${unit}" ]] && ln -sf "/etc/systemd/system/${unit}" "/etc/systemd/system/multi-user.target.wants/${unit}"
  done
fi

log "Neutralize cloud-init"
touch /etc/cloud/cloud-init.disabled 2>/dev/null || true

log "Sysprep"
find /var/log -type f -delete 2>/dev/null || true
rm -rf /tmp/* /var/tmp/* 2>/dev/null || true
rm -f /root/.bash_history /home/service/.bash_history 2>/dev/null || true
rm -rf "${FIELDKIT_ROOT}/runtime/content"/* "${FIELDKIT_ROOT}/runtime/state"/* 2>/dev/null || true
find "${FIELDKIT_ROOT}" -name '__pycache__' -type d -prune -exec rm -rf {} + 2>/dev/null || true
sync

log "Golden image ready"
