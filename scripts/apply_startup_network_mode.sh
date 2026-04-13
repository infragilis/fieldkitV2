#!/usr/bin/env bash
set -euo pipefail

FIELDKIT_ROOT=${FIELDKIT_ROOT:-/opt/fieldkit}
SETTINGS_PATH=${SETTINGS_PATH:-${FIELDKIT_ROOT}/runtime/state/settings.json}
WIFI_INTERFACE=${WIFI_INTERFACE:-wlan0}

if [[ ${EUID} -ne 0 ]]; then
  echo "Run as root."
  exit 1
fi

if [[ ! -f ${SETTINGS_PATH} ]]; then
  echo "No settings file at ${SETTINGS_PATH}; skipping startup network apply."
  exit 0
fi

read_setting() {
  local expression=$1
  python3 -c 'import json,sys
from pathlib import Path
payload=json.loads(Path(sys.argv[1]).read_text())
value=payload
for key in sys.argv[2].split("."):
    value=value.get(key, "") if isinstance(value, dict) else ""
print(value if value is not None else "")' "${SETTINGS_PATH}" "${expression}"
}

WIFI_MODE=$(read_setting "wifi.mode")
WIFI_SSID=$(read_setting "wifi.ssid")
WIFI_PASSWORD=$(read_setting "wifi.password")
WIFI_COUNTRY=$(read_setting "wifi.country_code")
HOSTNAME=$(read_setting "hostname")

if [[ -n ${HOSTNAME} ]]; then
  /bin/bash "${FIELDKIT_ROOT}/scripts/set_appliance_hostname.sh" "${HOSTNAME}"
fi

case "${WIFI_MODE}" in
  ap)
    exec /bin/bash "${FIELDKIT_ROOT}/scripts/apply_wifi_mode.sh" \
      ap "${WIFI_INTERFACE}" "${WIFI_SSID:-fieldkit}" "${WIFI_PASSWORD:-fieldkit}" "${WIFI_COUNTRY:-US}"
    ;;
  client)
    exec /bin/bash "${FIELDKIT_ROOT}/scripts/apply_wifi_mode.sh" \
      client "${WIFI_INTERFACE}" "${WIFI_SSID:-}" "${WIFI_PASSWORD:-}" "${WIFI_COUNTRY:-US}" "${WIFI_SSID:-}" "${WIFI_PASSWORD:-}"
    ;;
  disabled|"")
    exec /bin/bash "${FIELDKIT_ROOT}/scripts/apply_wifi_mode.sh" disabled "${WIFI_INTERFACE}"
    ;;
  *)
    echo "Unsupported wifi.mode=${WIFI_MODE}"
    exit 1
    ;;
esac
