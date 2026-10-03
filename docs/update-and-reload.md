# Update And Reload

This document describes how to update a deployed Fieldkit appliance and reload the running services.

The currently deployed web UI includes:

- a main dashboard at `/`
- a dedicated settings page at `/settings`
- a local shell page at `/pi-shell` backed by an in-browser terminal emulator
- popup console windows at `/serial-console/0` and `/serial-console/1`
- a files page at `/files`
- a cluster-import page at `/cluster-import` (NetApp workbook → Ansible)
- a server-sync page at `/server-sync` (download from the Fieldkit server)
- a raw export browser at `/fieldkit`
- a tools page at `/tools`

Server sync runs in the background, automatically 10 minutes after boot and
hourly thereafter, with manual **Sync now**, live progress/ETA, and persisted
last results. See [Server Sync](server-sync.md) for its timer installation,
asynchronous API, and the `data/{cisco,ontap,brocade,efos,nvidia}` directory layout.

The **Files** page browses the `data`, `personal`, `usb`, and `serial-logs`
libraries. `personal`/`usb` accept uploads; `personal`/`usb`/`serial-logs` files
can be deleted. Each `data`/`personal` file and folder also has a **Copy to USB**
action that writes it to the inserted stick (ONTAP payloads to the USB root,
everything else keeping its library folder); a green **On USB** marker shows when
a listing item is already on the stick. The shared `/fieldkit` HTTP/TFTP/FTP
export serves `data` and `personal` only — `usb` is a copy destination, not an
export source, so it is never mirrored onto the boot card.

All page HTML lives in `app/static/*.html` templates. `app/main.py` only serves files and fills in small placeholders (export listing, docs topics, console index). The topbar is rendered once by `renderTopbar()` in `app/static/app.js`; the version badge is fetched from `/openapi.json`, so bump the version only in `pyproject.toml` and `app/main.py`.

Fieldkit is served over HTTP (port 80) and HTTPS (port 443) using a self-signed
certificate at `/etc/nginx/ssl/fieldkit.{crt,key}`. There is no HTTP→HTTPS
redirect, so both endpoints work. The raw export browser remains available at
`/fieldkit/...` on the same endpoints.

## Copy-deploy method (used for this appliance)

The current appliance Pi at `/opt/fieldkit` has **no GitHub credentials**, so `git pull` against the private repo fails. The supported path is copy-based:

1. From a checkout on a dev machine, copy changed/new files into `/opt/fieldkit`, preserving `app/`, `scripts/`, and `deploy/` paths.
2. Install/refresh the sudoers file if it changed:
   ```bash
   sudo install -o root -g root -m 0440 /opt/fieldkit/deploy/sudoers/fieldkit-network /etc/sudoers.d/fieldkit-network
   sudo visudo -c
   ```
3. Fix ownership if the copy landed under the wrong UID:
   ```bash
   sudo chown -R service:service /opt/fieldkit/app /opt/fieldkit/scripts /opt/fieldkit/deploy
   ```
4. Make sure `scripts/change_password.sh` is executable (root-owned `0755`).
5. Restart the web service (below).

Verify the running files match the source checkout with `sha256sum` on the key files before relying on a deploy.

## Pull the latest repo state (git-capable installs)

On a Raspberry Pi where `/opt/fieldkit` is a git checkout with credentials:

```bash
cd /opt/fieldkit
git pull --ff-only
```

## Refresh the Python environment

```bash
cd /opt/fieldkit
sudo bash scripts/install_fieldkit.sh
```

That single installer refreshes OS package prerequisites, runtime layout, the Python virtualenv, systemd units, transfer/AP support, nginx plain HTTP mode, and the running services.

## Reload the web service

```bash
sudo systemctl restart fieldkit-web.service
sudo systemctl status fieldkit-web.service --no-pager
```

## Reload nginx

If nginx config changed:

```bash
sudo nginx -t
sudo systemctl reload nginx
```

## Refresh transfer service support

If the shared export root, FTP/TFTP config, or transfer-service policy changed:

```bash
cd /opt/fieldkit
sudo bash scripts/install_transfer_services.sh
```

That install step leaves FTP and TFTP disabled by default. Enable them from the Settings page only when needed.

## Refresh Wi-Fi AP support

If the dedicated Wi-Fi AP scripts, units, or sudoers policy changed:

```bash
cd /opt/fieldkit
sudo bash scripts/install_wifi_ap_support.sh
```

## Full update sequence

Copy-based (current appliance):

```bash
# dev machine
cd <checkout>
tar czf /tmp/fieldkit-deploy.tgz \
  app/main.py app/api/routes/*.py app/services/*.py app/static/*.html app/static/*.js \
  scripts/*.sh deploy/sudoers/fieldkit-network
# Pi
scp /tmp/fieldkit-deploy.tgz service@<pi>:/tmp/
ssh service@<pi> 'sudo tar xzf /tmp/fieldkit-deploy.tgz -C /opt/fieldkit && \
  sudo install -o root -g root -m 0440 /opt/fieldkit/deploy/sudoers/fieldkit-network /etc/sudoers.d/fieldkit-network && \
  sudo chown -R service:service /opt/fieldkit/app /opt/fieldkit/scripts /opt/fieldkit/deploy && \
  sudo visudo -c'
```

Git-based installs:

```bash
cd /opt/fieldkit
git pull --ff-only
sudo bash scripts/install_fieldkit.sh
```

If `/opt/fieldkit` is a copied tree rather than a Git checkout, copy the changed files into `/opt/fieldkit` and restart `fieldkit-web.service` instead of running `git pull`.

## Health checks

Verify locally on the Pi:

```bash
curl -fsS http://127.0.0.1/
curl -fsS http://127.0.0.1/settings
curl -fsS http://127.0.0.1/pi-shell
curl -fsS http://127.0.0.1/files
curl -fsS http://127.0.0.1/readme
curl -fsS http://127.0.0.1/tools
curl -fsS http://127.0.0.1/fieldkit/
systemctl is-active fieldkit-web.service
systemctl is-active nginx
```

## Smoke test the live appliance

Run the reusable smoke harness from the repo root when you want an end-to-end transfer check:

```bash
./scripts/smoke_test_appliance.sh
```

This uploads a temporary file to `personal` and verifies:

- HTTP API upload and download
- HTTP download from `/fieldkit/personal/...`
- SCP download from `/opt/fieldkit/runtime/content/fieldkit/personal/...`
- FTP and TFTP downloads when those services are currently active

## Notes

- Short `502` responses from nginx can happen during app restarts if the proxy comes up before uvicorn is ready.
- Browser hard refreshes may be needed after frontend changes because `app.js` and `styles.css` are cached by the browser. Use a fresh shared cache revision (`?v=...`) on **both assets across all HTML templates** when shipping shared UI changes. Keep those revisions when reverting unrelated page markup, so a rollback does not reuse an older cached stylesheet/script URL.
- `/pi-shell` also depends on vendored terminal assets under `app/static/vendor`, so a hard refresh is especially important after shell UI changes.
- If `git pull --ff-only` fails, inspect local changes before forcing anything.
- Keep the repo and deployed app rooted at `/opt/fieldkit` for consistency with the current systemd and nginx assets.
- Local operator notes such as `TODO.local.md` and `HANDOFF.md` should stay out of git and off the appliance.
- The shared export tree is only for `data`, `personal`, and `usb`; `serial-logs` remain GUI-only.
- TFTP and FTP are toggle-controlled from the UI; SCP remains available through the normal SSH service without a separate toggle.
- Plain HTTP is the appliance access path.
- Fieldkit AP mode now uses dedicated `hostapd` and AP-only `dnsmasq` units instead of a NetworkManager hotspot profile.
- Keep a wired path available when testing AP mode changes.
- The export tree is synced once at startup and on file mutations; it is no longer rescanned on every directory listing.
- `service` needs NOPASSWD sudo only for the allowlisted commands in `deploy/sudoers/fieldkit-network`. Ethernet apply requires the `nmcli connection modify/up` rules; password change requires `scripts/change_password.sh`.

## One-click appliance updates

Kits at v0.1.7+ can update themselves from the configured Fieldkit server:

- Settings page → **Appliance updates**: shows the installed version, checks
  the server for the latest published bundle, and offers **Apply update**.
- The server publishes `fieldkit-update-<version>.tgz` and
  `fieldkit-update-latest.json` in the Spaces `releases/` area; the device API
  (`/api/v1/device/update-latest`, device-token auth) hands kits a fresh
  presigned download URL (the upload key is limited-access, so no bucket
  policy is used).
- Applying downloads the bundle, verifies its SHA-256, backs up
  `app/scripts/deploy` to `/root/fieldkit-backups/fieldkit-update-pre-*.tgz`,
  extracts, refreshes sudoers, and restarts the web service via a transient
  `fieldkit-post-update` unit so the restart does not kill the updater.
  Progress lands in `runtime/state/update-state.json`.
- Build bundles with `scripts/build_update_bundle.sh <version>`; publish to
  the bucket (see `docs/golden-image-build.md`). Keep the monthly golden image
  for new kits and ship in-place updates between releases.
