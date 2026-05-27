#!/usr/bin/env bash
set -euo pipefail

FIELDKIT_ROOT=${FIELDKIT_ROOT:-/opt/fieldkit}
FIELDKIT_USER=${FIELDKIT_USER:-service}
FIELDKIT_PASS=${FIELDKIT_PASS:-service}
FIELDKIT_HOSTNAME=${FIELDKIT_HOSTNAME:-fieldkit}
FIELDKIT_REPO_URL=${FIELDKIT_REPO_URL:-https://github.com/infragilis/fieldkitV2.git}
FIELDKIT_BRANCH=${FIELDKIT_BRANCH:-main}
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
  echo "Run as root, for example: sudo bash scripts/bootstrap_fresh_pi.sh"
  exit 1
fi

export DEBIAN_FRONTEND=noninteractive

log "Installing baseline OS packages"
apt-get update
apt-get install -y \
  avahi-daemon \
  curl \
  dnsmasq \
  git \
  hostapd \
  network-manager \
  nginx \
  openssh-server \
  python3 \
  python3-pip \
  python3-venv \
  sudo \
  tftpd-hpa \
  vsftpd

log "Creating/updating ${FIELDKIT_USER} user"
if ! id -u "${FIELDKIT_USER}" >/dev/null 2>&1; then
  useradd -m -s /bin/bash "${FIELDKIT_USER}"
fi
echo "${FIELDKIT_USER}:${FIELDKIT_PASS}" | chpasswd
usermod -aG sudo,dialout,netdev,plugdev "${FIELDKIT_USER}" || true

log "Preparing NetworkManager and SSH"
systemctl enable ssh >/dev/null 2>&1 || systemctl enable sshd >/dev/null 2>&1 || true
systemctl enable NetworkManager
systemctl disable systemd-networkd >/dev/null 2>&1 || true
systemctl restart NetworkManager
systemctl enable avahi-daemon >/dev/null 2>&1 || true
systemctl restart avahi-daemon >/dev/null 2>&1 || true

log "Installing Fieldkit source at ${FIELDKIT_ROOT}"
if [[ -d "${FIELDKIT_ROOT}/.git" ]]; then
  git -C "${FIELDKIT_ROOT}" fetch origin "${FIELDKIT_BRANCH}"
  git -C "${FIELDKIT_ROOT}" checkout "${FIELDKIT_BRANCH}"
  git -C "${FIELDKIT_ROOT}" pull --ff-only origin "${FIELDKIT_BRANCH}"
else
  if [[ -e "${FIELDKIT_ROOT}" && -n "$(find "${FIELDKIT_ROOT}" -mindepth 1 -maxdepth 1 -print -quit 2>/dev/null)" ]]; then
    echo "${FIELDKIT_ROOT} exists and is not an empty Git checkout. Move it aside or set FIELDKIT_ROOT."
    exit 1
  fi
  rm -rf "${FIELDKIT_ROOT}"
  git clone --branch "${FIELDKIT_BRANCH}" "${FIELDKIT_REPO_URL}" "${FIELDKIT_ROOT}"
fi
chown -R "${FIELDKIT_USER}:${FIELDKIT_USER}" "${FIELDKIT_ROOT}"

log "Provisioning runtime layout"
FIELDKIT_ROOT="${FIELDKIT_ROOT}" \
FIELDKIT_USER="${FIELDKIT_USER}" \
FIELDKIT_PASS="${FIELDKIT_PASS}" \
FIELDKIT_HOSTNAME="${FIELDKIT_HOSTNAME}" \
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
  FIELDKIT_ROOT="${FIELDKIT_ROOT}" SERVICE_USER="${FIELDKIT_USER}" bash scripts/install_transfer_services.sh
fi

if [[ "${INSTALL_AP_SUPPORT}" == "1" ]]; then
  log "Installing Wi-Fi AP support"
  FIELDKIT_ROOT="${FIELDKIT_ROOT}" bash scripts/install_wifi_ap_support.sh
fi

log "Installing nginx export mode"
bash scripts/install_export_http_mode.sh

if [[ "${START_SERVICES}" == "1" ]]; then
  log "Starting Fieldkit services"
  systemctl restart fieldkit-web.service
  systemctl reload nginx || systemctl restart nginx
fi

log "Bootstrap complete"
cat <<EOF2

Fieldkit root: ${FIELDKIT_ROOT}
User: ${FIELDKIT_USER}
Hostname: ${FIELDKIT_HOSTNAME}
Web service: fieldkit-web.service

Default access after reboot/network convergence:
- http://${FIELDKIT_HOSTNAME}.local/
- http://10.42.0.1/ when AP mode is enabled

Change the default password immediately on real deployments.
EOF2
