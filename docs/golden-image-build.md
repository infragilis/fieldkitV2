# Golden Image Build

Builds the flash-and-go Fieldkit SD image served on the server `/get` page.
The build runs on an x86_64 host (the `fieldkit-server` VM works well) — no
Raspberry Pi is needed. The result is a compressed `fieldkit-vX.Y.Z.img.xz`
ready for Raspberry Pi Imager.

The production base is **Raspberry Pi OS Lite 64-bit (Trixie)**, which supports
**Pi 3B/3B+/3A+, Pi 4, and Pi 5**. One image boots all three.

## Requirements (build host)

- x86_64 Debian/Ubuntu with ~20 GB free disk (the working image is 8 GiB), root
  access
- `qemu-user-static` (registered binfmt), `parted`, `e2fsprogs`, `xz-utils`,
  `curl`, `rsync`, `sudo`, `util-linux` (`sfdisk`, `mountpoint`),
  `initramfs-tools` (`lsinitramfs`), `zerofree`
- `gdisk` is only needed for the legacy `debian-cloud` profile

## One-shot build

```bash
sudo apt-get install -y qemu-user-static parted e2fsprogs xz-utils curl rsync \
  util-linux initramfs-tools zerofree gdisk
sudo bash scripts/golden-image-build.sh
```

`update-initramfs -u -k all` must succeed inside the chroot (it is fatal), and
free space is zeroed with `zerofree` on the unmounted filesystem so the
fixed-size image compresses well. The `.xz` and its checksum are written to
temporary names and renamed only after success.

`BASE_PROFILE=rpi-os` is the default. The script:

1. Downloads the pinned Raspberry Pi OS Lite image (immutable date-stamped URL),
   verifies its SHA-256, `xz -t`, and decompresses it to a raw `.img`.
2. Grows the working image to 8 GiB and expands the ext4 root (`p2`) so the
   install has headroom. The base layout is **MBR (msdos)**: `p1` = FAT boot,
   `p2` = ext4 root (PARTUUIDs `4d8fd085-01` / `-02`). The script asserts this
   layout before touching it.
3. Mounts root + boot, chroots in with qemu, and runs the Fieldkit installer
   (`GOLDEN_MODE=install`) with `START_SERVICES=0`.
4. Detaches the loop and saves a clean `installed.img` snapshot (plus
   `installed.img.profile` / `installed.img.base-sha256` sidecars), then
   re-attaches for sysprep (`GOLDEN_MODE=sysprep`).
5. Zero-fills free space, runs the **strict offline audit**
   (`scripts/golden-image-audit.sh`), and aborts on any mismatch.
6. Keeps the fixed 8 GiB MBR image (no shrink — see below) and compresses it
   with `xz -T0 -6`. The output is roughly 0.7–1.0 GB because the free space is
   zeroed.

`debian-cloud` remains available as an explicit non-default `BASE_PROFILE` for
reference; it keeps the old GPT root `p1` / boot `p15` layout and the `sgdisk`
shrink path.

## Fast refresh (small changes)

After the first build, keep `installed.img`. For bug fixes and small changes,
skip the emulated install entirely:

```bash
sudo bash scripts/golden-refresh.sh
```

The refresh refuses to run unless `installed.img.profile` matches
`BASE_PROFILE` and (for `rpi-os`) the saved base SHA matches, so a stale Debian
snapshot cannot be silently refreshed as Raspberry Pi OS. It rsyncs the changed
repository files, re-runs `pip install -e` and sysprep, runs the same strict
audit, then compresses. Typically 5–15 minutes. For everyday iteration on a live
kit, prefer copy-deploy (`docs/update-and-reload.md`); only refresh the image
when new kits need to ship with the changes.

Bump `IMAGE_NAME` in the scripts when the Fieldkit version changes.

## First boot (what the image relies on)

- **Root grow**: Raspberry Pi OS ships `resize` in
  `/boot/firmware/cmdline.txt`. The initramfs `resize_early` hook grows `p2` to
  the card, then `rpi-resize.service` + `systemd-growfs-root.service` grow the
  filesystem, and `rpi-resize.service` disables itself. The image therefore
  ships fixed-size and grows to any card on first boot. Fieldkit's own
  `fieldkit-growroot` is **not** installed on this profile.
- **First boot marker**: `/etc/machine-id` ships as `uninitialized`, so
  systemd's `ConditionFirstBoot=yes` units run exactly once. Sysprep forces this
  value as its final identity step, and `regenerate_ssh_host_keys.service`
  creates unique host keys before SSH starts.
- **Network**: NetworkManager is the only manager (networkd and the
  wait-online services are masked). A `fieldkit-wired` DHCP keyfile binds
  `eth0`; the kernel interface names (`eth0`/`wlan0`) are preserved by the
  Raspberry Pi OS link policy. The field Wi-Fi AP is brought up best-effort by
  `fieldkit-startup-network.timer` (5 s after boot, non-blocking, retried on
  failure) in `apply_wifi_mode.sh`; it can never hold up the console, SSH,
  nginx, or the web UI. `hostapd`/`dnsmasq` (distro) are masked; Fieldkit uses
  its own `fieldkit-ap-*` units, which are pinned disabled so first-boot
  systemd presets cannot start them.
- **Console**: `console=serial0,115200 console=tty1` and `enable_uart=1`
  (appended under `[all]`).
- **Cloud-init / interactive first-boot wizards**: cloud-init is disabled
  (`.disabled` marker + masks); the user-rename dialog (`userconfig`), the
  distro ssh-switch helper, and **`systemd-firstboot.service`** are masked. The
  `machine-id` stays `uninitialized` on purpose (to trigger the native resize +
  SSH keygen), which would otherwise run the interactive `systemd-firstboot`
  wizard (locale/keymap/timezone/root password) on the console — it must never
  prompt on a field kit. The `service` account is created by the installer.
- **Presets**: `deploy/systemd/00-fieldkit.preset` sorts first and ends with
  `ignore *`, so the vendor preset (`90-systemd.preset`) cannot re-enable
  unwanted units on first boot.

## Strict offline audit

`scripts/golden-image-audit.sh` fails the build unless, from the mounted image:
required units are enabled; unwanted units are disabled/masked; the MBR disk id
and both PARTUUIDs are unchanged; `cmdline.txt` still has
`console=serial0,115200`, `console=tty1`, the root PARTUUID, `rootwait`, and
`resize`; `enable_uart=1` is under `[all]`; both initramfs images contain
`resize_early`/`parted`/`lsblk`; `/etc/machine-id` is `uninitialized`;
cloud-init is disabled; the wired DHCP keyfile is present and `0600`; the seeded
`settings.json` defaults to AP; and `nginx -t` / `sshd -t` pass.

## Publish

Upload to DigitalOcean Spaces (`fieldkit/releases/`) from the server VM:

```bash
cd /opt/fieldkit-server && set -a && . /etc/fieldkit-server/.env && set +a
.venv/bin/python - <<'PY'
from server import s3
from server.config import Settings
s = Settings.from_env()
c = s3._client(s, s.s3_endpoint)
for name in ("fieldkit-v0.2.2.img.xz", "fieldkit-v0.2.2.img.xz.sha256"):
    c.upload_file(f"/opt/fieldkit-golden/{name}", "fieldkit", f"fieldkit/releases/{name}")
PY
```

The upload key is a limited-access Spaces key, which cannot apply bucket
policies, so there is no public prefix: `/get` and the update-latest device
route generate fresh **presigned URLs** on each request (24 h for the image,
6 h for update bundles) and show the published SHA-256.

The server's `/get` looks for a fixed object name — `GOLDEN_IMAGE_NAME` in
`server/web.py`. Bump it to the new filename **together with** the image, or
`/get` will keep pointing at the previous object.

## Publish gate (hard requirement)

A build is not publishable until a **fresh-flash** card has been booted on a
real **Pi 3, Pi 4, and Pi 5**, each twice (first boot + one cold reboot), per
`docs/golden-image-checklist.md`. The offline audit proves static coherence
only; AP/regulatory behavior, HDMI/keyboard, and grow-on-real-card remain
hardware-only checks.

## User steps (shown on /get)

1. Download the image.
2. Flash with Raspberry Pi Imager to a 64 GB+ microSD card (use a fresh card).
3. Boot the Pi, wait ~2 minutes (first boot grows the root partition).
4. Connect via wired Ethernet (`http://fieldkit.local` / DHCP address) or the
   `fieldkit` AP (`http://10.42.0.1/`), log in `service`/`service`.
5. Change the password, then paste the device token on Server Sync and pick a
   sync window.

## Notes

- Rebuild per release; the image is version-stamped by filename.
- The image is built from `main` on GitHub, so push the release first.
- Never publish a partial/aborted image.
- Pi 3 boot media: the image uses the standard `/boot/firmware` layout and the
  official Raspberry Pi kernel (`kernel8.img` for Pi 3/4, `kernel_2712.img` for
  Pi 5).
- An MBR-safe shrink can be added after the Pi 3/4/5 matrix passes; until then
  the fixed-size image is intentional. See the team analysis in
  `/tmp/opencode/fieldkit-rpi-rebase-last.txt`.
