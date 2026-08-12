#!/usr/bin/env bash
set -euo pipefail

FIELDKIT_ROOT=${FIELDKIT_ROOT:-/opt/fieldkit}
AP_CONFIG_DIR=${AP_CONFIG_DIR:-/etc/fieldkit/ap}

if [[ ${EUID} -ne 0 ]]; then
  echo "Run as root."
  exit 1
fi

if ! dpkg -s hostapd >/dev/null 2>&1 || ! dpkg -s dnsmasq >/dev/null 2>&1; then
  if [[ "${FIELDKIT_SKIP_APT_UPDATE:-0}" != "1" ]]; then
    apt-get update
  fi
fi

if ! dpkg -s hostapd >/dev/null 2>&1; then
  apt-get install -y hostapd
fi

if ! dpkg -s dnsmasq >/dev/null 2>&1; then
  apt-get install -y dnsmasq
fi

install -d -m 0755 "${AP_CONFIG_DIR}"
install -D -m 0644 "${FIELDKIT_ROOT}/deploy/systemd/fieldkit-ap-hostapd.service" /etc/systemd/system/fieldkit-ap-hostapd.service
install -D -m 0644 "${FIELDKIT_ROOT}/deploy/systemd/fieldkit-ap-dnsmasq.service" /etc/systemd/system/fieldkit-ap-dnsmasq.service
install -D -m 0440 "${FIELDKIT_ROOT}/deploy/sudoers/fieldkit-network" /etc/sudoers.d/fieldkit-network

systemctl daemon-reload
systemctl disable --now fieldkit-ap-hostapd >/dev/null 2>&1 || true
systemctl disable --now fieldkit-ap-dnsmasq >/dev/null 2>&1 || true

echo "Wi-Fi AP support installed."
echo "Dedicated AP services are installed disabled by default."
