#!/usr/bin/env bash
# Restore the most recent pre-update backup (run as root via sudo).
#
# Backups are written by update_appliance.sh to
# /root/fieldkit-backups/fieldkit-update-pre-<version>-<ts>.tgz and contain
# app/, scripts/, deploy/, pyproject.toml and the READMEs.
set -uo pipefail

FIELDKIT_ROOT=${FIELDKIT_ROOT:-/opt/fieldkit}
BACKUP_DIR=${BACKUP_DIR:-/root/fieldkit-backups}
STATE_DIR="${FIELDKIT_ROOT}/runtime/state"
STATE_FILE="${STATE_DIR}/update-state.json"
LOCK_FILE="${STATE_DIR}/update.lock"

ensure_running() {
  local _
  for _ in $(seq 1 20); do
    systemctl is-active --quiet fieldkit-web.service && return 0
    systemctl start fieldkit-web.service 2>/dev/null || true
    sleep 2
  done
  systemctl is-active --quiet fieldkit-web.service
}

record() {
  local status=$1 detail=${2:-}
  mkdir -p "${STATE_DIR}"
  printf '{"status": "%s", "version": "manual", "detail": "%s", "started_at": "%s", "finished_at": "%s"}\n' \
    "${status}" "${detail}" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" > "${STATE_FILE}"
  chown service:service "${STATE_FILE}" 2>/dev/null || true
}

# Never leave the web service down when this script exits.
trap 'ensure_running >/dev/null 2>&1 || true' EXIT

# Refuse to interleave with an in-flight update/health check.
mkdir -p "${STATE_DIR}"
exec 9>"${LOCK_FILE}"
if ! flock -n 9; then
  echo "An update is in progress; try again shortly." >&2
  exit 1
fi

# Refuse while an update/health check is in flight (root-only marker).
MARKER="/root/fieldkit-backups/.update-in-progress"
if [[ -e "${MARKER}" ]]; then
  echo "An update/health check is in progress; try again shortly." >&2
  exit 1
fi

LATEST="$(ls -1t "${BACKUP_DIR}"/fieldkit-update-pre-*.tgz 2>/dev/null | head -1 || true)"
if [[ -z "${LATEST}" ]]; then
  echo "No pre-update backup found in ${BACKUP_DIR}" >&2
  exit 1
fi

echo "Rolling back from ${LATEST}"
systemctl stop fieldkit-web.service 2>/dev/null || true
extracted=0
if tar xzf "${LATEST}" -C "${FIELDKIT_ROOT}"; then
  extracted=1
  # Restore the deployed /etc configuration captured alongside the backup.
  if [[ -f "${LATEST%.tgz}.etc.tgz" ]]; then
    tar xzf "${LATEST%.tgz}.etc.tgz" -C / 2>/dev/null || true
    systemctl daemon-reload 2>/dev/null || true
  fi
  chown -R service:service "${FIELDKIT_ROOT}/app" "${FIELDKIT_ROOT}/docs" 2>/dev/null || true
  chown -R root:root "${FIELDKIT_ROOT}/scripts" "${FIELDKIT_ROOT}/deploy" 2>/dev/null || true
  chmod 0755 "${FIELDKIT_ROOT}/scripts" "${FIELDKIT_ROOT}/deploy" 2>/dev/null || true
  chmod 0755 "${FIELDKIT_ROOT}/scripts/"*.sh 2>/dev/null || true
  # Re-register the restored project metadata (offline-safe).
  if [[ -x "${FIELDKIT_ROOT}/.venv/bin/pip" ]]; then
    "${FIELDKIT_ROOT}/.venv/bin/pip" install --quiet --no-build-isolation --no-deps -e "${FIELDKIT_ROOT}" \
      || echo "pip editable install after rollback failed" >&2
  fi
else
  record failed "manual rollback failed to extract ${LATEST}"
fi

if [[ "${extracted}" == "1" ]]; then
  # This script runs in its own fieldkit-rollback.service cgroup, so restarting
  # the web service here cannot terminate the rollback.
  systemctl restart fieldkit-web.service 2>/dev/null || true
  ensure_running >/dev/null 2>&1 || true
  if systemctl is-active --quiet fieldkit-web.service; then
    record rolled-back "manual rollback from ${LATEST}"
  else
    record failed "manual rollback left the web service down"
  fi
fi
echo "Rollback complete; web service restarting."
