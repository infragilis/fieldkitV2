#!/usr/bin/env bash
set -euo pipefail

if [[ ${EUID} -ne 0 ]]; then
  echo "Run as root."
  exit 1
fi

if ! dpkg -s nginx >/dev/null 2>&1; then
  apt-get update
  DEBIAN_FRONTEND=noninteractive apt-get install -y nginx
fi

install -D -m 0644 deploy/nginx/fieldkit.conf /etc/nginx/sites-available/fieldkit
ln -sf /etc/nginx/sites-available/fieldkit /etc/nginx/sites-enabled/fieldkit
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl enable nginx
systemctl reload nginx || systemctl restart nginx

echo "Installed Fieldkit nginx plain HTTP mode."
