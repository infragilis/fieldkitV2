#!/usr/bin/env bash
set -euo pipefail

CERT_DIR=${CERT_DIR:-/etc/fieldkit/tls}
CERT_NAME=${CERT_NAME:-fieldkit}
CERT_DAYS=${CERT_DAYS:-3650}
COMMON_NAME=${COMMON_NAME:-fieldkit}
ALT_NAMES=${ALT_NAMES:-DNS:fieldkit,IP:192.168.200.120}

if [[ ${EUID} -ne 0 ]]; then
  echo "Run as root."
  exit 1
fi

apt-get update
DEBIAN_FRONTEND=noninteractive apt-get install -y nginx openssl

install -d -m 0755 "${CERT_DIR}"

TMP_CONFIG=$(mktemp)
cat >"${TMP_CONFIG}" <<EOF
[req]
default_bits = 2048
prompt = no
default_md = sha256
x509_extensions = v3_req
distinguished_name = dn

[dn]
CN = ${COMMON_NAME}

[v3_req]
subjectAltName = ${ALT_NAMES}
keyUsage = digitalSignature, keyEncipherment
extendedKeyUsage = serverAuth
EOF

openssl req -x509 -nodes -newkey rsa:2048 \
  -keyout "${CERT_DIR}/${CERT_NAME}.key" \
  -out "${CERT_DIR}/${CERT_NAME}.crt" \
  -days "${CERT_DAYS}" \
  -config "${TMP_CONFIG}"

chmod 0600 "${CERT_DIR}/${CERT_NAME}.key"
chmod 0644 "${CERT_DIR}/${CERT_NAME}.crt"
rm -f "${TMP_CONFIG}"

install -D -m 0644 deploy/nginx/fieldkit-ssl.conf /etc/nginx/sites-available/fieldkit
ln -sf /etc/nginx/sites-available/fieldkit /etc/nginx/sites-enabled/fieldkit
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl enable nginx
systemctl restart nginx

cat <<EOF
Installed self-signed TLS for Fieldkit.

HTTPS URL: https://192.168.200.120/
Certificate: ${CERT_DIR}/${CERT_NAME}.crt
Key: ${CERT_DIR}/${CERT_NAME}.key
EOF
