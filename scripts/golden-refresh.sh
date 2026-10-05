#!/usr/bin/env bash
# Fast golden-image refresh: rebuild the distributable image from the saved
# pre-sysprep snapshot, applying only the changed repository files.
#
# Skips the slow emulated OS/package install entirely. Run after pushing code
# changes to main when a fresh flash-and-go image is needed quickly.
#
# Requires installed.img + installed.img.profile (saved by
# scripts/golden-image-build.sh), a local checkout to copy from, and the same
# build dependencies as the full build (including zerofree).
# See docs/golden-image-build.md.
#
# BASE_PROFILE=rpi-os (default) | debian-cloud

set -euo pipefail

WORKDIR=${WORKDIR:-/opt/fieldkit-golden}
BASE_PROFILE=${BASE_PROFILE:-rpi-os}
IMAGE_NAME=${IMAGE_NAME:-fieldkit-v0.2.4.img}
LOCAL_CHECKOUT=${LOCAL_CHECKOUT:-/opt/fieldkit-golden-builder}
FIELDKIT_BRANCH=${FIELDKIT_BRANCH:-main}

RPIOS_SHA256=${RPIOS_SHA256:-cdf4f3bfac35ae947b46e4e767f935453810549779ac3290e05a6754aee627e5}

log() {
  printf '\n==> %s\n' "$*"
}

die() {
  printf 'ERROR: %s\n' "$*" >&2
  exit 1
}

if [[ ${EUID} -ne 0 ]]; then
  echo "Run as root (sudo bash scripts/golden-refresh.sh)"
  exit 1
fi

cd "${WORKDIR}"
[[ -f installed.img ]] || die "installed.img not found; run scripts/golden-image-build.sh once first"
[[ -f installed.img.profile ]] || die "installed.img.profile missing (old snapshot); run a full build first"
[[ "$(cat installed.img.profile)" == "${BASE_PROFILE}" ]] || \
  die "installed.img is profile '$(cat installed.img.profile)', not '${BASE_PROFILE}'"

case "${BASE_PROFILE}" in
  rpi-os)
    [[ -f installed.img.base-sha256 ]] || die "installed.img.base-sha256 missing"
    [[ "$(cat installed.img.base-sha256)" == "${RPIOS_SHA256}" ]] || \
      die "installed.img base image is stale; run a full build for the current base"
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

LOOP=""
MNT=""
RESOLV_BAK="${WORKDIR}/resolv.conf.base"

restore_resolv() {
  if [[ -f "${RESOLV_BAK}" ]] && [[ -n "${MNT}" ]] && mountpoint -q "${MNT}"; then
    rm -f "${MNT}/etc/resolv.conf"
    cp -a "${RESOLV_BAK}" "${MNT}/etc/resolv.conf"
  fi
}

cleanup() {
  local rc=$? bad=0 d loop_out=""
  set +e
  restore_resolv
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
  for d in "${MNT}/dev/pts" "${MNT}/dev" "${MNT}/sys" "${MNT}/proc" "${MNT}/boot/firmware" "${MNT}"; do
    [[ -n "${MNT}" ]] || continue
    mountpoint -q "${d}" && { printf 'WARNING: %s still mounted at exit\n' "${d}" >&2; bad=1; }
  done
  if [[ -n "${LOOP}" ]]; then
    loop_out="$(losetup -j "${WORKDIR}/refresh.img" 2>/dev/null)" || { printf 'WARNING: losetup query failed\n' >&2; bad=1; }
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

log "Copying snapshot"
cp -a installed.img refresh.img
rm -f "${RESOLV_BAK}"

if [[ "${BASE_PROFILE}" == "rpi-os" ]]; then
  assert_layout refresh.img
fi

log "Attaching image"
LOOP="$(losetup -Pf --show refresh.img)"
ROOT_PART="${LOOP}${ROOT_SUFFIX}"
BOOT_PART="${LOOP}${BOOT_SUFFIX}"

e2fsck -fy "${ROOT_PART}" || { rc=$?; [[ ${rc} -le 1 ]] || die "e2fsck failed (rc=${rc})"; }

MNT="${WORKDIR}/mnt"
mkdir -p "${MNT}"
mount "${ROOT_PART}" "${MNT}"
mount "${BOOT_PART}" "${MNT}/boot/firmware" || die "failed to mount boot partition"
cp -a "${MNT}/etc/resolv.conf" "${RESOLV_BAK}"
install -m 0644 /etc/resolv.conf "${MNT}/etc/resolv.conf"
cp /usr/bin/qemu-aarch64-static "${MNT}/usr/bin/" 2>/dev/null || true

mount -t proc proc "${MNT}/proc"
mount -t sysfs sysfs "${MNT}/sys"
mount -t devtmpfs devtmpfs "${MNT}/dev" || mount --bind /dev "${MNT}/dev"
mount -t devpts devpts "${MNT}/dev/pts" || true

log "Updating the Fieldkit source inside the image"
if [[ -d "${LOCAL_CHECKOUT}/.git" ]]; then
  git -C "${LOCAL_CHECKOUT}" fetch origin "${FIELDKIT_BRANCH}" 2>/dev/null || true
  git -C "${LOCAL_CHECKOUT}" checkout "${FIELDKIT_BRANCH}" 2>/dev/null || true
  # --no-owner/--no-group: do not stamp the image with the builder's uid; sysprep
  # re-asserts service/root ownership afterwards.
  rsync -a --no-owner --no-group --delete --exclude .git --exclude runtime --exclude .venv \
    "${LOCAL_CHECKOUT}/" "${MNT}/opt/fieldkit/"
else
  rm -rf "${MNT}/opt/fieldkit"
  git clone --branch "${FIELDKIT_BRANCH}" \
    "${FIELDKIT_REPO_URL:-https://github.com/infragilis/fieldkitV2.git}" "${MNT}/opt/fieldkit"
fi

log "Re-running installer hooks in the chroot (idempotent; usually seconds)"
chroot "${MNT}" /bin/bash -c \
  "/opt/fieldkit/.venv/bin/pip install --quiet -e /opt/fieldkit"
GOLDEN_MODE=sysprep BASE_PROFILE="${BASE_PROFILE}" \
  chroot "${MNT}" /bin/bash /opt/fieldkit/scripts/golden-chroot-install.sh

restore_resolv

log "Running strict offline audit"
GOLDEN_MNT="${MNT}" GOLDEN_IMG="${WORKDIR}/refresh.img" GOLDEN_LOOP="${LOOP}" \
  BASE_PROFILE="${BASE_PROFILE}" \
  bash "${LOCAL_CHECKOUT}/scripts/golden-image-audit.sh"

rm -f "${MNT}/usr/bin/qemu-aarch64-static"
for d in "${MNT}/dev/pts" "${MNT}/dev" "${MNT}/sys" "${MNT}/proc" "${MNT}/boot/firmware" "${MNT}"; do
  mountpoint -q "${d}" && umount "${d}" || true
done
for d in "${MNT}/dev/pts" "${MNT}/dev" "${MNT}/sys" "${MNT}/proc" "${MNT}/boot/firmware" "${MNT}"; do
  if mountpoint -q "${d}"; then
    die "${d} is still mounted"
  fi
done

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
  LOOP=""
  truncate -s "$(( (NEW_END_SECTORS + 34) * 512 ))" refresh.img
  sgdisk -Z -o \
    -n "15:${BOOT_START}:${BOOT_END}" -t "15:${BOOT_TYPE}" -u "15:${BOOT_UNIQ}" \
    -n "1:${PART_START}:${NEW_END_SECTORS}" -t "1:${TYPE_GUID}" -u "1:${UNIQ_GUID}" \
    -e refresh.img
else
  log "Keeping the fixed-size MBR image (native first-boot resize grows p2)"
  losetup -d "${LOOP}"
  LOOP=""
fi
loop_out="$(losetup -j "${WORKDIR}/refresh.img" 2>/dev/null)" || die "losetup -j failed for refresh.img"
[[ -z "${loop_out}" ]] || die "a loop device is still attached to refresh.img"

log "Compressing"
tmp_xz="${IMAGE_NAME}.xz.tmp"
tmp_sha="${IMAGE_NAME}.xz.sha256.tmp"
xz -T0 -6 -c refresh.img > "${tmp_xz}"
# The sidecar must carry the final basename so `sha256sum -c` works after the
# temporary file is renamed.
hash="$(sha256sum "${tmp_xz}" | awk '{print $1}')"
printf '%s  %s\n' "${hash}" "${IMAGE_NAME}.xz" > "${tmp_sha}"
mv -f "${tmp_xz}" "${IMAGE_NAME}.xz"
mv -f "${tmp_sha}" "${IMAGE_NAME}.xz.sha256"
rm -f refresh.img
rm -f "${RESOLV_BAK}"

log "Done"
echo "Image: ${WORKDIR}/${IMAGE_NAME}.xz"
cat "${WORKDIR}/${IMAGE_NAME}.xz.sha256"
