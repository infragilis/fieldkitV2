#!/usr/bin/env bash
# Post-update restart + health check with automatic rollback (run as root).
#
# Usage: post_update_check.sh <version> <backup_tgz> [started_at]
#
# Launched by update_appliance.sh via a transient systemd unit so the restart
# does not kill the updater. Waits for /openapi.json to report the new version;
# if it does not come up, restores the pre-update backup and restarts. Holds the
# shared update lock so a manual rollback cannot interleave.
set -uo pipefail

FIELDKIT_ROOT=${FIELDKIT_ROOT:-/opt/fieldkit}
VERSION=${1:-}
BACKUP=${2:-}
STARTED=${3:-}
STATE_DIR="${FIELDKIT_ROOT}/runtime/state"
STATE_FILE="${STATE_DIR}/update-state.json"
LOCK_FILE="${STATE_DIR}/update.lock"
# Root-only handoff locations (not writable by the service account).
REQUEST_FILE="${REQUEST_FILE:-/root/fieldkit-backups/.post-update-request.json}"
MARKER="${MARKER:-/root/fieldkit-backups/.update-in-progress}"
HEALTH_URL="http://127.0.0.1:8000/openapi.json"

# When run by the fieldkit-post-update.service unit there are no args; the
# updater leaves the request in a root-only file instead.
if [[ -z "${VERSION}" && -f "${REQUEST_FILE}" && ! -L "${REQUEST_FILE}" ]]; then
  VERSION="$(sed -n 's/.*"version": "\([^"]*\)".*/\1/p' "${REQUEST_FILE}" | head -1)"
  BACKUP="$(sed -n 's/.*"backup": "\([^"]*\)".*/\1/p' "${REQUEST_FILE}" | head -1)"
  STARTED="$(sed -n 's/.*"started_at": "\([^"]*\)".*/\1/p' "${REQUEST_FILE}" | head -1)"
fi

# The backup must be a regular file inside the protected backup directory.
case "${BACKUP}" in
  /root/fieldkit-backups/fieldkit-update-pre-*.tgz) ;;
  "") ;;
  *) echo "refusing unexpected backup path: ${BACKUP}" >&2; BACKUP="" ;;
esac
if [[ -n "${BACKUP}" && ( -L "${BACKUP}" || ! -f "${BACKUP}" ) ]]; then
  echo "refusing non-regular backup: ${BACKUP}" >&2
  BACKUP=""
fi

archive_is_safe() {
  local archive=$1
  [[ -f "${archive}" && ! -L "${archive}" ]] || return 1
  tar tzf "${archive}" 2>/dev/null | grep -qE '(^/|(^|/)\.\.(/|$))' && return 1
  return 0
}

record() {
  local status=$1 detail=${2:-}
  mkdir -p "${STATE_DIR}"
  printf '{"status": "%s", "version": "%s", "detail": "%s", "started_at": "%s", "finished_at": "%s"}\n' \
    "${status}" "${VERSION}" "${detail}" "${STARTED}" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" > "${STATE_FILE}"
  chown service:service "${STATE_FILE}" 2>/dev/null || true
}

ensure_running() {
  local _
  for _ in $(seq 1 20); do
    systemctl is-active --quiet fieldkit-web.service && return 0
    systemctl start fieldkit-web.service 2>/dev/null || true
    sleep 2
  done
  systemctl is-active --quiet fieldkit-web.service
}

healthy() {
  local body
  body="$(curl -fsS --max-time 5 "${HEALTH_URL}" 2>/dev/null || true)"
  # Starlette emits compact JSON ("version":"0.2.4"); allow optional whitespace.
  [ -n "${body}" ] && printf '%s' "${body}" | grep -Eq '"version"[[:space:]]*:[[:space:]]*"'"${VERSION}"'"'
}

# Never leave the web service down, and always clear the in-progress marker.
trap 'rm -f "${MARKER}" 2>/dev/null || true; ensure_running >/dev/null 2>&1 || true' EXIT

exec 9>"${LOCK_FILE}"
if ! flock -w 120 9; then
  record failed "could not acquire the update lock"
  exit 1
fi

record restarting "restarting web service"
systemctl restart fieldkit-web.service 2>/dev/null || systemctl start fieldkit-web.service 2>/dev/null || true

healthy_ok=0
for _ in $(seq 1 30); do
  sleep 2
  if healthy; then
    healthy_ok=1
    break
  fi
done

if [[ "${healthy_ok}" == "1" ]]; then
  record applied "health check passed"
  exit 0
fi

if [[ -n "${BACKUP}" ]] && archive_is_safe "${BACKUP}"; then
  systemctl stop fieldkit-web.service 2>/dev/null || true
  if tar xzf "${BACKUP}" -C "${FIELDKIT_ROOT}"; then
    chown -R service:service "${FIELDKIT_ROOT}/app" 2>/dev/null || true
    chown -R root:root "${FIELDKIT_ROOT}/scripts" "${FIELDKIT_ROOT}/deploy" 2>/dev/null || true
    chmod 0755 "${FIELDKIT_ROOT}/scripts" "${FIELDKIT_ROOT}/deploy" 2>/dev/null || true
    chmod 0755 "${FIELDKIT_ROOT}/scripts/"*.sh 2>/dev/null || true
    ensure_running >/dev/null 2>&1 || true
    if systemctl is-active --quiet fieldkit-web.service; then
      record rolled-back "health check failed; restored the pre-update backup"
    else
      record failed "health check failed; restore did not bring the service back"
    fi
  else
    ensure_running >/dev/null 2>&1 || true
    record failed "health check failed; backup restore failed"
  fi
else
  ensure_running >/dev/null 2>&1 || true
  record failed "health check failed; no backup to restore"
fi
exit 1
