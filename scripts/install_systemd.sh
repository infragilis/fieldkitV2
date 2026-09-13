#!/usr/bin/env bash
set -euo pipefail

FIELDKIT_ROOT=${FIELDKIT_ROOT:-/opt/fieldkit}
SERVICE_USER=${SERVICE_USER:-service}

if [[ ${EUID} -ne 0 ]]; then
  echo "Run as root."
  exit 1
fi

if [[ ${FIELDKIT_ROOT} != "/opt/fieldkit" ]]; then
  echo "FIELDKIT_ROOT must be /opt/fieldkit because installed paths are canonical."
  exit 1
fi

install -D -m 0644 deploy/systemd/fieldkit-web.service /etc/systemd/system/fieldkit-web.service
install -D -m 0644 deploy/systemd/fieldkit-startup-network.service /etc/systemd/system/fieldkit-startup-network.service
install -D -m 0644 deploy/systemd/fieldkit-server-sync.service /etc/systemd/system/fieldkit-server-sync.service
install -D -m 0644 deploy/systemd/fieldkit-server-sync.timer /etc/systemd/system/fieldkit-server-sync.timer
install -D -m 0440 deploy/sudoers/fieldkit-update /etc/sudoers.d/fieldkit-update 2>/dev/null || true
sed -i "s#/opt/fieldkit#${FIELDKIT_ROOT}#g" /etc/systemd/system/fieldkit-web.service
sed -i "s#/opt/fieldkit#${FIELDKIT_ROOT}#g" /etc/systemd/system/fieldkit-startup-network.service
sed -i "s#User=service#User=${SERVICE_USER}#g" /etc/systemd/system/fieldkit-web.service
sed -i "s#User=service#User=${SERVICE_USER}#g" /etc/systemd/system/fieldkit-server-sync.service

systemctl daemon-reload
systemctl enable fieldkit-web.service
systemctl enable fieldkit-startup-network.service
systemctl enable fieldkit-server-sync.timer

echo "Installed Fieldkit web/startup services and automatic server-sync timer"
