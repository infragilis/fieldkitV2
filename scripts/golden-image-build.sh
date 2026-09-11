#!/usr/bin/env bash
# Golden image build (runs on an x86_64 build host, e.g. the fieldkit-server VM).
#
# Downloads the official Debian 13 (trixie) arm64 Raspberry Pi image, grows it,
# chroots in with qemu-user-static, runs the Fieldkit installer + sysprep, then
# shrinks and compresses the result for the /get page.
#
# Requires: qemu-user-static, parted, e2fsprogs, pv, xz-utils, curl, sudo.
# See docs/golden-image-build.md.

set -euo pipefail

WORKDIR=${WORKDIR:-/opt/fieldkit-golden}
BASE_URL=${BASE_URL:-https://cloud.debian.org/images/cloud/trixie/daily/latest/debian-13-raspi-arm64-daily.tar.xz}
IMAGE_NAME=${IMAGE_NAME:-fieldkit-v0.1.6.img}
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

log "Growing root partition"
parted -s "${LOOP}" resizepart 2 100% || true
partprobe "${LOOP}" || true
ROOT_PART="${LOOP}p2"
e2fsck -fy "${ROOT_PART}" || true
resize2fs "${ROOT_PART}"

log "Mounting rootfs"
mkdir -p mnt
mount "${ROOT_PART}" mnt
mount "${LOOP}p1" mnt/boot/firmware 2>/dev/null || true

log "Preparing chroot"
install -m 0644 /etc/resolv.conf mnt/etc/resolv.conf
cp /usr/bin/qemu-aarch64-static mnt/usr/bin/

log "Cloning the Fieldkit release into the image"
rm -rf mnt/opt/fieldkit
git clone --branch "${FIELDKIT_BRANCH:-main}" "${FIELDKIT_REPO_URL:-https://github.com/infragilis/fieldkitV2.git}" mnt/opt/fieldkit

log "Running installer inside the chroot (this is the slow part)"
mount -t proc proc mnt/proc
mount -t sysfs sysfs mnt/sys
mount -t devtmpfs devtmpfs mnt/dev || mount --bind /dev mnt/dev
mount -t devpts devpts mnt/dev/pts || true
chroot mnt /bin/bash /opt/fieldkit/scripts/golden-chroot-install.sh

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
NEW_END_SECTORS=$(( (FS_BYTES + SLACK) / 512 ))
parted -s "${LOOP}" unit s resizepart 2 "${NEW_END_SECTORS}"
partprobe "${LOOP}" || true
END_SECTOR="$(parted -s "${LOOP}" unit s print | awk '$1 == 2 {print $3}' | tr -d 's')"
TOTAL_BYTES=$(( (END_SECTOR + 1) * 512 ))
losetup -d "${LOOP}"
truncate -s "${TOTAL_BYTES}" "${RAW_IMG}"

log "Compressing (this also takes a while)"
xz -T0 -9 -c "${RAW_IMG}" > "${IMAGE_NAME}.xz"
sha256sum "${IMAGE_NAME}.xz" > "${IMAGE_NAME}.xz.sha256"
rm -f "${RAW_IMG}"

log "Done"
echo "Image: ${WORKDIR}/${IMAGE_NAME}.xz"
cat "${WORKDIR}/${IMAGE_NAME}.xz.sha256"
