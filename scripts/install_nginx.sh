#!/usr/bin/env bash
set -euo pipefail

if [[ ${EUID} -ne 0 ]]; then
  echo "Run as root."
  exit 1
fi

apt-get update
DEBIAN_FRONTEND=noninteractive apt-get install -y nginx
install -D -m 0644 deploy/nginx/fieldkit.conf /etc/nginx/sites-available/fieldkit
ln -sf /etc/nginx/sites-available/fieldkit /etc/nginx/sites-enabled/fieldkit
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl enable nginx
systemctl restart nginx

echo "Installed nginx reverse proxy for Fieldkit on port 80"
