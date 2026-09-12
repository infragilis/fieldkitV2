#!/usr/bin/env bash
# Apply an in-place Fieldkit update bundle (run as root via sudo).
#
# Usage: update_appliance.sh <version> <url> <sha256>
#
# Downloads the update bundle, verifies its SHA-256, backs up the current
# app/scripts/deploy trees, extracts the new files, and restarts the web
# service. Safe to re-run; a failed download or checksum leaves the running
# appliance untouched.
set -euo pipefail

FIELDKIT_ROOT=${FIELDKIT_ROOT:-/opt/fieldkit}
VERSION=$1
URL=$2
SHA256=$3

if [[ -z "${VERSION}" || -z "${URL}" || -z "${SHA256}" ]]; then
  echo "Usage: update_appliance.sh <version> <url> <sha256>" >&2
  exit 2
fi

# Defensive validation: the route already derives these from the trusted server,
# but the script may also be invoked directly.
if [[ ! "${VERSION}" =~ ^[0-9]+(\.[0-9]+){1,3}$ ]]; then
  echo "Invalid version: ${VERSION}" >&2
  exit 2
fi
if [[ ! "${SHA256}" =~ ^[0-9a-fA-F]{64}$ ]]; then
  echo "Invalid sha256" >&2
  exit 2
fi
if [[ ! "${URL}" =~ ^https:// ]]; then
  echo "Update URL must be https" >&2
  exit 2
fi

STATE_DIR="${FIELDKIT_ROOT}/runtime/state"
STATE_FILE="${STATE_DIR}/update-state.json"
LOCK_FILE="${STATE_DIR}/update.lock"

if [[ -f "${LOCK_FILE}" ]]; then
  echo "An update is already in progress." >&2
  exit 1
fi
trap 'rm -f "${LOCK_FILE}"' EXIT
touch "${LOCK_FILE}"

mkdir -p "${STATE_DIR}"
BUNDLE="${STATE_DIR}/fieldkit-update-${VERSION}.tgz"

record_state() {
  local status=$1
  local detail=${2:-}
  printf '{"status": "%s", "version": "%s", "detail": "%s", "finished_at": "%s"}\n' \
    "${status}" "${VERSION}" "${detail}" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" > "${STATE_FILE}"
  chown service:service "${STATE_FILE}" 2>/dev/null || true
}

echo "Downloading ${VERSION} from ${URL}"
curl -fSL --retry 2 -o "${BUNDLE}" "${URL}"
record_state downloading "downloaded ${VERSION}"

echo "Verifying checksum"
echo "${SHA256}  ${BUNDLE}" | sha256sum -c - || {
  rm -f "${BUNDLE}"
  record_state failed "checksum mismatch"
  exit 1
}
record_state verified "checksum ok"

echo "Backing up current install"
BACKUP_DIR="/root/fieldkit-backups"
mkdir -p "${BACKUP_DIR}"
BACKUP_TGZ="${BACKUP_DIR}/fieldkit-update-pre-${VERSION}-$(date -u +%Y%m%dT%H%M%SZ).tgz"
tar czf "${BACKUP_TGZ}" -C "${FIELDKIT_ROOT}" app scripts deploy 2>/dev/null || true
record_state backed-up "backup at ${BACKUP_TGZ}"

echo "Extracting update"
if tar tzf "${BUNDLE}" | grep -qE '(^/|(^|/)\.\.(/|$))'; then
  echo "Refusing update: archive contains unsafe paths" >&2
  record_state failed "unsafe archive paths"
  exit 1
fi
tar xzf "${BUNDLE}" -C "${FIELDKIT_ROOT}"
# App code stays service-owned; root-executed helpers and their assets must not
# be writable by the web account.
chown -R service:service "${FIELDKIT_ROOT}/app"
chown -R root:root "${FIELDKIT_ROOT}/scripts" "${FIELDKIT_ROOT}/deploy"
chmod 0755 "${FIELDKIT_ROOT}/scripts" "${FIELDKIT_ROOT}/deploy"
chmod 0755 "${FIELDKIT_ROOT}/scripts/"*.sh 2>/dev/null || true
install -o root -g root -m 0440 "${FIELDKIT_ROOT}/deploy/sudoers/fieldkit-network" /etc/sudoers.d/fieldkit-network 2>/dev/null || true
install -o root -g root -m 0440 "${FIELDKIT_ROOT}/deploy/sudoers/fieldkit-transfer" /etc/sudoers.d/fieldkit-transfer 2>/dev/null || true
install -o root -g root -m 0440 "${FIELDKIT_ROOT}/deploy/sudoers/fieldkit-update" /etc/sudoers.d/fieldkit-update 2>/dev/null || true
rm -f "${BUNDLE}"
record_state applying "files extracted"

echo "Restarting web service"
record_state applied "update applied; restarting"
# Restart from a transient unit so the restart does not kill this script
# (a plain systemctl restart stops the service cgroup that spawned it).
systemd-run --collect --no-block --unit=fieldkit-post-update \
  systemctl restart fieldkit-web.service 2>/dev/null || true
echo "Update to ${VERSION} applied."
