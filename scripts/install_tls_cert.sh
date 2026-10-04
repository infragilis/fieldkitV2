#!/usr/bin/env bash
# Generate the per-device self-signed TLS certificate used by Fieldkit's nginx
# HTTPS listener (decision 12). Idempotent: an existing cert is kept unless
# --force is given.
#
# The first-boot fieldkit-tls-cert.service runs this before nginx so every
# flashed kit gets its own key (the golden image ships none).
set -euo pipefail

CERT_DIR=${CERT_DIR:-/etc/nginx/ssl}
CERT=${CERT:-${CERT_DIR}/fieldkit.crt}
KEY=${KEY:-${CERT_DIR}/fieldkit.key}
DAYS=${DAYS:-3650}

FORCE=0
if [[ "${1:-}" == "--force" ]]; then
  FORCE=1
fi

if [[ ${EUID} -ne 0 ]]; then
  echo "Run as root."
  exit 1
fi

if [[ -s "${CERT}" && -s "${KEY}" && ${FORCE} -eq 0 ]]; then
  echo "TLS certificate already present: ${CERT}"
  exit 0
fi

if ! command -v openssl >/dev/null 2>&1; then
  echo "openssl is required to generate the TLS certificate." >&2
  exit 1
fi

hostname_short="$(hostname 2>/dev/null || echo fieldkit)"
hostname_short=${hostname_short%%.*}
[[ -n "${hostname_short}" ]] || hostname_short=fieldkit

install -d -m 0755 "${CERT_DIR}"
tmp_key="$(mktemp "${CERT_DIR}/.fieldkit.key.XXXXXX")"
tmp_crt="$(mktemp "${CERT_DIR}/.fieldkit.crt.XXXXXX")"
trap 'rm -f "${tmp_key}" "${tmp_crt}"' EXIT

openssl req -x509 -nodes -newkey rsa:2048 \
  -days "${DAYS}" \
  -keyout "${tmp_key}" -out "${tmp_crt}" \
  -subj "/CN=${hostname_short}" \
  -addext "subjectAltName=DNS:${hostname_short},DNS:fieldkit,DNS:fieldkit.local,DNS:localhost,IP:10.42.0.1,IP:127.0.0.1" \
  >/dev/null 2>&1

chmod 0600 "${tmp_key}"
chmod 0644 "${tmp_crt}"
mv -f "${tmp_key}" "${KEY}"
mv -f "${tmp_crt}" "${CERT}"
trap - EXIT

echo "Generated self-signed TLS certificate for ${hostname_short} -> ${CERT}"
