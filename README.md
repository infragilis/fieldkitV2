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
- Directory browsing for `data`, `personal`, and `usb`
- Upload support into `personal`
- Persisted settings for ethernet, Wi-Fi mode, and serial console profiles
- Placeholder endpoints for password changes, connectivity, and serial device status
- Dry-run system apply planning for hostname and ethernet changes
- A systemd unit template and install script for the web service
- Pi capability detection so Wi-Fi behavior can differ cleanly across Pi 3 and newer vs older models
- WebSocket serial console plumbing for the two configured USB serial profiles

Pi-specific integrations such as `hostapd`, `dnsmasq`, `nmcli`, `tftpd`, `scp`, and serial streaming are intentionally isolated behind service modules so they can be implemented and tested separately.

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

## Next implementation steps

1. Wire network service actions to NetworkManager or systemd-networkd on the Pi.
2. Add richer serial session controls such as break, reconnect, and capture-to-file.
3. Add HTTP/TFTP/SCP serving workflows for firmware and images.
4. Add optional removable USB content mounting and browsing.
5. Add appliance provisioning scripts for hostname, user setup, and service installation.

## Deployment assets

- [scripts/provision_pi.sh](/opt/fieldkit/scripts/provision_pi.sh:1) prepares hostname, user, and runtime directories.
- [scripts/install_systemd.sh](/opt/fieldkit/scripts/install_systemd.sh:1) installs the web service unit.
- [deploy/systemd/fieldkit-web.service](/opt/fieldkit/deploy/systemd/fieldkit-web.service:1) runs the FastAPI app under `uvicorn`.
