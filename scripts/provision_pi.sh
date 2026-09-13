#!/usr/bin/env bash
set -euo pipefail

FIELDKIT_ROOT=${FIELDKIT_ROOT:-/opt/fieldkit}
FIELDKIT_USER=${FIELDKIT_USER:-service}
FIELDKIT_PASS=${FIELDKIT_PASS:-service}
FIELDKIT_HOSTNAME=${FIELDKIT_HOSTNAME:-fieldkit}
FIELDKIT_DEFAULT_WIFI_MODE=${FIELDKIT_DEFAULT_WIFI_MODE:-ap}

if [[ ${EUID} -ne 0 ]]; then
  echo "Run as root."
  exit 1
fi

if ! id -u "${FIELDKIT_USER}" >/dev/null 2>&1; then
  useradd -m -s /bin/bash "${FIELDKIT_USER}"
fi

echo "${FIELDKIT_USER}:${FIELDKIT_PASS}" | chpasswd
/bin/bash "${FIELDKIT_ROOT}/scripts/set_appliance_hostname.sh" "${FIELDKIT_HOSTNAME}"

install -d -o "${FIELDKIT_USER}" -g "${FIELDKIT_USER}" "${FIELDKIT_ROOT}"
install -d -o "${FIELDKIT_USER}" -g "${FIELDKIT_USER}" "${FIELDKIT_ROOT}/runtime/content/data"
install -d -o "${FIELDKIT_USER}" -g "${FIELDKIT_USER}" "${FIELDKIT_ROOT}/runtime/content/personal"
install -d -o "${FIELDKIT_USER}" -g "${FIELDKIT_USER}" "${FIELDKIT_ROOT}/runtime/content/usb"
install -d -m 0700 -o "${FIELDKIT_USER}" -g "${FIELDKIT_USER}" "${FIELDKIT_ROOT}/runtime/state"

SETTINGS_PATH="${FIELDKIT_ROOT}/runtime/state/settings.json"
if [[ ! -f "${SETTINGS_PATH}" ]]; then
  SETTINGS_PATH="${SETTINGS_PATH}" FIELDKIT_HOSTNAME="${FIELDKIT_HOSTNAME}" FIELDKIT_DEFAULT_WIFI_MODE="${FIELDKIT_DEFAULT_WIFI_MODE}" python3 - <<'PY'
import json
import os
import tempfile
from pathlib import Path

path = Path(os.environ["SETTINGS_PATH"])
payload = json.dumps(
    {
        "hostname": os.environ["FIELDKIT_HOSTNAME"],
        "wifi": {
            "mode": os.environ["FIELDKIT_DEFAULT_WIFI_MODE"],
            "ssid": "fieldkit",
            "password": "fieldkit",
            "country_code": "US",
        },
    }, indent=2) + "\n"
descriptor, temp_name = tempfile.mkstemp(dir=path.parent, prefix="." + path.name + ".", suffix=".tmp")
temp = Path(temp_name)
try:
    os.fchmod(descriptor, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temp, path)
finally:
    temp.unlink(missing_ok=True)
PY
  chown "${FIELDKIT_USER}:${FIELDKIT_USER}" "${SETTINGS_PATH}"
  chmod 0600 "${SETTINGS_PATH}"
else
  chmod 0600 "${SETTINGS_PATH}"
fi

cat <<EOF
Provisioning complete.

Hostname: ${FIELDKIT_HOSTNAME}
User: ${FIELDKIT_USER}
App root: ${FIELDKIT_ROOT}
Default Wi-Fi mode: ${FIELDKIT_DEFAULT_WIFI_MODE}
EOF
