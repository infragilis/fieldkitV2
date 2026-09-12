#!/usr/bin/env bash
set -euo pipefail

HOSTNAME_VALUE=${1:-}

if [[ ${EUID} -ne 0 ]]; then
  echo "Run as root."
  exit 1
fi

if [[ -z ${HOSTNAME_VALUE} ]]; then
  echo "Usage: set_appliance_hostname.sh <hostname>"
  exit 1
fi

# Single RFC 1123 label only; reject anything that could inject /etc/hosts lines.
if [[ ! ${HOSTNAME_VALUE} =~ ^[A-Za-z0-9]([A-Za-z0-9-]{0,61}[A-Za-z0-9])?$ ]]; then
  echo "Invalid hostname: ${HOSTNAME_VALUE}" >&2
  exit 1
fi

hostnamectl set-hostname "${HOSTNAME_VALUE}"

python3 - "${HOSTNAME_VALUE}" <<'PY'
from pathlib import Path
import sys

hostname = sys.argv[1]
hosts_path = Path("/etc/hosts")
lines = hosts_path.read_text(encoding="utf-8").splitlines()
updated = []
found = False
for line in lines:
    stripped = line.strip()
    if stripped.startswith("127.0.1.1"):
        updated.append(f"127.0.1.1 {hostname} {hostname}")
        found = True
    else:
        updated.append(line)
if not found:
    updated.append(f"127.0.1.1 {hostname} {hostname}")
hosts_path.write_text("\n".join(updated) + "\n", encoding="utf-8")
PY

if systemctl list-unit-files avahi-daemon.service >/dev/null 2>&1; then
  systemctl restart avahi-daemon >/dev/null 2>&1 || true
fi
