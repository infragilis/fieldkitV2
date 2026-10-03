#!/usr/bin/env bash
# Golden image build (runs on an x86_64 build host, e.g. the fieldkit-server VM).
#
# Downloads the official Debian 13 (trixie) arm64 Raspberry Pi image, grows it,
# chroots in with qemu-user-static, runs the Fieldkit installer + sysprep, then
# shrinks and compresses the result for the /get page.
#
# Requires: qemu-user-static, parted, e2fsprogs, pv, xz-utils, curl, sudo, gdisk.
# See docs/golden-image-build.md.

set -euo pipefail

WORKDIR=${WORKDIR:-/opt/fieldkit-golden}
BASE_URL=${BASE_URL:-https://cloud.debian.org/images/cloud/trixie/daily/latest/debian-13-raspi-arm64-daily.tar.xz}
IMAGE_NAME=${IMAGE_NAME:-fieldkit-v0.2.2.img}
REPO_CHECKOUT=${REPO_CHECKOUT:-/home/user/fieldkit}

log() {
  printf '\n==> %s\n' "$*"
}

if [[ ${EUID} -ne 0 ]]; then
  echo "Run as root (sudo bash scripts/golden-image-build.sh)"
  exit 1
fi

mkdir -p "${WORKDIR}"
cd "${WORKDIR}"

log "Downloading base image"
if [[ ! -f base.tar.xz ]]; then
  curl -fSL --retry 3 -o base.tar.xz "${BASE_URL}"
fi

log "Extracting image"
mkdir -p extracted
tar -xf base.tar.xz -C extracted
RAW_IMG="$(find extracted -maxdepth 1 -name '*.img' -o -name '*.raw' | head -1)"
if [[ -z "${RAW_IMG}" ]]; then
  echo "No raw image found inside the archive"
  exit 1
fi

log "Growing image to 8 GiB"
truncate -s 8G "${RAW_IMG}"

log "Attaching image"
LOOP="$(losetup -Pf --show "${RAW_IMG}")"
echo "loop device: ${LOOP}"

log "Growing root partition (Debian cloud layout: root=p1, boot=p15)"
parted -s "${LOOP}" resizepart 1 100% || true
partprobe "${LOOP}" || true
ROOT_PART="${LOOP}p1"
BOOT_PART="${LOOP}p15"
e2fsck -fy "${ROOT_PART}" || true
resize2fs "${ROOT_PART}"

log "Mounting rootfs"
mkdir -p mnt
mount "${ROOT_PART}" mnt
mount "${BOOT_PART}" mnt/boot/firmware 2>/dev/null || true

log "Preparing chroot"
install -m 0644 /etc/resolv.conf mnt/etc/resolv.conf
cp /usr/bin/qemu-aarch64-static mnt/usr/bin/

log "Cloning the Fieldkit release into the image"
rm -rf mnt/opt/fieldkit
LOCAL_CHECKOUT=${LOCAL_CHECKOUT:-/opt/fieldkit-golden-builder}
if [[ -d "${LOCAL_CHECKOUT}/.git" ]]; then
  git clone --branch "${FIELDKIT_BRANCH:-main}" "file://${LOCAL_CHECKOUT}" mnt/opt/fieldkit
else
  git clone --branch "${FIELDKIT_BRANCH:-main}" "${FIELDKIT_REPO_URL:-https://github.com/infragilis/fieldkitV2.git}" mnt/opt/fieldkit
fi
# The chroot helper must match the build host's working tree, not the clone's
# committed HEAD (the builder checkout may carry uncommitted script fixes).
install -m 0755 "${LOCAL_CHECKOUT}/scripts/golden-chroot-install.sh" mnt/opt/fieldkit/scripts/golden-chroot-install.sh

log "Running installer inside the chroot (this is the slow part)"
mount -t proc proc mnt/proc
mount -t sysfs sysfs mnt/sys
mount -t devtmpfs devtmpfs mnt/dev || mount --bind /dev mnt/dev
mount -t devpts devpts mnt/dev/pts || true
GOLDEN_MODE=install chroot mnt /bin/bash /opt/fieldkit/scripts/golden-chroot-install.sh

log "Saving pre-sysprep snapshot for future refresh builds"
cp -a "${RAW_IMG}" installed.img

log "Sysprepping the image"
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
PART_START="$(sgdisk -i 1 "${RAW_IMG}" | awk -F: '/First sector/ {gsub(/ /,"",$2); sub(/\(.*/,"",$2); print $2}')"
TYPE_GUID="$(sgdisk -i 1 "${RAW_IMG}" | awk -F: '/Partition GUID code/ {gsub(/ /,"",$2); sub(/\(.*/,"",$2); print $2}')"
UNIQ_GUID="$(sgdisk -i 1 "${RAW_IMG}" | awk -F: '/Partition unique GUID/ {gsub(/ /,"",$2); sub(/\(.*/,"",$2); print $2}')"
BOOT_START="$(sgdisk -i 15 "${RAW_IMG}" | awk -F: '/First sector/ {gsub(/ /,"",$2); sub(/\(.*/,"",$2); print $2}')"
BOOT_END="$(sgdisk -i 15 "${RAW_IMG}" | awk -F: '/Last sector/ {gsub(/ /,"",$2); sub(/\(.*/,"",$2); print $2}')"
BOOT_TYPE="$(sgdisk -i 15 "${RAW_IMG}" | awk -F: '/Partition GUID code/ {gsub(/ /,"",$2); sub(/\(.*/,"",$2); print $2}')"
BOOT_UNIQ="$(sgdisk -i 15 "${RAW_IMG}" | awk -F: '/Partition unique GUID/ {gsub(/ /,"",$2); sub(/\(.*/,"",$2); print $2}')"
SLACK_SECTORS=$(( SLACK / 512 ))
NEW_END_SECTORS=$(( PART_START + (FS_BYTES / 512) + SLACK_SECTORS ))
losetup -d "${LOOP}"
truncate -s "$(( (NEW_END_SECTORS + 34) * 512 ))" "${RAW_IMG}"
sgdisk -Z -o \
  -n "15:${BOOT_START}:${BOOT_END}" -t "15:${BOOT_TYPE}" -u "15:${BOOT_UNIQ}" \
  -n "1:${PART_START}:${NEW_END_SECTORS}" -t "1:${TYPE_GUID}" -u "1:${UNIQ_GUID}" \
  -e "${RAW_IMG}"

log "Compressing (this also takes a while)"
xz -T0 -6 -c "${RAW_IMG}" > "${IMAGE_NAME}.xz"
sha256sum "${IMAGE_NAME}.xz" > "${IMAGE_NAME}.xz.sha256"
rm -f "${RAW_IMG}"

log "Done"
echo "Image: ${WORKDIR}/${IMAGE_NAME}.xz"
cat "${WORKDIR}/${IMAGE_NAME}.xz.sha256"
