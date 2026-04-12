# Update And Reload

This document describes how to update a deployed Fieldkit appliance from git and reload the running services.

The currently deployed web UI includes:

- a main dashboard at `/`
- a dedicated settings page at `/settings`
- popup console windows at `/serial-console/0` and `/serial-console/1`
- a files page at `/files`

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
curl -k https://127.0.0.1/files
curl -k https://127.0.0.1/readme
systemctl is-active fieldkit-web.service
systemctl is-active nginx
```

## Notes

- Short `502` responses from nginx can happen during app restarts if the proxy comes up before uvicorn is ready.
- Browser hard refreshes may be needed after frontend changes because `app.js` and `styles.css` are cached by the browser.
- If `git pull --ff-only` fails, inspect local changes before forcing anything.
- Keep the repo and deployed app rooted at `/opt/fieldkit` for consistency with the current systemd and nginx assets.
- Local operator notes such as `TODO.local.md` and `HANDOFF.md` should stay out of git and off the appliance.
