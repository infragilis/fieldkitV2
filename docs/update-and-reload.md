# Update And Reload

This document describes how to update a deployed Fieldkit appliance from git and reload the running services.

The currently deployed web UI includes:

- a main dashboard at `/`
- a dedicated settings page at `/settings`
- a local shell page at `/pi-shell` backed by an in-browser terminal emulator
- popup console windows at `/serial-console/0` and `/serial-console/1`
- a files page at `/files`
- a raw export browser at `/fieldkit`

The raw export browser is intended for device-side downloads. By default, `/fieldkit/...` is available over plain HTTP on port `80`, while the main GUI can remain on HTTPS.

## Pull the latest repo state

On the Raspberry Pi:

```bash
cd /opt/fieldkit
git pull --ff-only
```

## Refresh the Python environment

```bash
cd /opt/fieldkit
python3 -m venv .venv
. .venv/bin/activate
pip install --upgrade pip
pip install -e .
```

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

## Re-apply HTTPS

If the TLS config or certificate workflow changed:

```bash
cd /opt/fieldkit
sudo bash scripts/install_https_self_signed.sh
```

## Full update sequence

```bash
cd /opt/fieldkit
git pull --ff-only
python3 -m venv .venv
. .venv/bin/activate
pip install --upgrade pip
pip install -e .
sudo systemctl restart fieldkit-web.service
sudo nginx -t
sudo systemctl reload nginx
```

## Health checks

Verify locally on the Pi:

```bash
curl -k https://127.0.0.1/
curl -k https://127.0.0.1/settings
curl -k https://127.0.0.1/pi-shell
curl -k https://127.0.0.1/files
curl -k https://127.0.0.1/readme
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

- HTTPS API upload and download
- plain HTTP download from `/fieldkit/personal/...`
- SCP download from `/opt/fieldkit/runtime/content/fieldkit/personal/...`
- FTP and TFTP downloads when those services are currently active

## Notes

- Short `502` responses from nginx can happen during app restarts if the proxy comes up before uvicorn is ready.
- Browser hard refreshes may be needed after frontend changes because `app.js` and `styles.css` are cached by the browser.
- `/pi-shell` also depends on vendored terminal assets under `app/static/vendor`, so a hard refresh is especially important after shell UI changes.
- If `git pull --ff-only` fails, inspect local changes before forcing anything.
- Keep the repo and deployed app rooted at `/opt/fieldkit` for consistency with the current systemd and nginx assets.
- Local operator notes such as `TODO.local.md` and `HANDOFF.md` should stay out of git and off the appliance.
- The shared export tree is only for `data`, `personal`, and `usb`; `serial-logs` remain GUI-only.
- TFTP and FTP are toggle-controlled from the UI; SCP remains available through the normal SSH service without a separate toggle.
- Plain HTTP export for `/fieldkit/...` is the default so non-HTTPS-capable maintenance clients can still download from the appliance.
- Fieldkit AP mode now uses dedicated `hostapd` and AP-only `dnsmasq` units instead of a NetworkManager hotspot profile.
- Keep a wired path available when testing AP mode changes.
