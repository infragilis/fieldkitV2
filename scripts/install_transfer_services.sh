#!/usr/bin/env bash
set -euo pipefail

FIELDKIT_ROOT=${FIELDKIT_ROOT:-/opt/fieldkit}
SERVICE_USER=${SERVICE_USER:-service}
EXPORT_ROOT="${FIELDKIT_ROOT}/runtime/content/fieldkit"

if [[ ${EUID} -ne 0 ]]; then
  echo "Run as root."
  exit 1
fi

if ! dpkg -s tftpd-hpa >/dev/null 2>&1 || ! dpkg -s vsftpd >/dev/null 2>&1; then
  apt-get update
fi

if ! dpkg -s tftpd-hpa >/dev/null 2>&1; then
  apt-get install -y tftpd-hpa
fi

if ! dpkg -s vsftpd >/dev/null 2>&1; then
  apt-get install -y vsftpd
fi

install -d -o "${SERVICE_USER}" -g "${SERVICE_USER}" "${EXPORT_ROOT}"

cat >/etc/default/tftpd-hpa <<EOF
TFTP_USERNAME="tftp"
TFTP_DIRECTORY="${EXPORT_ROOT}"
TFTP_ADDRESS=":69"
TFTP_OPTIONS="--secure --create"
EOF

cat >/etc/vsftpd.conf <<EOF
listen=YES
listen_ipv6=NO
anonymous_enable=YES
local_enable=NO
write_enable=NO
anon_root=${EXPORT_ROOT}
no_anon_password=YES
hide_ids=YES
xferlog_enable=YES
ftpd_banner=Fieldkit FTP export
anon_world_readable_only=YES
EOF

install -D -m 0440 deploy/sudoers/fieldkit-transfer /etc/sudoers.d/fieldkit-transfer

systemctl daemon-reload

systemctl disable --now tftpd-hpa >/dev/null 2>&1 || true
systemctl disable --now vsftpd >/dev/null 2>&1 || true

echo "Transfer service support installed."
echo "Export root: ${EXPORT_ROOT}"
echo "TFTP and FTP are installed disabled by default and should be enabled from the Fieldkit Settings page if needed."
