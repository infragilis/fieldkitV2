#!/usr/bin/env bash
# Golden image build (runs on an x86_64 build host, e.g. the fieldkit-server VM).
#
# Builds the flash-and-go Fieldkit SD image served on the server /get page.
# The default base is Raspberry Pi OS Lite 64-bit (Trixie), which supports
# Pi 3, Pi 4, and Pi 5. The image is chrooted with qemu-user-static, the
# Fieldkit installer + sysprep run, then the result is compressed for /get.
#
# Requires: qemu-user-static, parted, e2fsprogs, xz-utils, curl, sudo, gdisk,
#           sfdisk (util-linux), lsinitramfs (initramfs-tools).
# See docs/golden-image-build.md.
#
# BASE_PROFILE=rpi-os (default) | debian-cloud (legacy reference only)

set -euo pipefail

WORKDIR=${WORKDIR:-/opt/fieldkit-golden}
BASE_PROFILE=${BASE_PROFILE:-rpi-os}
IMAGE_NAME=${IMAGE_NAME:-fieldkit-v0.2.4.img}
REPO_CHECKOUT=${REPO_CHECKOUT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}
LOCAL_CHECKOUT=${LOCAL_CHECKOUT:-/opt/fieldkit-golden-builder}
BASE_SIZE=${BASE_SIZE:-8G}

RPIOS_IMAGE=2026-09-15-raspios-trixie-arm64-lite.img.xz
RPIOS_URL=${RPIOS_URL:-https://downloads.raspberrypi.com/raspios_lite_arm64/images/raspios_lite_arm64-2026-09-15/${RPIOS_IMAGE}}
RPIOS_SHA256=${RPIOS_SHA256:-cdf4f3bfac35ae947b46e4e767f935453810549779ac3290e05a6754aee627e5}

DEBIAN_URL=${DEBIAN_URL:-https://cloud.debian.org/images/cloud/trixie/daily/latest/debian-13-raspi-arm64-daily.tar.xz}

log() {
  printf '\n==> %s\n' "$*"
}

die() {
  printf 'ERROR: %s\n' "$*" >&2
  exit 1
}

if [[ ${EUID} -ne 0 ]]; then
  echo "Run as root (sudo bash scripts/golden-image-build.sh)"
  exit 1
fi

LOOP=""
MNT=""
RAW_IMG=""
RESOLV_BAK="${WORKDIR}/resolv.conf.base"
cleanup() {
  local rc=$? bad=0 d loop_out=""
  set +e
  if [[ -n "${MNT}" ]] && mountpoint -q "${MNT}"; then
    restore_resolv
  fi
  for d in "${MNT}/dev/pts" "${MNT}/dev" "${MNT}/sys" "${MNT}/proc" "${MNT}/boot/firmware" "${MNT}"; do
    [[ -n "${MNT}" ]] || continue
    if mountpoint -q "${d}"; then
      umount "${d}" 2>/dev/null || umount -l "${d}" 2>/dev/null || \
        { printf 'WARNING: could not unmount %s\n' "${d}" >&2; bad=1; }
    fi
  done
  if [[ -n "${LOOP}" ]]; then
    losetup -d "${LOOP}" 2>/dev/null || { printf 'WARNING: could not detach %s\n' "${LOOP}" >&2; bad=1; }
  fi
  # Verify the postconditions rather than silently claiming success.
  for d in "${MNT}/dev/pts" "${MNT}/dev" "${MNT}/sys" "${MNT}/proc" "${MNT}/boot/firmware" "${MNT}"; do
    [[ -n "${MNT}" ]] || continue
    mountpoint -q "${d}" && { printf 'WARNING: %s still mounted at exit\n' "${d}" >&2; bad=1; }
  done
  if [[ -n "${LOOP}" ]]; then
    loop_out="$(losetup -j "${RAW_IMG}" 2>/dev/null)" || { printf 'WARNING: losetup query failed\n' >&2; bad=1; }
    if [[ -n "${loop_out}" ]] && grep -q "${LOOP}" <<<"${loop_out}"; then
      printf 'WARNING: loop %s still attached at exit\n' "${LOOP}" >&2
      bad=1
    fi
  fi
  [[ ${rc} -eq 0 && ${bad} -ne 0 ]] && rc=1
  exit "${rc}"
}
trap cleanup EXIT

assert_layout() {
  local img=$1
  local label_out
  label_out="$(sfdisk -d "${img}")" || die "sfdisk -d failed on ${img}"
  grep -q '^label: dos' <<<"${label_out}" || die "${img} is not an MBR (dos) disk"
  # Trim whitespace: util-linux 2.39 pads `--part-type` output with a leading space.
  [[ "$(sfdisk --disk-id "${img}" | tr -d '[:space:]')" == "0x4d8fd085" ]] || die "${img} has an unexpected disk id"
  [[ "$(sfdisk --part-type "${img}" 1 | tr -d '[:space:]')" == "c" ]] || die "${img} p1 is not FAT (type c)"
  [[ "$(sfdisk --part-type "${img}" 2 | tr -d '[:space:]')" == "83" ]] || die "${img} p2 is not Linux (type 83)"
  mapfile -t _parts < <(grep -E ' : start=' <<<"${label_out}")
  [[ "${#_parts[@]}" -eq 2 ]] || die "${img} does not have exactly 2 partitions"
  grep -q 'start= *1064960,' <<<"${_parts[1]}" || die "${img} p2 does not start at the expected sector"
}

assert_unmounted() {
  local d
  for d in "${MNT}/dev/pts" "${MNT}/dev" "${MNT}/sys" "${MNT}/proc" "${MNT}/boot/firmware" "${MNT}"; do
    if mountpoint -q "${d}"; then
      die "${d} is still mounted"
    fi
  done
}

assert_loop_detached() {
  local loop_out rc=0
  loop_out="$(losetup -j "${RAW_IMG}" 2>/dev/null)" || rc=$?
  [[ ${rc} -eq 0 ]] || die "losetup -j failed for ${RAW_IMG}"
  [[ -z "${loop_out}" ]] || die "a loop device is still attached to ${RAW_IMG}"
}

verify_sha256() {
  local file=$1 expected=$2 actual
  actual="$(sha256sum "${file}" | awk '{print $1}')"
  [[ "${actual}" == "${expected}" ]] || die "sha256 mismatch for ${file}: got ${actual}, expected ${expected}"
}

case "${BASE_PROFILE}" in
  rpi-os)
    ROOT_SUFFIX=p2
    BOOT_SUFFIX=p1
    ;;
  debian-cloud)
    ROOT_SUFFIX=p1
    BOOT_SUFFIX=p15
    ;;
  *)
    die "unknown BASE_PROFILE '${BASE_PROFILE}'"
    ;;
esac

mkdir -p "${WORKDIR}"
cd "${WORKDIR}"
rm -f "${RESOLV_BAK}"

# ---------------------------------------------------------------------------
# 1. Base image
# ---------------------------------------------------------------------------
if [[ "${BASE_PROFILE}" == "rpi-os" ]]; then
  log "Downloading Raspberry Pi OS Lite base (pinned ${RPIOS_IMAGE})"
  if [[ ! -f base.img.xz ]]; then
    curl -fSL --retry 3 -o base.img.xz "${RPIOS_URL}"
  fi
  verify_sha256 base.img.xz "${RPIOS_SHA256}"
  xz -t base.img.xz
  log "Decompressing base image"
  xz -dc base.img.xz > base.img
  RAW_IMG="${WORKDIR}/base.img"
else
  log "Downloading Debian cloud base"
  if [[ ! -f base.tar.xz ]]; then
    curl -fSL --retry 3 -o base.tar.xz "${DEBIAN_URL}"
  fi
  mkdir -p extracted
  tar -xf base.tar.xz -C extracted
  RAW_IMG="$(find extracted -maxdepth 1 \( -name '*.img' -o -name '*.raw' \) | head -1)"
  [[ -n "${RAW_IMG}" ]] || die "No raw image found inside the archive"
fi

log "Growing working image to ${BASE_SIZE}"
truncate -s "${BASE_SIZE}" "${RAW_IMG}"

log "Attaching image"
LOOP="$(losetup -Pf --show "${RAW_IMG}")"
echo "loop device: ${LOOP}"

if [[ "${BASE_PROFILE}" == "rpi-os" ]]; then
  # Assert the expected MBR layout before touching it.
  assert_layout "${RAW_IMG}"
fi

log "Growing root partition (profile=${BASE_PROFILE}, root=${ROOT_SUFFIX})"
parted -s "${LOOP}" unit s resizepart "${ROOT_SUFFIX#p}" 100%
# Reattach the loop so the kernel re-reads the new partition table
# deterministically instead of relying on partprobe, which can fail on loop
# devices and leave the old partition size in place.
losetup -d "${LOOP}"
LOOP="$(losetup -Pf --show "${RAW_IMG}")"
ROOT_PART="${LOOP}${ROOT_SUFFIX}"
BOOT_PART="${LOOP}${BOOT_SUFFIX}"
e2fsck -fy "${ROOT_PART}" || { rc=$?; [[ ${rc} -le 1 ]] || die "e2fsck failed (rc=${rc})"; }
resize2fs "${ROOT_PART}"

mount_image() {
  log "Mounting rootfs"
  mkdir -p "${WORKDIR}/mnt"
  MNT="${WORKDIR}/mnt"
  mount "${ROOT_PART}" "${MNT}"
  # The boot filesystem must be mounted: config/cmdline edits and initramfs
  # regeneration must land on the FAT partition, not the root filesystem.
  mount "${BOOT_PART}" "${MNT}/boot/firmware"
  # Do not ship the builder's resolver configuration. Save the base file once
  # per run; the EXIT trap restores it if the run aborts while mounted.
  if [[ ! -f "${RESOLV_BAK}" ]]; then
    cp -a "${MNT}/etc/resolv.conf" "${RESOLV_BAK}"
  fi
  install -m 0644 /etc/resolv.conf "${MNT}/etc/resolv.conf"
  cp /usr/bin/qemu-aarch64-static "${MNT}/usr/bin/" 2>/dev/null || true
}

unmount_image() {
  log "Unmounting"
  for d in "${MNT}/dev/pts" "${MNT}/dev" "${MNT}/sys" "${MNT}/proc" "${MNT}/boot/firmware" "${MNT}"; do
    mountpoint -q "${d}" && umount "${d}" || true
  done
}

mount_chroot_fs() {
  mount -t proc proc "${MNT}/proc"
  mount -t sysfs sysfs "${MNT}/sys"
  mount -t devtmpfs devtmpfs "${MNT}/dev" || mount --bind /dev "${MNT}/dev"
  mount -t devpts devpts "${MNT}/dev/pts" || true
}

restore_resolv() {
  if [[ -f "${RESOLV_BAK}" ]] && mountpoint -q "${MNT}"; then
    rm -f "${MNT}/etc/resolv.conf"
    cp -a "${RESOLV_BAK}" "${MNT}/etc/resolv.conf"
  fi
}

mount_image
mount_chroot_fs

log "Cloning the Fieldkit release into the image"
rm -rf "${MNT}/opt/fieldkit"
if [[ -d "${LOCAL_CHECKOUT}/.git" ]]; then
  git clone --branch "${FIELDKIT_BRANCH:-main}" "file://${LOCAL_CHECKOUT}" "${MNT}/opt/fieldkit"
else
  git clone --branch "${FIELDKIT_BRANCH:-main}" \
    "${FIELDKIT_REPO_URL:-https://github.com/infragilis/fieldkitV2.git}" "${MNT}/opt/fieldkit"
fi
install -m 0755 "${LOCAL_CHECKOUT}/scripts/golden-chroot-install.sh" \
  "${MNT}/opt/fieldkit/scripts/golden-chroot-install.sh"

log "Running installer inside the chroot (this is the slow part)"
GOLDEN_MODE=install BASE_PROFILE="${BASE_PROFILE}" \
  chroot "${MNT}" /bin/bash /opt/fieldkit/scripts/golden-chroot-install.sh

# Detach cleanly before snapshotting so installed.img is not a torn copy of a
# mounted filesystem. Restore the base resolver first so the snapshot does not
# carry the builder's resolv.conf.
restore_resolv
rm -f "${MNT}/usr/bin/qemu-aarch64-static"
unmount_image
losetup -d "${LOOP}"
LOOP=""

log "Saving pre-sysprep snapshot for future refresh builds"
cp -a "${RAW_IMG}" installed.img
printf '%s\n' "${BASE_PROFILE}" > installed.img.profile
if [[ "${BASE_PROFILE}" == "rpi-os" ]]; then
  printf '%s\n' "${RPIOS_SHA256}" > installed.img.base-sha256
elif [[ -f base.tar.xz ]]; then
  sha256sum base.tar.xz | awk '{print $1}' > installed.img.base-sha256
fi

log "Re-attaching for sysprep"
LOOP="$(losetup -Pf --show "${RAW_IMG}")"
ROOT_PART="${LOOP}${ROOT_SUFFIX}"
BOOT_PART="${LOOP}${BOOT_SUFFIX}"
mount_image
mount_chroot_fs

log "Sysprepping the image"
GOLDEN_MODE=sysprep BASE_PROFILE="${BASE_PROFILE}" \
  chroot "${MNT}" /bin/bash /opt/fieldkit/scripts/golden-chroot-install.sh

restore_resolv

log "Running strict offline audit"
GOLDEN_MNT="${MNT}" GOLDEN_IMG="${RAW_IMG}" GOLDEN_LOOP="${LOOP}" \
  BASE_PROFILE="${BASE_PROFILE}" \
  bash "${LOCAL_CHECKOUT}/scripts/golden-image-audit.sh"

# The builder-only qemu must not ship in the image.
rm -f "${MNT}/usr/bin/qemu-aarch64-static"
unmount_image
assert_unmounted

# Zero the free blocks so the fixed-size image compresses well. zerofree needs
# the filesystem unmounted; an I/O failure is fatal.
log "Zeroing free space (zerofree)"
command -v zerofree >/dev/null 2>&1 || die "zerofree is required"
zerofree -v "${ROOT_PART}" || die "zerofree failed"

if [[ "${BASE_PROFILE}" == "debian-cloud" ]]; then
  log "Shrinking filesystem and GPT (debian-cloud)"
  e2fsck -fy "${ROOT_PART}" || { rc=$?; [[ ${rc} -le 1 ]] || die "e2fsck failed (rc=${rc})"; }
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
  LOOP=""
  truncate -s "$(( (NEW_END_SECTORS + 34) * 512 ))" "${RAW_IMG}"
  sgdisk -Z -o \
    -n "15:${BOOT_START}:${BOOT_END}" -t "15:${BOOT_TYPE}" -u "15:${BOOT_UNIQ}" \
    -n "1:${PART_START}:${NEW_END_SECTORS}" -t "1:${TYPE_GUID}" -u "1:${UNIQ_GUID}" \
    -e "${RAW_IMG}"
else
  log "Keeping the fixed ${BASE_SIZE} MBR image (native first-boot resize grows p2)"
  losetup -d "${LOOP}"
  LOOP=""
fi
assert_loop_detached

log "Compressing (this also takes a while)"
tmp_xz="${IMAGE_NAME}.xz.tmp"
tmp_sha="${IMAGE_NAME}.xz.sha256.tmp"
xz -T0 -6 -c "${RAW_IMG}" > "${tmp_xz}"
# The sidecar must carry the final basename so `sha256sum -c` works after the
# temporary file is renamed.
hash="$(sha256sum "${tmp_xz}" | awk '{print $1}')"
printf '%s  %s\n' "${hash}" "${IMAGE_NAME}.xz" > "${tmp_sha}"
mv -f "${tmp_xz}" "${IMAGE_NAME}.xz"
mv -f "${tmp_sha}" "${IMAGE_NAME}.xz.sha256"
if [[ "${RAW_IMG}" == "${WORKDIR}/base.img" || "${RAW_IMG}" == "${WORKDIR}/extracted/"* ]]; then
  rm -f "${RAW_IMG}"
fi
rm -f "${RESOLV_BAK}"

log "Done"
echo "Image: ${WORKDIR}/${IMAGE_NAME}.xz"
cat "${WORKDIR}/${IMAGE_NAME}.xz.sha256"
