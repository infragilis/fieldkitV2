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

mkdir -p "${STATE_DIR}"
exec 9>"${LOCK_FILE}"
if ! flock -n 9; then
  echo "An update is already in progress." >&2
  exit 1
fi
BUNDLE="${STATE_DIR}/fieldkit-update-${VERSION}.tgz"

STARTED="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

record_state() {
  local status=$1
  local detail=${2:-}
  printf '{"status": "%s", "version": "%s", "detail": "%s", "started_at": "%s", "finished_at": "%s"}\n' \
    "${status}" "${VERSION}" "${detail}" "${STARTED}" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" > "${STATE_FILE}"
  chown service:service "${STATE_FILE}" 2>/dev/null || true
}

# Make sure any unexpected exit leaves a visible failed state.
trap 'record_state failed "unexpected error at line ${LINENO}"' ERR

echo "Downloading ${VERSION} from ${URL}"
curl -fSL --retry 2 --connect-timeout 10 --max-time 300 -o "${BUNDLE}" "${URL}"
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
# A usable rollback archive is required: refuse to proceed without one.
if ! tar czf "${BACKUP_TGZ}" -C "${FIELDKIT_ROOT}" app scripts deploy pyproject.toml \
     README.md README.es.md README.de.md README.nl.md README.fr.md 2>/dev/null; then
  rm -f "${BACKUP_TGZ}"
  record_state failed "could not create the pre-update backup"
  exit 1
fi
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

# Refresh the editable install so version/dependency metadata matches the
# bundle. Offline-safe: with a bundled wheels/ dir pip installs deps from it;
# otherwise the project is re-registered without touching the network.
PIP="${FIELDKIT_ROOT}/.venv/bin/pip"
if [[ -x "${PIP}" ]]; then
  # --no-build-isolation avoids pip fetching PEP 517 build deps from the
  # network; the venv already has setuptools/wheel.
  if [[ -d "${FIELDKIT_ROOT}/wheels" ]]; then
    "${PIP}" install --quiet --no-build-isolation --no-index --find-links "${FIELDKIT_ROOT}/wheels" -e "${FIELDKIT_ROOT}" \
      || echo "pip install from bundled wheels failed" >&2
  else
    "${PIP}" install --quiet --no-build-isolation --no-deps -e "${FIELDKIT_ROOT}" \
      || echo "pip editable install failed" >&2
  fi
fi

echo "Restarting web service with health check"
# Start a PERSISTENT unit (not systemd-run): it is not tied to this script's
# cgroup, so it survives the restart and is reliable even if systemd-run is
# unavailable. The unit reads the request file left below.
REQUEST_FILE="/root/fieldkit-backups/.post-update-request.json"
MARKER="/root/fieldkit-backups/.update-in-progress"
umask 077
printf '{"version": "%s", "backup": "%s", "started_at": "%s"}\n' \
  "${VERSION}" "${BACKUP_TGZ}" "${STARTED}" > "${REQUEST_FILE}"
chmod 0600 "${REQUEST_FILE}" 2>/dev/null || true
# Marker blocks a manual rollback from racing the asynchronous health check;
# post_update_check.sh removes it on exit.
: > "${MARKER}"
chmod 0600 "${MARKER}" 2>/dev/null || true
install -o root -g root -m 0644 \
  "${FIELDKIT_ROOT}/deploy/systemd/fieldkit-post-update.service" /etc/systemd/system/ 2>/dev/null || true
systemctl daemon-reload 2>/dev/null || true
systemctl reset-failed fieldkit-post-update.service 2>/dev/null || true
if ! systemctl start --no-block fieldkit-post-update.service 2>/dev/null; then
  rm -f "${MARKER}" 2>/dev/null || true
  # Last resort: restart directly (no health check) rather than leave it down.
  echo "post-update unit failed to start; restarting web service directly" >&2
  record_state failed "post-update health check could not start"
  systemctl restart fieldkit-web.service 2>/dev/null || true
fi
echo "Update to ${VERSION} applied."
