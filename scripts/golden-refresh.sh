#!/usr/bin/env bash
# Fast golden-image refresh: rebuild the distributable image from the saved
# pre-sysprep snapshot, applying only the changed repository files.
#
# Skips the slow emulated OS/package install entirely. Run after pushing code
# changes to main when a fresh flash-and-go image is needed quickly.
#
# Requires installed.img (saved by scripts/golden-image-build.sh), a local
# checkout to copy from, and gdisk for the final GPT repair.
# See docs/golden-image-build.md.

set -euo pipefail

WORKDIR=${WORKDIR:-/opt/fieldkit-golden}
IMAGE_NAME=${IMAGE_NAME:-fieldkit-v0.1.7.img}
LOCAL_CHECKOUT=${LOCAL_CHECKOUT:-/opt/fieldkit-golden-builder}
FIELDKIT_BRANCH=${FIELDKIT_BRANCH:-main}

log() {
  printf '\n==> %s\n' "$*"
}

if [[ ${EUID} -ne 0 ]]; then
  echo "Run as root (sudo bash scripts/golden-refresh.sh)"
  exit 1
fi

cd "${WORKDIR}"
if [[ ! -f installed.img ]]; then
  echo "installed.img snapshot not found; run scripts/golden-image-build.sh once first"
  exit 1
fi

log "Copying snapshot"
cp -a installed.img refresh.img

log "Attaching image"
LOOP="$(losetup -Pf --show refresh.img)"
ROOT_PART="${LOOP}p1"
BOOT_PART="${LOOP}p15"
e2fsck -fy "${ROOT_PART}" || true
mkdir -p mnt
mount "${ROOT_PART}" mnt
mount "${BOOT_PART}" mnt/boot/firmware 2>/dev/null || true
install -m 0644 /etc/resolv.conf mnt/etc/resolv.conf
cp /usr/bin/qemu-aarch64-static mnt/usr/bin/
mount -t proc proc mnt/proc
mount -t sysfs sysfs mnt/sys
mount -t devtmpfs devtmpfs mnt/dev || mount --bind /dev mnt/dev
mount -t devpts devpts mnt/dev/pts || true

log "Updating the Fieldkit source inside the image"
if [[ -d "${LOCAL_CHECKOUT}/.git" ]]; then
  git -C "${LOCAL_CHECKOUT}" fetch origin "${FIELDKIT_BRANCH}" 2>/dev/null || true
  git -C "${LOCAL_CHECKOUT}" checkout "${FIELDKIT_BRANCH}" 2>/dev/null || true
  rsync -a --delete --exclude .git --exclude runtime --exclude .venv \
    "${LOCAL_CHECKOUT}/" mnt/opt/fieldkit/
else
  rm -rf mnt/opt/fieldkit
  git clone --branch "${FIELDKIT_BRANCH}" "${FIELDKIT_REPO_URL:-https://github.com/infragilis/fieldkitV2.git}" mnt/opt/fieldkit
fi

log "Re-running installer hooks in the chroot (idempotent; usually seconds)"
chroot mnt /bin/bash -c \
  "/opt/fieldkit/.venv/bin/pip install --quiet -e /opt/fieldkit || true"
GOLDEN_MODE=sysprep chroot mnt /bin/bash /opt/fieldkit/scripts/golden-chroot-install.sh

log "Unmounting"
umount mnt/dev/pts 2>/dev/null || true
umount mnt/dev 2>/dev/null || true
umount mnt/sys 2>/dev/null || true
umount mnt/proc 2>/dev/null || true
umount mnt/boot/firmware 2>/dev/null || true
umount mnt

log "Shrinking filesystem and partition"
e2fsck -fy "${ROOT_PART}" || true
resize2fs -M "${ROOT_PART}"
BLOCK_SIZE="$(dumpe2fs -h "${ROOT_PART}" 2>/dev/null | awk -F: '/Block size/ {gsub(/ /,"",$2); print $2}')"
BLOCK_COUNT="$(dumpe2fs -h "${ROOT_PART}" 2>/dev/null | awk -F: '/Block count/ {gsub(/ /,"",$2); print $2}')"
FS_BYTES=$(( BLOCK_SIZE * BLOCK_COUNT ))
SLACK=$(( 256 * 1024 * 1024 ))
PART_START="$(sgdisk -i 1 refresh.img | awk -F: '/First sector/ {gsub(/ /,"",$2); sub(/\(.*/,"",$2); print $2}')"
TYPE_GUID="$(sgdisk -i 1 refresh.img | awk -F: '/Partition GUID code/ {gsub(/ /,"",$2); sub(/\(.*/,"",$2); print $2}')"
UNIQ_GUID="$(sgdisk -i 1 refresh.img | awk -F: '/Partition unique GUID/ {gsub(/ /,"",$2); sub(/\(.*/,"",$2); print $2}')"
BOOT_START="$(sgdisk -i 15 refresh.img | awk -F: '/First sector/ {gsub(/ /,"",$2); sub(/\(.*/,"",$2); print $2}')"
BOOT_END="$(sgdisk -i 15 refresh.img | awk -F: '/Last sector/ {gsub(/ /,"",$2); sub(/\(.*/,"",$2); print $2}')"
BOOT_TYPE="$(sgdisk -i 15 refresh.img | awk -F: '/Partition GUID code/ {gsub(/ /,"",$2); sub(/\(.*/,"",$2); print $2}')"
BOOT_UNIQ="$(sgdisk -i 15 refresh.img | awk -F: '/Partition unique GUID/ {gsub(/ /,"",$2); sub(/\(.*/,"",$2); print $2}')"
SLACK_SECTORS=$(( SLACK / 512 ))
NEW_END_SECTORS=$(( PART_START + (FS_BYTES / 512) + SLACK_SECTORS ))
losetup -d "${LOOP}"
truncate -s "$(( (NEW_END_SECTORS + 34) * 512 ))" refresh.img
sgdisk -Z -o \
  -n "15:${BOOT_START}:${BOOT_END}" -t "15:${BOOT_TYPE}" -u "15:${BOOT_UNIQ}" \
  -n "1:${PART_START}:${NEW_END_SECTORS}" -t "1:${TYPE_GUID}" -u "1:${UNIQ_GUID}" \
  -e refresh.img

log "Compressing"
xz -T0 -6 -c refresh.img > "${IMAGE_NAME}.xz"
sha256sum "${IMAGE_NAME}.xz" > "${IMAGE_NAME}.xz.sha256"
rm -f refresh.img

log "Done"
echo "Image: ${WORKDIR}/${IMAGE_NAME}.xz"
cat "${WORKDIR}/${IMAGE_NAME}.xz.sha256"
