#!/usr/bin/env bash
set -euo pipefail

EXPORT_HTTP_ENABLED=${EXPORT_HTTP_ENABLED:-1}
CERT_DIR=${CERT_DIR:-/etc/fieldkit/tls}
CERT_NAME=${CERT_NAME:-fieldkit}

if [[ ${EUID} -ne 0 ]]; then
  echo "Run as root."
  exit 1
fi

if ! dpkg -s nginx >/dev/null 2>&1; then
  apt-get update
  DEBIAN_FRONTEND=noninteractive apt-get install -y nginx
fi

if [[ -f "${CERT_DIR}/${CERT_NAME}.crt" && -f "${CERT_DIR}/${CERT_NAME}.key" ]]; then
  if [[ "${EXPORT_HTTP_ENABLED}" == "1" ]]; then
    install -D -m 0644 deploy/nginx/fieldkit-ssl-export-http.conf /etc/nginx/sites-available/fieldkit
  else
    install -D -m 0644 deploy/nginx/fieldkit-ssl.conf /etc/nginx/sites-available/fieldkit
  fi
else
  install -D -m 0644 deploy/nginx/fieldkit.conf /etc/nginx/sites-available/fieldkit
fi

ln -sf /etc/nginx/sites-available/fieldkit /etc/nginx/sites-enabled/fieldkit
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl enable nginx
systemctl reload nginx || systemctl restart nginx

echo "HTTP export mode installed: export_http=${EXPORT_HTTP_ENABLED}"
