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

if [[ ${EUID} -ne 0 ]]; then
  echo "Run as root, for example: sudo bash scripts/bootstrap_fresh_pi.sh"
  exit 1
fi

export DEBIAN_FRONTEND=noninteractive

log "Installing bootstrap OS packages"
apt-get update
apt-get install -y \
  ca-certificates \
  git \
  sudo

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

log "Running Fieldkit installer"
FIELDKIT_ROOT="${FIELDKIT_ROOT}" \
FIELDKIT_USER="${FIELDKIT_USER}" \
FIELDKIT_PASS="${FIELDKIT_PASS}" \
FIELDKIT_HOSTNAME="${FIELDKIT_HOSTNAME}" \
INSTALL_OS_PACKAGES=1 \
INSTALL_AP_SUPPORT="${INSTALL_AP_SUPPORT}" \
INSTALL_TRANSFER_SUPPORT="${INSTALL_TRANSFER_SUPPORT}" \
START_SERVICES="${START_SERVICES}" \
bash "${FIELDKIT_ROOT}/scripts/install_fieldkit.sh"
