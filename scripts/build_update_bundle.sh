#!/usr/bin/env bash
# Build an in-place update bundle from the current checkout.
#
# Usage: build_update_bundle.sh <version> [--publish-command "..."]
#
# Produces dist/fieldkit-update-<version>.tgz (app/, scripts/, deploy/ only —
# no runtime, venv, tests, or knowledge files) plus dist/fieldkit-update-latest.json
# with the version, SHA-256, public URL and publish time.
set -euo pipefail

VERSION=$1
if [[ -z "${VERSION}" ]]; then
  echo "Usage: build_update_bundle.sh <version>" >&2
  exit 2
fi

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DIST="${ROOT}/dist"
mkdir -p "${DIST}"

# Bind the bundle version to the code it contains: the health check compares it
# against the FastAPI version served by /openapi.json.
PYPROJECT_VERSION="$(sed -n 's/^version = "\(.*\)"/\1/p' "${ROOT}/pyproject.toml" | head -1)"
MAIN_VERSION="$(sed -n 's/.*version="\([^"]*\)".*/\1/p' "${ROOT}/app/main.py" | head -1)"
if [[ "${VERSION}" != "${PYPROJECT_VERSION}" || "${VERSION}" != "${MAIN_VERSION}" ]]; then
  echo "Version mismatch: arg=${VERSION} pyproject=${PYPROJECT_VERSION} app/main.py=${MAIN_VERSION}" >&2
  exit 2
fi
BUNDLE="fieldkit-update-${VERSION}.tgz"
BUNDLE_PATH="${DIST}/${BUNDLE}"
PUBLIC_URL="${PUBLIC_URL:-https://fieldkit.nyc3.digitaloceanspaces.com/fieldkit/releases/${BUNDLE}}"

# pyproject.toml + READMEs ship too: the appliance reads its version from
# /opt/fieldkit/pyproject.toml, and the READMEs are served by /readme.
tar czf "${BUNDLE_PATH}" \
  --exclude='app/static/vendor' \
  --exclude='*/__pycache__' \
  --exclude='app/*.egg-info' \
  -C "${ROOT}" app scripts deploy pyproject.toml \
  README.md README.es.md README.de.md README.nl.md README.fr.md

SHA256="$(sha256sum "${BUNDLE_PATH}" | cut -d' ' -f1)"
python3 - "${DIST}/fieldkit-update-latest.json" "${VERSION}" "${BUNDLE}" "${PUBLIC_URL}" "${SHA256}" <<'PY'
import json, sys
from datetime import datetime, timezone
path, version, bundle, url, sha256 = sys.argv[1:]
payload = {
    "version": version,
    "file": bundle,
    "url": url,
    "sha256": sha256,
    "published_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
}
json.dump(payload, open(path, "w"), indent=2)
print(json.dumps(payload, indent=2))
PY

echo "Bundle: ${BUNDLE_PATH}"
echo "sha256: ${SHA256}"
