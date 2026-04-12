# Fieldkit

Fieldkit is a Raspberry Pi appliance for field servicing network devices. It exposes:

- A web UI for downloads, uploads, connectivity, and console management
- Two USB serial console endpoints with independent settings
- A local content library split into `data`, `personal`, and optional `usb`
- A modular backend so Pi integration code stays isolated from the web layer

## Current scope

This initial scaffold provides:

- A FastAPI backend with modular routers and services
- A static web UI shell
- A dedicated `Files` page for browsing `data`, `personal`, and `usb`
- Upload support into `personal`
- Persisted settings for ethernet, Wi-Fi mode, and serial console profiles
- Local vendor reference notes linked from the main page
- Placeholder endpoints for password changes, connectivity, and serial device status
- Dry-run system apply planning for hostname and ethernet changes
- A systemd unit template and install script for the web service
- Pi capability detection so Wi-Fi behavior can differ cleanly across Pi 3 and newer vs older models
- WebSocket serial console plumbing for the two configured USB serial profiles

Pi-specific integrations such as `hostapd`, `dnsmasq`, `nmcli`, `tftpd`, `scp`, and serial streaming are intentionally isolated behind service modules so they can be implemented and tested separately.

## File Libraries

Fieldkit exposes three file libraries through the `Files` page:

- `data`
- `personal`
- `usb`

Current USB behavior:

- If removable storage is auto-mounted under `/media/service`, `/media`, or `/mnt`, Fieldkit will use that mount as the `usb` library automatically.
- The current implementation is intended for the common single-mounted-USB-stick case.
- Multi-drive handling, labels, and hot-plug refresh are tracked in [TODO.md](/opt/fieldkit/TODO.md:1).

## Layout

```text
fieldkit/
  app/
    api/          # HTTP routes
    core/         # Config and data models
    services/     # Platform-specific service boundaries
    static/       # Frontend assets
    main.py       # FastAPI application entry
  runtime/
    content/
      data/
      personal/
      usb/
    state/
      settings.json
```

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000`.

The app exposes serial console WebSocket endpoints at `/api/serial/ws/0` and `/api/serial/ws/1`.

## Kit Documentation

Fieldkit includes local vendor quick-reference notes that are served by the app and intended to be available directly on the appliance in the field.

Topics currently included:

- `NetApp`
- `Cisco`
- `NVIDIA`
- `Brocade Fabric OS`
- `Broadcom Ethernet Switching`

These notes live in [docs/kits](/opt/fieldkit/docs/kits) and are exposed through the web UI from the main page as well as the local docs index at `/kit-docs`.

## Raspberry Pi target behavior

- Ethernet can be pinned to a local service IP for direct device imaging
- Wi-Fi can operate as AP or client mode
- Pi 3 and newer should expose onboard Wi-Fi flows; older models should keep Wi-Fi disabled unless an adapter is explicitly added later
- The fourth port service workflow should be implemented via the network service module
- `service/service` is the intended default appliance user
- The device hostname target is `fieldkit`

## Minimum supported platform

The current documented baseline is:

- Raspberry Pi 3 Model B or newer
- Debian 13 (`trixie`) 64-bit
- Python 3.13
- NetworkManager / `nmcli`
- OpenSSH server

Reference inventory and rationale are documented in [docs/platform-baseline.md](/opt/fieldkit/docs/platform-baseline.md:1).

## Deployment Guides

- [docs/pi-setup.md](/opt/fieldkit/docs/pi-setup.md:1) explains how to prepare a Raspberry Pi to the minimum supported Fieldkit baseline.
- [docs/update-and-reload.md](/opt/fieldkit/docs/update-and-reload.md:1) explains how to pull the repo, refresh the Python environment, and reload the deployed kit.
- [docs/golden-image-checklist.md](/opt/fieldkit/docs/golden-image-checklist.md:1) provides a concise repeatable checklist for preparing a handoff-ready Fieldkit image.

## Next implementation steps

1. Wire network service actions to NetworkManager or systemd-networkd on the Pi.
2. Add richer serial session controls such as break, reconnect, and capture-to-file.
3. Add HTTP/TFTP/SCP serving workflows for firmware and images.
4. Add optional removable USB content mounting and browsing.
5. Add appliance provisioning scripts for hostname, user setup, and service installation.

## Deployment assets

- [scripts/provision_pi.sh](/opt/fieldkit/scripts/provision_pi.sh:1) prepares hostname, user, and runtime directories.
- [scripts/install_systemd.sh](/opt/fieldkit/scripts/install_systemd.sh:1) installs the web service unit.
- [scripts/install_nginx.sh](/opt/fieldkit/scripts/install_nginx.sh:1) exposes Fieldkit on port `80` through `nginx`.
- [scripts/install_https_self_signed.sh](/opt/fieldkit/scripts/install_https_self_signed.sh:1) generates a self-signed certificate and exposes Fieldkit on `443` while keeping `80` available.
- [deploy/systemd/fieldkit-web.service](/opt/fieldkit/deploy/systemd/fieldkit-web.service:1) runs the FastAPI app under `uvicorn`.
- [deploy/nginx/fieldkit.conf](/opt/fieldkit/deploy/nginx/fieldkit.conf:1) proxies port `80` to the local app on `127.0.0.1:8000`.
- [deploy/nginx/fieldkit-ssl.conf](/opt/fieldkit/deploy/nginx/fieldkit-ssl.conf:1) adds self-signed TLS on `443` and keeps the HTTP front end on `80`.
- [docs/https-self-signed.md](/opt/fieldkit/docs/https-self-signed.md:1) explains how to export and trust the self-signed Fieldkit certificate.

## HTTPS Staging

Self-signed HTTPS is staged but not enabled on the live kit yet. When ready, run:

```bash
sudo bash /opt/fieldkit/scripts/install_https_self_signed.sh
```

This adds HTTPS on port `443` using a self-signed certificate for the Fieldkit appliance and redirects HTTP on port `80` to HTTPS.
