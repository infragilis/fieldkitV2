# Fieldkit

Fieldkit is a Raspberry Pi appliance for field servicing network devices. It exposes:

- A web UI for console access, file transfer, connectivity review, and appliance settings
- Two USB serial console endpoints with independent settings and popup console windows
- A local content library split into `data`, `personal`, `usb`, and `serial-logs`
- A modular backend so Pi integration code stays isolated from the web layer

## Hardware Note

Console access requires USB-to-serial console cables or USB serial adapters that present as `ttyUSB*` or `ttyACM*` devices on the appliance.

## Default Access

The default appliance SSH login is `service` / `service`.

This is a factory-default credential only and should be changed immediately on any real kit.

## Open Source

Fieldkit is fully open source and available for anyone to use, modify, and distribute under the MIT license in [LICENSE](/opt/fieldkit/LICENSE:1).

This project is provided `AS IS`, without warranty of any kind, express or implied.

## Issues And Features

Post bugs, issues, and feature requests at:

- <https://github.com/infragilis/fieldkitV2/issues>

## Current Functionality

The current repo and live kit provide:

- A FastAPI backend with modular routers and services
- A main dashboard focused on console access, docs, and uploads
- A dedicated `/settings` page for connectivity, networking, password changes, and serial presets
- A dedicated `/files` page for browsing `data`, `personal`, `usb`, and `serial-logs`
- Desktop-to-kit uploads into `personal` or mounted `usb`
- Duplicate upload protection so existing files are not overwritten silently
- Delete actions for `personal` files and captured `serial-logs`
- USB auto-detection for common mounted media roots under `/media/service`, `/media`, and `/mnt`
- Hidden/macOS metadata filtering in the file browser so `._*`, `.Spotlight-V100`, and similar entries do not clutter USB views
- Local vendor reference notes linked from the web UI
- Persisted settings for ethernet, Wi-Fi mode, and serial console profiles
- Quick serial preset switching between `9600 8N1` and `115200 8N1`
- Automatic serial adapter detection so console sessions can work without manually setting `/dev/ttyUSB*` paths
- A dedicated `/serial-settings` page for full per-console settings such as optional device preference, baud, parity, data bits, and stop bits
- Popup serial console windows at `/serial-console/0` and `/serial-console/1`
- Direct keyboard capture in popup console sessions instead of line-by-line send forms
- Timestamped serial session log capture under `runtime/state/serial-logs`
- Reset actions for active console sessions
- Dry-run network apply planning for hostname and ethernet changes
- A systemd unit template and install script for the web service
- Pi capability detection so Wi-Fi behavior can differ cleanly across Pi 3 and newer vs older models

Pi-specific integrations such as `hostapd`, `dnsmasq`, `nmcli`, `tftpd`, `scp`, and serial streaming are intentionally isolated behind service modules so they can be implemented and tested separately.

## Operational Requirements

- Fieldkit should be able to run Ansible workflows against field devices from the kit itself.
- Serial console sessions should be logged on the kit with date/time-stamped session files for later review.

## Web UI

Primary routes:

- `/` for the main dashboard
- `/settings` for connectivity, networking, password, and serial preset management
- `/serial-settings` for detailed per-console serial profile editing
- `/files` for file browsing, upload, and delete actions
- `/readme` for the repo README rendered locally on the kit
- `/kit-docs` for the local documentation index

## File Libraries

Fieldkit exposes four file libraries through the `Files` page:

- `data`
- `personal`
- `usb`
- `serial-logs`

Current USB behavior:

- If removable storage is auto-mounted under `/media/service`, `/media`, or `/mnt`, Fieldkit will use that mount as the `usb` library automatically.
- The current implementation is intended for the common single-mounted-USB-stick case.
- Multi-drive handling, labels, and hot-plug refresh are planned but tracked only in the local working notes, not in the deployed repo.

Current file behavior:

- Uploads are allowed to `personal` and `usb`
- Uploads to `data` and `serial-logs` are blocked
- Duplicate filenames return a warning instead of overwriting the existing file
- Deletes are allowed for `personal` and `serial-logs`
- USB files are currently treated as read-only from a delete perspective

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
Each session creates a UTC-stamped log file in `runtime/state/serial-logs` and records open/close events plus `RX` and `TX` traffic.
If no device preference is saved for a console, Fieldkit auto-assigns the next detected `ttyUSB*` or `ttyACM*` adapter.

Popup console windows are exposed at `/serial-console/0` and `/serial-console/1`.
These windows are intended to be moved around independently by field engineers and capture keyboard input directly.

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
- `service/service` is the intended default appliance SSH username and password
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

## Current Limitations

- USB browsing still assumes the common single-mounted-drive case
- Multi-drive labels and hot-plug refresh are not implemented yet
- Serial adapters are auto-assigned in detected order, but stable identity by USB serial number or port topology is not implemented yet
- Password changes are still handled by a backend placeholder path
- Network apply remains a dry-run planning workflow rather than a full live reconfiguration path
- Ansible device-side workflows are not implemented yet

## Next Implementation Steps

1. Improve USB storage handling to support multiple mounted drives, labels, and live refresh.
2. Add richer serial session controls such as break handling and more detailed reconnect state.
3. Wire network service actions to real NetworkManager or systemd-networkd changes on the Pi.
4. Add HTTP/TFTP/SCP serving workflows for firmware and images.
5. Add Ansible execution workflows for field devices and NetApp runbooks.

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
