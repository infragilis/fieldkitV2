# Golden Image Build

Builds the flash-and-go Fieldkit SD image served on the server `/get` page.
The build runs on an x86_64 host (the `fieldkit-server` VM works well) — no
Raspberry Pi is needed. The result is a shrunk, compressed
`fieldkit-vX.Y.Z.img.xz` ready for Raspberry Pi Imager.

## Requirements (build host)

- x86_64 Debian/Ubuntu with ~10 GB free disk, root access
- `qemu-user-static parted e2fsprogs pv xz-utils curl git rsync gdisk`

## One-shot build

```bash
sudo apt-get install -y qemu-user-static parted e2fsprogs pv xz-utils curl git rsync gdisk
sudo bash scripts/golden-image-build.sh
```

The script downloads the official Debian 13 (trixie) arm64 Raspberry Pi image
(`https://cloud.debian.org/images/cloud/trixie/daily/latest/debian-13-raspi-arm64-daily.tar.xz`),
grows it to 8 GiB, chroots in with qemu, runs the full Fieldkit installer with
`START_SERVICES=0` (a systemctl/hostnamectl shim enables the units without
starting them), saves a pre-sysprep snapshot (`installed.img`), then syspreps
(password SSH, host keys regenerated on first boot, cloud-init disabled,
logs/runtime cleared), shrinks the filesystem and partition, and compresses
the image with `xz -T0 -6`. The first build takes roughly 30-60 minutes
because the OS/package install runs under arm64 emulation.

Shrink mechanics (shared with the refresh script): `resize2fs -M` shrinks the
root filesystem to its minimum, then the GPT is rebuilt with `sgdisk -Z -o`
instead of `parted resizepart` (script-mode parted refuses to shrink; the
half-resized headers a failed run leaves behind would also block it). Both
partitions are recreated with their original geometry, type GUIDs, and unique
GUIDs (PARTUUIDs), because `/etc/fstab` mounts root and `/boot/firmware` by
`PARTUUID=`. The stock hybrid MBR (FAT boot entry + 0xEE entries) is left
intact. Output: a ~3.2 GiB image that compresses to roughly 650 MB.

## Fast refresh (small changes)

After the first build, keep `installed.img`. For bug fixes and small changes,
skip the emulated install entirely:

```bash
sudo bash scripts/golden-refresh.sh
```

The refresh copies the snapshot, rsyncs the changed repository files into it,
re-runs `pip install -e` and sysprep, then shrinks and compresses. Typically
5-15 minutes instead of an hour. For everyday iteration on a live kit, prefer
copy-deploy (`docs/update-and-reload.md`) — seconds, no image involved. Only
refresh the image when new kits need to ship with the changes.

Bump `IMAGE_NAME` in the scripts when the Fieldkit version changes; the image
is built from `main` on GitHub, so push the release first.

## Publish

Upload to DigitalOcean Spaces (`fieldkit/releases/`) from the server VM:

```bash
cd /opt/fieldkit-server && set -a && . /etc/fieldkit-server/.env && set +a
.venv/bin/python - <<'PY'
from server import s3
from server.config import Settings
s = Settings.from_env()
c = s3._client(s, s.s3_endpoint)
for name in ("fieldkit-v0.2.1.img.xz", "fieldkit-v0.2.1.img.xz.sha256"):
    c.upload_file(f"/opt/fieldkit-golden/{name}", "fieldkit", f"fieldkit/releases/{name}")
PY
```

The upload key is a limited-access Spaces key, which cannot apply bucket
policies, so there is no public prefix: `/get` and the update-latest device
route generate fresh **presigned URLs** on each request (24h for the image,
6h for update bundles) and show the published SHA-256.

The server's `/get` looks for a fixed object name — `GOLDEN_IMAGE_NAME` in
`server/web.py`. Bump it to the new filename **together with** the image, or
`/get` will keep pointing at the previous object.

## User steps (shown on /get)

1. Download the image.
2. Flash with Raspberry Pi Imager to a 64 GB+ microSD card.
3. Boot the Pi, wait ~2 minutes.
4. Connect via wired Ethernet (`http://fieldkit.local` / DHCP address) or the
   `fieldkit` AP (`http://10.42.0.1/`), log in `service`/`service`.
5. Change the password, then paste the device token on Server Sync and pick a
   sync window.

## Base image and Pi 5 (IMPORTANT)

The current base is the **Debian 13 (trixie) "raspi" arm64 cloud image**, which
supports **Pi 3 and Pi 4 only**. The reference/field kit is a **Pi 5**
(`BCM2712`), so these images cannot be used on it (no network). **A build must
support Pi 3, Pi 4, and Pi 5.**

Chosen fix: rebase on **Raspberry Pi OS Lite 64-bit (Trixie)** (supports Pi
3B/3B+/3A+, Pi 4, Pi 5). Required changes (see `SESSION_START.md` for detail):

1. Download a direct `*.img.xz` (not a tar) and `xz -dc` it; add a base profile.
2. Partition layout is **p1 = FAT boot, p2 = ext4 root** (Debian was root p1 /
   boot p15); grow p2.
3. Do **not** apply the Debian-specific `sgdisk -Z -o` p1/p15 shrink to the RPi
   OS table initially — ship the 8-GiB working image; add a partition-aware
   shrink only after Pi 3/4/5 boot is verified.
4. Network: RPi OS uses `dhcpcd`; install/enable **NetworkManager** (Fieldkit
   needs it), disable `dhcpcd`, keep the NM wired DHCP keyfile, mask distro
   `hostapd`/`dnsmasq`.
5. Re-verify `sshd-keygen`, `getty@tty1`, `console=tty1` +
   `console=serial0,115200`, `enable_uart=1`, and the `enforce_image_state`
   audit; then **boot-test on Pi 3, Pi 4, and Pi 5 before publishing.**

## Notes

- The Debian cloud image covers Pi 3/4/5 (arm64); Pi 5 requires Debian 14, so
  the trixie image targets Pi 3 and Pi 4.
- Rebuild per release; the image is version-stamped by filename.
- Pi 3 boot media: the image uses the standard `/boot/firmware` layout and the
  official kernel, matching the reference appliance.
- First build on the VM succeeded 2026-09-12 (fixes: partition-number bug in
  the old `parted resizepart 2`, start-offset arithmetic, script-mode parted
  shrink refusal, stale GPT headers from a killed run).
- The image ships with the root partition shrunk to ~2.75 GiB and the root
  filesystem at its minimum (~2.5 GiB). `/etc/fstab` already carries
  `x-systemd.growfs`, which grows the filesystem to the partition at mount;
  the golden builder additionally installs `fieldkit-growroot.service`, which
  on first boot grows the root **partition** to fill the boot media
  (32/64/128 GB) and then the filesystem, then disarms itself by removing
  `/etc/fieldkit-growroot`. It uses `growpart` + `sgdisk` (installed by the
  golden installer) and is a no-op on already-full media.
