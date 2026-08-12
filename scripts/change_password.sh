#!/usr/bin/env bash
set -euo pipefail

TARGET_USER=${1:-service}
CURRENT_PASSWORD=${2:-}
NEW_PASSWORD=${3:-}

if [[ ${EUID} -ne 0 ]]; then
  echo "Run as root."
  exit 1
fi

if [[ -z ${CURRENT_PASSWORD} || -z ${NEW_PASSWORD} ]]; then
  echo "Usage: change_password.sh <user> <current_password> <new_password>"
  exit 1
fi

if [[ ${#NEW_PASSWORD} -lt 4 ]]; then
  echo "New password is too short."
  exit 1
fi

if ! python3 - "${TARGET_USER}" "${CURRENT_PASSWORD}" <<'PY'
import ctypes
import sys

user, current = sys.argv[1], sys.argv[2]
stored = None
with open("/etc/shadow", encoding="utf-8") as handle:
    for line in handle:
        fields = line.rstrip("\n").split(":")
        if fields and fields[0] == user:
            stored = fields[1] if len(fields) > 1 else ""
            break
if stored is None:
    print(f"User {user} not found in /etc/shadow.", file=sys.stderr)
    sys.exit(1)
if stored in {"!", "*", "!!"}:
    print(f"Password login is locked for {user}.", file=sys.stderr)
    sys.exit(1)
libcrypt = ctypes.CDLL("libcrypt.so.1")
libcrypt.crypt.restype = ctypes.c_char_p
computed = libcrypt.crypt(current.encode(), stored.encode())
if computed is None or computed.decode() != stored:
    print("Current password is incorrect.", file=sys.stderr)
    sys.exit(1)
print("verified")
PY
then
  exit 1
fi

printf '%s:%s\n' "${TARGET_USER}" "${NEW_PASSWORD}" | chpasswd
echo "Password changed for ${TARGET_USER}."
