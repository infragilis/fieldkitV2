#!/bin/bash
# Fieldkit first-boot root grow.
#
# The distributable golden image ships with the root partition shrunk to just
# above the filesystem size. On first boot this grows the root partition to
# fill the boot media (32/64/128 GB microSD, etc.) and then grows the
# filesystem. It is armed by the /etc/fieldkit-growroot flag the golden
# builder drops in; the flag is removed once the attempt completes.
set -u

flag=/etc/fieldkit-growroot
[ -e "$flag" ] || exit 0

root_src="$(findmnt -n -o SOURCE / 2>/dev/null || true)"
case "$root_src" in
  /dev/*) ;;
  *) echo "fieldkit-growroot: unexpected root device '$root_src'"; exit 0 ;;
esac

# /dev/mmcblk0p1 -> disk=/dev/mmcblk0 part=1 ; /dev/sda1 -> /dev/sda 1
disk="$(printf '%s' "$root_src" | sed -E 's/p?[0-9]+$//')"
part="$(printf '%s' "$root_src" | sed -E 's/^.*[^0-9]([0-9]+)$/\1/')"

if [ ! -b "$disk" ] || [ -z "${part:-}" ]; then
  echo "fieldkit-growroot: cannot parse root device '$root_src'"
  exit 0
fi

if ! command -v growpart >/dev/null 2>&1; then
  echo "fieldkit-growroot: growpart not installed; leaving $flag for next boot"
  exit 0
fi

# The image is dd'd to a larger card, so the GPT backup header sits mid-disk;
# move it to the end and refresh the last-usable sector before growing.
if command -v sgdisk >/dev/null 2>&1; then
  sgdisk -e "$disk" >/dev/null 2>&1 || true
fi

echo "fieldkit-growroot: growing ${disk} partition ${part} (${root_src})"
# growpart is best-effort (it exits non-zero for "NOCHANGE" on already-full
# media). Only disarm the flag once resize2fs succeeds, so a real failure
# retries on the next boot instead of silently leaving the card ungrown.
growpart "$disk" "$part" >/dev/null 2>&1 || true
if resize2fs "$root_src"; then
  rm -f "$flag"
  exit 0
fi
echo "fieldkit-growroot: resize2fs failed; leaving $flag for the next boot"
exit 1
