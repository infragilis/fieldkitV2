#!/usr/bin/env bash
# Fieldkit USB automount helper.
#
# Invoked by the templated unit fieldkit-usb-mount@.service, which the udev rule
# 99-fieldkit-usb.rules starts when a removable USB filesystem appears. Mounts
# the volume under /media so the appliance's `usb` library (copy-to-USB) can use
# it, with service-writable ownership so the web account can copy files on. The
# unit is BindsTo the device unit, so removal stops it and runs ExecStop here.
#
# Usage: fieldkit-usb.sh <mount|umount> <device>   (device: sda1 or /dev/sda1)
set -euo pipefail

ACTION=${1:-}
DEV=$(basename "${2:-}")
if [[ -z "${ACTION}" || -z "${DEV}" ]]; then
  echo "usage: fieldkit-usb.sh <mount|umount> <device>" >&2
  exit 2
fi
DEVNODE="/dev/${DEV}"
STATE_DIR=/run/fieldkit-usb
STATE_FILE="${STATE_DIR}/${DEV}"

sanitize() { printf '%s' "$1" | tr -c 'A-Za-z0-9._-' '-' | sed -E 's/-+/-/g; s/^-//; s/-$//'; }
svc_uid() { id -u service 2>/dev/null || echo 1001; }
svc_gid() { id -g service 2>/dev/null || echo 1001; }

case "${ACTION}" in
  mount)
    [[ -b "${DEVNODE}" ]] || { echo "not a block device: ${DEVNODE}" >&2; exit 1; }
    # Only USB mass storage: never the SD card / NVMe system disk.
    if command -v udevadm >/dev/null 2>&1; then
      bus=$(udevadm info -q property -n "${DEVNODE}" 2>/dev/null | sed -n 's/^ID_BUS=//p' | head -1)
      [[ "${bus}" == "usb" ]] || { echo "skipping ${DEVNODE}: not USB"; exit 0; }
    fi
    fstype=$(blkid -s TYPE -o value "${DEVNODE}" 2>/dev/null || true)
    case "${fstype}" in
      vfat|exfat|ext3|ext4) ;;
      *) echo "skipping ${DEVNODE}: unsupported fs '${fstype:-none}'"; exit 0 ;;
    esac
    if findmnt -rn -S "${DEVNODE}" >/dev/null 2>&1; then
      echo "${DEVNODE} already mounted"; exit 0
    fi
    label=$(blkid -s LABEL -o value "${DEVNODE}" 2>/dev/null || true)
    name=$(sanitize "${label:-${DEV}}")
    [[ -n "${name}" ]] || name="${DEV}"
    mp="/media/${name}"
    if mountpoint -q "${mp}" 2>/dev/null || findmnt -rn -S "${DEVNODE}" >/dev/null 2>&1; then
      mp="/media/${name}-${DEV}"
    fi
    mkdir -p "${mp}"
    opts="noatime,nosuid,nodev"
    case "${fstype}" in
      vfat)  opts="${opts},uid=$(svc_uid),gid=$(svc_gid),umask=022,utf8=1,shortname=mixed" ;;
      exfat) opts="${opts},uid=$(svc_uid),gid=$(svc_gid),umask=022" ;;
    esac
    if ! mount -o "${opts}" "${DEVNODE}" "${mp}"; then
      rmdir "${mp}" 2>/dev/null || true
      echo "failed to mount ${DEVNODE} at ${mp}" >&2
      exit 1
    fi
    mkdir -p "${STATE_DIR}"
    printf '%s\n' "${mp}" > "${STATE_FILE}"
    echo "mounted ${DEVNODE} at ${mp}"
    ;;
  umount)
    mp=""
    [[ -f "${STATE_FILE}" ]] && mp=$(cat "${STATE_FILE}" 2>/dev/null || true)
    [[ -n "${mp}" ]] || mp="/media/$(sanitize "${DEV}")"
    if mountpoint -q "${mp}" 2>/dev/null; then
      umount "${mp}" 2>/dev/null || umount -l "${mp}" 2>/dev/null || true
    fi
    rmdir "${mp}" 2>/dev/null || true
    rm -f "${STATE_FILE}"
    echo "unmounted ${DEVNODE}"
    ;;
  *)
    echo "unknown action: ${ACTION}" >&2
    exit 2
    ;;
esac
