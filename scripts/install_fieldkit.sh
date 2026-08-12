#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
DEFAULT_ROOT=$(cd -- "${SCRIPT_DIR}/.." && pwd)

FIELDKIT_ROOT=${FIELDKIT_ROOT:-${DEFAULT_ROOT}}
FIELDKIT_USER=${FIELDKIT_USER:-service}
FIELDKIT_PASS=${FIELDKIT_PASS:-service}
FIELDKIT_HOSTNAME=${FIELDKIT_HOSTNAME:-fieldkit}
INSTALL_OS_PACKAGES=${INSTALL_OS_PACKAGES:-1}
INSTALL_AP_SUPPORT=${INSTALL_AP_SUPPORT:-1}
INSTALL_TRANSFER_SUPPORT=${INSTALL_TRANSFER_SUPPORT:-1}
START_SERVICES=${START_SERVICES:-1}

log() {
  printf '\n==> %s\n' "$*"
}

run_as_fieldkit_user() {
  sudo -u "${FIELDKIT_USER}" -H "$@"
}

if [[ ${EUID} -ne 0 ]]; then
  echo "Run as root, for example: sudo bash scripts/install_fieldkit.sh"
  exit 1
fi

if [[ ! -f "${FIELDKIT_ROOT}/pyproject.toml" || ! -d "${FIELDKIT_ROOT}/app" ]]; then
  echo "FIELDKIT_ROOT must point at a Fieldkit checkout. Current value: ${FIELDKIT_ROOT}"
  exit 1
fi

export DEBIAN_FRONTEND=noninteractive

if [[ "${INSTALL_OS_PACKAGES}" == "1" ]]; then
  log "Installing baseline OS packages"
  apt-get update
  apt-get install -y \
    avahi-daemon \
    ca-certificates \
    curl \
    dnsmasq \
    git \
    hostapd \
    iproute2 \
    network-manager \
    nginx \
    openssh-server \
    python3 \
    python3-pip \
    python3-venv \
    sudo \
    tftpd-hpa \
    vsftpd
fi

log "Creating/updating ${FIELDKIT_USER} user"
if ! id -u "${FIELDKIT_USER}" >/dev/null 2>&1; then
  useradd -m -s /bin/bash "${FIELDKIT_USER}"
fi
echo "${FIELDKIT_USER}:${FIELDKIT_PASS}" | chpasswd
usermod -aG sudo,dialout,netdev,plugdev "${FIELDKIT_USER}" || true

log "Preparing NetworkManager, SSH, and mDNS"
systemctl enable ssh >/dev/null 2>&1 || systemctl enable sshd >/dev/null 2>&1 || true
systemctl enable NetworkManager
systemctl disable systemd-networkd >/dev/null 2>&1 || true
systemctl restart NetworkManager
systemctl enable avahi-daemon >/dev/null 2>&1 || true
systemctl restart avahi-daemon >/dev/null 2>&1 || true

log "Provisioning runtime layout"
chown -R "${FIELDKIT_USER}:${FIELDKIT_USER}" "${FIELDKIT_ROOT}"
if [[ "${INSTALL_AP_SUPPORT}" == "1" ]]; then
  FIELDKIT_DEFAULT_WIFI_MODE=ap
else
  FIELDKIT_DEFAULT_WIFI_MODE=disabled
fi
FIELDKIT_ROOT="${FIELDKIT_ROOT}" \
FIELDKIT_USER="${FIELDKIT_USER}" \
FIELDKIT_PASS="${FIELDKIT_PASS}" \
FIELDKIT_HOSTNAME="${FIELDKIT_HOSTNAME}" \
FIELDKIT_DEFAULT_WIFI_MODE="${FIELDKIT_DEFAULT_WIFI_MODE}" \
bash "${FIELDKIT_ROOT}/scripts/provision_pi.sh"

log "Installing Python environment"
run_as_fieldkit_user python3 -m venv "${FIELDKIT_ROOT}/.venv"
run_as_fieldkit_user "${FIELDKIT_ROOT}/.venv/bin/pip" install --upgrade pip
run_as_fieldkit_user "${FIELDKIT_ROOT}/.venv/bin/pip" install -e "${FIELDKIT_ROOT}"

log "Installing systemd units"
cd "${FIELDKIT_ROOT}"
FIELDKIT_ROOT="${FIELDKIT_ROOT}" SERVICE_USER="${FIELDKIT_USER}" bash scripts/install_systemd.sh

if [[ "${INSTALL_TRANSFER_SUPPORT}" == "1" ]]; then
  log "Installing transfer service support"
  FIELDKIT_ROOT="${FIELDKIT_ROOT}" SERVICE_USER="${FIELDKIT_USER}" FIELDKIT_SKIP_APT_UPDATE=1 bash scripts/install_transfer_services.sh
fi

if [[ "${INSTALL_AP_SUPPORT}" == "1" ]]; then
  log "Installing Wi-Fi AP support"
  FIELDKIT_ROOT="${FIELDKIT_ROOT}" FIELDKIT_SKIP_APT_UPDATE=1 bash scripts/install_wifi_ap_support.sh
fi

log "Installing nginx plain HTTP mode"
bash scripts/install_export_http_mode.sh

if [[ "${START_SERVICES}" == "1" ]]; then
  log "Starting Fieldkit services"
  systemctl restart fieldkit-startup-network.service
  systemctl restart fieldkit-web.service
  systemctl reload nginx || systemctl restart nginx
fi

log "Install complete"
cat <<EOF

Fieldkit root: ${FIELDKIT_ROOT}
User: ${FIELDKIT_USER}
Hostname: ${FIELDKIT_HOSTNAME}
Web service: fieldkit-web.service

Default access after reboot/network convergence:
- http://${FIELDKIT_HOSTNAME}.local/
- http://10.42.0.1/ when AP mode is enabled

Change the default password immediately on real deployments.
EOF
