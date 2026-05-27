#!/usr/bin/env bash
set -euo pipefail

FIELDKIT_HOST=${FIELDKIT_HOST:-192.168.200.120}
FIELDKIT_SCHEME=${FIELDKIT_SCHEME:-http}
FIELDKIT_USER=${FIELDKIT_USER:-service}
FIELDKIT_PASSWORD=${FIELDKIT_PASSWORD:-service}
FIELDKIT_APP_ROOT=${FIELDKIT_APP_ROOT:-/opt/fieldkit}
SMOKE_NAME=${SMOKE_NAME:-fieldkit-smoke.txt}
SMOKE_PAYLOAD=${SMOKE_PAYLOAD:-fieldkit smoke payload}
TEST_TFTP=${TEST_TFTP:-auto}
FIELDKIT_BASE_URL="${FIELDKIT_SCHEME}://${FIELDKIT_HOST}"
TMP_FILE=$(mktemp)
TMP_FETCH=$(mktemp)

cleanup() {
  rm -f "${TMP_FILE}" "${TMP_FETCH}"
  curl -sk -X DELETE "${FIELDKIT_BASE_URL}/api/files?library=personal&path=${SMOKE_NAME}" >/dev/null 2>&1 || true
}
trap cleanup EXIT

need_bin() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "missing required binary: $1" >&2
    exit 1
  fi
}

need_bin curl
need_bin sshpass
need_bin scp
need_bin python3

printf '%s\n' "${SMOKE_PAYLOAD}" > "${TMP_FILE}"

curl -sk -X DELETE "${FIELDKIT_BASE_URL}/api/files?library=personal&path=${SMOKE_NAME}" >/dev/null 2>&1 || true

echo "Uploading ${SMOKE_NAME} to personal library via HTTP API..."
curl -sk -f -X POST -F "file=@${TMP_FILE};filename=${SMOKE_NAME}" \
  "${FIELDKIT_BASE_URL}/api/files/upload?library=personal" >/dev/null

echo "Verifying HTTP API download..."
curl -sk -f "${FIELDKIT_BASE_URL}/api/files/download?library=personal&path=${SMOKE_NAME}" > "${TMP_FETCH}"
cmp -s "${TMP_FILE}" "${TMP_FETCH}"

echo "Verifying plain HTTP export download..."
curl -fsS "http://${FIELDKIT_HOST}/fieldkit/personal/${SMOKE_NAME}" > "${TMP_FETCH}"
cmp -s "${TMP_FILE}" "${TMP_FETCH}"

echo "Verifying SCP download from shared export root..."
sshpass -p "${FIELDKIT_PASSWORD}" scp -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
  "${FIELDKIT_USER}@${FIELDKIT_HOST}:${FIELDKIT_APP_ROOT}/runtime/content/fieldkit/personal/${SMOKE_NAME}" "${TMP_FETCH}" >/dev/null
cmp -s "${TMP_FILE}" "${TMP_FETCH}"

echo "Checking transfer service status..."
STATUS_JSON=$(curl -sk -f "${FIELDKIT_BASE_URL}/api/transfers/status")
printf '%s' "${STATUS_JSON}" | python3 -c 'import json,sys; data=json.load(sys.stdin); print(json.dumps({"http_export": data["http_export"], "tftp": data["tftp"], "ftp": data["ftp"], "scp": data["scp"]}, indent=2))'

FTP_ACTIVE=$(printf '%s' "${STATUS_JSON}" | python3 -c 'import json,sys; data=json.load(sys.stdin); print("1" if data["ftp"]["active"] else "0")')
if [[ "${FTP_ACTIVE}" == "1" ]]; then
  echo "Verifying FTP download..."
  curl --max-time 20 -fsS "ftp://${FIELDKIT_HOST}/personal/${SMOKE_NAME}" > "${TMP_FETCH}"
  cmp -s "${TMP_FILE}" "${TMP_FETCH}"
else
  echo "Skipping FTP download test because FTP is not active."
fi

RUN_TFTP=0
if [[ "${TEST_TFTP}" == "always" ]]; then
  RUN_TFTP=1
elif [[ "${TEST_TFTP}" == "auto" ]]; then
  TFTP_ACTIVE=$(printf '%s' "${STATUS_JSON}" | python3 -c 'import json,sys; data=json.load(sys.stdin); print("1" if data["tftp"]["active"] else "0")')
  if [[ "${TFTP_ACTIVE}" == "1" ]]; then
    RUN_TFTP=1
  fi
fi

if [[ "${RUN_TFTP}" == "1" ]]; then
  echo "Verifying TFTP download..."
  curl --max-time 20 -fsS "tftp://${FIELDKIT_HOST}/personal/${SMOKE_NAME}" > "${TMP_FETCH}"
  cmp -s "${TMP_FILE}" "${TMP_FETCH}"
else
  echo "Skipping TFTP download test."
fi

echo "Smoke test passed."
