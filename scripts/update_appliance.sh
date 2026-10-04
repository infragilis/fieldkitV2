#!/usr/bin/env bash
# Apply an in-place Fieldkit update bundle (run as root via sudo).
#
# Usage: update_appliance.sh <version> <url> <sha256>
#
# Downloads the bundle, verifies its SHA-256, backs up the current install (and
# the deployed /etc configuration), STAGES the bundle, applies it with
# restore-on-failure, reapplies the deployed systemd/nginx/sudoers config, and
# restarts the web service via the persistent health-check unit. Safe to re-run;
# a failed download, checksum, extraction, or apply leaves the appliance on the
# previous version.
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
BACKUP_DIR="${BACKUP_DIR:-/root/fieldkit-backups}"

mkdir -p "${STATE_DIR}" "${BACKUP_DIR}"
exec 9>"${LOCK_FILE}"
if ! flock -n 9; then
  echo "An update is already in progress." >&2
  exit 1
fi
BUNDLE="${STATE_DIR}/fieldkit-update-${VERSION}.tgz"
STAGING="${STATE_DIR}/update-staging-${VERSION}"

STARTED="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

record_state() {
  local status=$1
  local detail=${2:-}
  printf '{"status": "%s", "version": "%s", "detail": "%s", "started_at": "%s", "finished_at": "%s"}\n' \
    "${status}" "${VERSION}" "${detail}" "${STARTED}" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" > "${STATE_FILE}"
  chown service:service "${STATE_FILE}" 2>/dev/null || true
}

# Restore the install (and the /etc configuration) from a pre-update backup.
restore_backup() {
  local tgz=$1
  echo "Restoring ${tgz}" >&2
  tar xzf "${tgz}" -C "${FIELDKIT_ROOT}" 2>/dev/null || true
  if [[ -f "${tgz%.tgz}.etc.tgz" ]]; then
    tar xzf "${tgz%.tgz}.etc.tgz" -C / 2>/dev/null || true
  fi
  chown -R service:service "${FIELDKIT_ROOT}/app" "${FIELDKIT_ROOT}/docs" 2>/dev/null || true
  chown -R root:root "${FIELDKIT_ROOT}/scripts" "${FIELDKIT_ROOT}/deploy" 2>/dev/null || true
  systemctl daemon-reload 2>/dev/null || true
}

abort_with_restore() {
  local backup=$1 detail=$2
  restore_backup "${backup}"
  record_state failed "${detail}"
  exit 1
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

echo "Backing up current install and configuration"
BACKUP_TGZ="${BACKUP_DIR}/fieldkit-update-pre-${VERSION}-$(date -u +%Y%m%dT%H%M%SZ).tgz"
# A usable rollback archive is required: refuse to proceed without one. docs is
# included because the appliance reads docs/kits at runtime.
if ! tar czf "${BACKUP_TGZ}" -C "${FIELDKIT_ROOT}" app scripts deploy docs pyproject.toml \
     README.md README.es.md README.de.md README.nl.md README.fr.md 2>/dev/null; then
  rm -f "${BACKUP_TGZ}"
  record_state failed "could not create the pre-update backup"
  exit 1
fi
# Also capture the deployed /etc configuration so rollback can restore it.
BACKUP_ETC_TGZ="${BACKUP_TGZ%.tgz}.etc.tgz"
etcfiles=()
for f in etc/nginx/sites-available/fieldkit etc/nginx/sites-enabled/fieldkit \
         etc/systemd/system-preset/00-fieldkit.preset \
         etc/sudoers.d/fieldkit-network etc/sudoers.d/fieldkit-transfer etc/sudoers.d/fieldkit-update; do
  [[ -e "/${f}" ]] && etcfiles+=("${f}")
done
if compgen -G "/etc/systemd/system/fieldkit-*" >/dev/null; then
  while IFS= read -r line; do etcfiles+=("${line#/}"); done < <(ls -1 /etc/systemd/system/fieldkit-* 2>/dev/null)
fi
if [[ ${#etcfiles[@]} -gt 0 ]]; then
  tar czf "${BACKUP_ETC_TGZ}" -C / "${etcfiles[@]}" 2>/dev/null || rm -f "${BACKUP_ETC_TGZ}"
fi
record_state backed-up "backup at ${BACKUP_TGZ}"

echo "Staging update"
rm -rf "${STAGING}"
mkdir -p "${STAGING}"
if tar tzf "${BUNDLE}" | grep -qE '(^/|(^|/)\.\.(/|$))'; then
  echo "Refusing update: archive contains unsafe paths" >&2
  rm -rf "${STAGING}"
  record_state failed "unsafe archive paths"
  exit 1
fi
if ! tar xzf "${BUNDLE}" -C "${STAGING}"; then
  rm -rf "${STAGING}" "${BUNDLE}"
  record_state failed "could not extract the bundle"
  exit 1
fi
rm -f "${BUNDLE}"
record_state applying "staged"

# Apply from the validated staging tree, restoring the backup on any failure.
for d in app scripts deploy docs; do
  [[ -d "${STAGING}/${d}" ]] || abort_with_restore "${BACKUP_TGZ}" "bundle missing ${d}"
done
for d in app scripts deploy docs; do
  rsync -a --delete --no-owner --no-group "${STAGING}/${d}/" "${FIELDKIT_ROOT}/${d}/" \
    || abort_with_restore "${BACKUP_TGZ}" "failed to apply ${d}"
done
for f in pyproject.toml README.md README.es.md README.de.md README.nl.md README.fr.md; do
  [[ -f "${STAGING}/${f}" ]] && cp -a "${STAGING}/${f}" "${FIELDKIT_ROOT}/${f}"
done
rm -rf "${STAGING}"

# App code and docs stay service-owned; root-executed helpers and their assets
# must not be writable by the web account.
chown -R service:service "${FIELDKIT_ROOT}/app" "${FIELDKIT_ROOT}/docs"
chown -R root:root "${FIELDKIT_ROOT}/scripts" "${FIELDKIT_ROOT}/deploy"
chmod 0755 "${FIELDKIT_ROOT}/scripts" "${FIELDKIT_ROOT}/deploy"
chmod 0755 "${FIELDKIT_ROOT}/scripts/"*.sh 2>/dev/null || true

echo "Applying deployed configuration"
# systemd units + preset (idempotent).
for unit in "${FIELDKIT_ROOT}"/deploy/systemd/*.service "${FIELDKIT_ROOT}"/deploy/systemd/*.timer; do
  [[ -f "${unit}" ]] || continue
  install -o root -g root -m 0644 "${unit}" /etc/systemd/system/
done
install -D -o root -g root -m 0644 \
  "${FIELDKIT_ROOT}/deploy/systemd/00-fieldkit.preset" /etc/systemd/system-preset/00-fieldkit.preset 2>/dev/null || true
# sudoers.
install -o root -g root -m 0440 "${FIELDKIT_ROOT}/deploy/sudoers/fieldkit-network" /etc/sudoers.d/fieldkit-network 2>/dev/null || true
install -o root -g root -m 0440 "${FIELDKIT_ROOT}/deploy/sudoers/fieldkit-transfer" /etc/sudoers.d/fieldkit-transfer 2>/dev/null || true
install -o root -g root -m 0440 "${FIELDKIT_ROOT}/deploy/sudoers/fieldkit-update" /etc/sudoers.d/fieldkit-update 2>/dev/null || true
# nginx site (ensure the TLS cert exists first so `nginx -t` validates the 443
# listener), then reload only if the config is valid.
if [[ -f "${FIELDKIT_ROOT}/deploy/nginx/fieldkit.conf" ]] && command -v nginx >/dev/null 2>&1; then
  [[ -x "${FIELDKIT_ROOT}/scripts/install_tls_cert.sh" ]] && \
    bash "${FIELDKIT_ROOT}/scripts/install_tls_cert.sh" >/dev/null 2>&1 || true
  install -D -o root -g root -m 0644 "${FIELDKIT_ROOT}/deploy/nginx/fieldkit.conf" /etc/nginx/sites-available/fieldkit
  ln -sf /etc/nginx/sites-available/fieldkit /etc/nginx/sites-enabled/fieldkit
  if nginx -t >/dev/null 2>&1; then
    systemctl reload nginx 2>/dev/null || systemctl restart nginx 2>/dev/null || true
  else
    echo "nginx config check failed; leaving the running config in place" >&2
  fi
fi
systemctl daemon-reload 2>/dev/null || true
systemctl enable fieldkit-tls-cert.service 2>/dev/null || true

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
record_state applying "files and configuration applied"

echo "Restarting web service with health check"
# Start a PERSISTENT unit (not systemd-run): it is not tied to this script's
# cgroup, so it survives the restart and is reliable even if systemd-run is
# unavailable. The unit reads the request file left below.
REQUEST_FILE="${BACKUP_DIR}/.post-update-request.json"
MARKER="${BACKUP_DIR}/.update-in-progress"
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
install -o root -g root -m 0644 \
  "${FIELDKIT_ROOT}/deploy/systemd/fieldkit-rollback.service" /etc/systemd/system/ 2>/dev/null || true
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
