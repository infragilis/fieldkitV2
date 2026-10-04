#!/usr/bin/env bash
set -euo pipefail

if [[ ${EUID} -ne 0 ]]; then
  echo "Run as root."
  exit 1
fi

MODE=${1:-enable}
if [[ "${MODE}" != "enable" && "${MODE}" != "disable" ]]; then
  echo "Usage: $0 [enable|disable]" >&2
  exit 2
fi

# The nginx template has a 443 listener, so the self-signed cert must exist
# before any `nginx -t`. Best-effort here; nginx -t is the real gate.
bash "$(dirname -- "$0")/install_tls_cert.sh" >/dev/null 2>&1 || true

BACKUP=$(mktemp)
HAD_CONFIG=0
if [[ -f /etc/nginx/sites-available/fieldkit ]]; then
  cp /etc/nginx/sites-available/fieldkit "${BACKUP}"
  HAD_CONFIG=1
fi
OLD_TARGET=$(readlink /etc/nginx/sites-enabled/fieldkit 2>/dev/null || true)
rollback() {
  if [[ "${HAD_CONFIG}" == "1" ]]; then cp "${BACKUP}" /etc/nginx/sites-available/fieldkit; else rm -f /etc/nginx/sites-available/fieldkit; fi
  if [[ -n "${OLD_TARGET}" ]]; then ln -sfn "${OLD_TARGET}" /etc/nginx/sites-enabled/fieldkit; else rm -f /etc/nginx/sites-enabled/fieldkit; fi
  nginx -t && (systemctl reload nginx || systemctl restart nginx)
}
finish() { rm -f "${BACKUP}"; }

if [[ "${MODE}" == "disable" ]]; then
  # Keep the appliance UI available on port 80, but explicitly reject the
  # shared export prefix.  The enabled config is restored below when needed.
  install -D -m 0644 deploy/nginx/fieldkit.conf /etc/nginx/sites-available/fieldkit-disabled
  sed -i '/location \/ {/i\\    location ^~ /fieldkit { return 404; }' /etc/nginx/sites-available/fieldkit-disabled
  ln -sfn /etc/nginx/sites-available/fieldkit-disabled /etc/nginx/sites-enabled/fieldkit
  if ! nginx -t || ! (systemctl reload nginx || systemctl restart nginx); then
    if ! rollback; then echo "ERROR: nginx rollback failed; restored config could not be loaded." >&2; fi
    rm -f "${BACKUP}"
    exit 1
  fi
  finish
  echo "Disabled Fieldkit nginx HTTP export."
  exit 0
fi

if ! dpkg -s nginx >/dev/null 2>&1; then
  apt-get update
  DEBIAN_FRONTEND=noninteractive apt-get install -y nginx
fi

install -D -m 0644 deploy/nginx/fieldkit.conf /etc/nginx/sites-available/fieldkit
ln -sf /etc/nginx/sites-available/fieldkit /etc/nginx/sites-enabled/fieldkit
rm -f /etc/nginx/sites-enabled/default
if ! nginx -t || ! (systemctl reload nginx || systemctl restart nginx); then
  if ! rollback; then echo "ERROR: nginx rollback failed; restored config could not be loaded." >&2; fi
  rm -f "${BACKUP}"
  exit 1
fi
systemctl enable nginx
finish

echo "Installed Fieldkit nginx (HTTP 80 + self-signed HTTPS 443)."
