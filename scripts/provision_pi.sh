#!/usr/bin/env bash
set -euo pipefail

FIELDKIT_ROOT=${FIELDKIT_ROOT:-/opt/fieldkit}
FIELDKIT_USER=${FIELDKIT_USER:-service}
FIELDKIT_PASS=${FIELDKIT_PASS:-service}
FIELDKIT_HOSTNAME=${FIELDKIT_HOSTNAME:-fieldkit}

if [[ ${EUID} -ne 0 ]]; then
  echo "Run as root."
  exit 1
fi

if ! id -u "${FIELDKIT_USER}" >/dev/null 2>&1; then
  useradd -m -s /bin/bash "${FIELDKIT_USER}"
fi

echo "${FIELDKIT_USER}:${FIELDKIT_PASS}" | chpasswd
hostnamectl set-hostname "${FIELDKIT_HOSTNAME}"

install -d -o "${FIELDKIT_USER}" -g "${FIELDKIT_USER}" "${FIELDKIT_ROOT}"
install -d -o "${FIELDKIT_USER}" -g "${FIELDKIT_USER}" "${FIELDKIT_ROOT}/runtime/content/data"
install -d -o "${FIELDKIT_USER}" -g "${FIELDKIT_USER}" "${FIELDKIT_ROOT}/runtime/content/personal"
install -d -o "${FIELDKIT_USER}" -g "${FIELDKIT_USER}" "${FIELDKIT_ROOT}/runtime/content/usb"
install -d -o "${FIELDKIT_USER}" -g "${FIELDKIT_USER}" "${FIELDKIT_ROOT}/runtime/state"

cat <<EOF
Provisioning complete.

Hostname: ${FIELDKIT_HOSTNAME}
User: ${FIELDKIT_USER}
App root: ${FIELDKIT_ROOT}
EOF
