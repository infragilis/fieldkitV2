#!/usr/bin/env bash
set -euo pipefail

FIELDKIT_ROOT=${FIELDKIT_ROOT:-/opt/fieldkit}
SERVICE_USER=${SERVICE_USER:-service}

if [[ ${EUID} -ne 0 ]]; then
  echo "Run as root."
  exit 1
fi

install -D -m 0644 deploy/systemd/fieldkit-web.service /etc/systemd/system/fieldkit-web.service
install -D -m 0644 deploy/systemd/fieldkit-startup-network.service /etc/systemd/system/fieldkit-startup-network.service
sed -i "s#/opt/fieldkit#${FIELDKIT_ROOT}#g" /etc/systemd/system/fieldkit-web.service
sed -i "s#/opt/fieldkit#${FIELDKIT_ROOT}#g" /etc/systemd/system/fieldkit-startup-network.service
sed -i "s#User=service#User=${SERVICE_USER}#g" /etc/systemd/system/fieldkit-web.service

systemctl daemon-reload
systemctl enable fieldkit-web.service
systemctl enable fieldkit-startup-network.service

echo "Installed fieldkit-web.service and fieldkit-startup-network.service"
