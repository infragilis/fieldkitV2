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
install -D -m 0644 deploy/systemd/fieldkit-startup-network.timer /etc/systemd/system/fieldkit-startup-network.timer
install -D -m 0644 deploy/systemd/fieldkit-server-sync.service /etc/systemd/system/fieldkit-server-sync.service
install -D -m 0644 deploy/systemd/fieldkit-server-sync.timer /etc/systemd/system/fieldkit-server-sync.timer
install -D -m 0644 deploy/systemd/fieldkit-post-update.service /etc/systemd/system/fieldkit-post-update.service
install -D -m 0644 deploy/systemd/fieldkit-rollback.service /etc/systemd/system/fieldkit-rollback.service
install -D -m 0644 deploy/systemd/fieldkit-tls-cert.service /etc/systemd/system/fieldkit-tls-cert.service
install -D -m 0644 deploy/systemd/fieldkit-usb-mount@.service /etc/systemd/system/fieldkit-usb-mount@.service
install -D -m 0644 deploy/systemd/nginx-fieldkit-tls.conf /etc/systemd/system/nginx.service.d/10-fieldkit-tls.conf
install -D -m 0644 deploy/systemd/00-fieldkit.preset /etc/systemd/system-preset/00-fieldkit.preset
install -D -m 0440 deploy/sudoers/fieldkit-update /etc/sudoers.d/fieldkit-update 2>/dev/null || true
sed -i "s#/opt/fieldkit#${FIELDKIT_ROOT}#g" /etc/systemd/system/fieldkit-web.service
sed -i "s#/opt/fieldkit#${FIELDKIT_ROOT}#g" /etc/systemd/system/fieldkit-startup-network.service
sed -i "s#/opt/fieldkit#${FIELDKIT_ROOT}#g" /etc/systemd/system/fieldkit-post-update.service
sed -i "s#User=service#User=${SERVICE_USER}#g" /etc/systemd/system/fieldkit-web.service
sed -i "s#User=service#User=${SERVICE_USER}#g" /etc/systemd/system/fieldkit-server-sync.service

systemctl daemon-reload
systemctl enable fieldkit-web.service
# The startup-network service is timer-triggered (after boot) so it cannot block
# multi-user / the console / the web UI.
systemctl enable fieldkit-startup-network.timer
systemctl enable fieldkit-server-sync.timer
# Generate the per-device self-signed TLS cert before nginx (see the unit).
systemctl enable fieldkit-tls-cert.service
# Ensure a getty on the HDMI/VT console so the keyboard works on first boot.
systemctl enable getty@tty1.service 2>/dev/null || true

# Auto-mount removable USB media for copy-to-USB: the udev rule starts the
# fieldkit-usb-mount@.service template, which runs scripts/fieldkit-usb.sh.
install -D -m 0644 deploy/udev/99-fieldkit-usb.rules /etc/udev/rules.d/99-fieldkit-usb.rules
udevadm control --reload-rules 2>/dev/null || true
udevadm trigger --subsystem-match=block --action=add 2>/dev/null || true

echo "Installed Fieldkit web/startup services and automatic server-sync timer"
