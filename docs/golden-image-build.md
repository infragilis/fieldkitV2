# Golden Image Build

Builds the flash-and-go Fieldkit SD image served on the server `/get` page.
The build runs on an x86_64 host (the `fieldkit-server` VM works well) — no
Raspberry Pi is needed. The result is a shrunk, compressed
`fieldkit-vX.Y.Z.img.xz` ready for Raspberry Pi Imager.

## Requirements (build host)

- x86_64 Debian/Ubuntu with ~10 GB free disk, root access
- `qemu-user-static parted e2fsprogs pv xz-utils curl git`

## One-shot build

```bash
sudo apt-get install -y qemu-user-static parted e2fsprogs pv xz-utils curl git
sudo bash scripts/golden-image-build.sh
```

The script downloads the official Debian 13 (trixie) arm64 Raspberry Pi image
(`https://cloud.debian.org/images/cloud/trixie/daily/latest/debian-13-raspi-arm64-daily.tar.xz`),
grows it, chroots in with qemu, runs the full Fieldkit installer with
`START_SERVICES=0` (a systemctl shim enables the units without starting them),
syspreps (password SSH, host keys regenerated on first boot, cloud-init
disabled, logs/runtime cleared), shrinks the filesystem and partition, and
compresses the image with `xz -T0 -9`.

Bump `IMAGE_NAME` in the script when the Fieldkit version changes; the image
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
for name in ("fieldkit-v0.1.6.img.xz", "fieldkit-v0.1.6.img.xz.sha256"):
    c.upload_file(f"/opt/fieldkit-golden/{name}", "fieldkit", f"fieldkit/releases/{name}")
PY
```

The `releases/` prefix is public-read (bucket policy), so the `/get` page links
to `https://fieldkit.nyc3.digitaloceanspaces.com/fieldkit/releases/...` and
flips from "not published yet" to the download state automatically (it checks
the object and shows the published SHA-256).

## User steps (shown on /get)

1. Download the image.
2. Flash with Raspberry Pi Imager to a 64 GB+ microSD card.
3. Boot the Pi, wait ~2 minutes.
4. Connect via wired Ethernet (`http://fieldkit.local` / DHCP address) or the
   `fieldkit` AP (`http://10.42.0.1/`), log in `service`/`service`.
5. Change the password, then paste the device token on Server Sync and pick a
   sync window.

## Notes

- The Debian cloud image covers Pi 3/4/5 (arm64); Pi 5 requires Debian 14, so
  the trixie image targets Pi 3 and Pi 4.
- Rebuild per release; the image is version-stamped by filename.
- Pi 3 boot media: the image uses the standard `/boot/firmware` layout and the
  official kernel, matching the reference appliance.
