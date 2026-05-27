# Raspberry Pi Setup

This document describes how to prepare a fresh Raspberry Pi as a Fieldkit appliance.

## Minimum supported target

- Raspberry Pi 3 Model B or newer
- Debian 13 (`trixie`) 64-bit
- NetworkManager enabled
- SSH access during setup

Reference baseline details are in [platform-baseline.md](platform-baseline.md).

## Fresh install bootstrap

Start from a clean Debian 13 64-bit Raspberry Pi install with SSH enabled and wired Ethernet available.

Install only what is needed to fetch the repo:

```bash
sudo apt-get update
sudo apt-get install -y git
```

Clone Fieldkit and run the bootstrap script:

```bash
git clone https://github.com/infragilis/fieldkitV2.git
cd fieldkitV2
sudo bash scripts/bootstrap_fresh_pi.sh
```

The script installs OS packages, creates or updates the `service` user, configures NetworkManager, clones or updates `/opt/fieldkit`, creates the Python virtualenv, installs Fieldkit, installs systemd/nginx/transfer/AP support, and starts the web service.

The default bootstrap uses plain HTTP, not HTTPS.

Default access after setup:

- `http://fieldkit.local/`
- `http://10.42.0.1/` when AP mode is enabled

Default credentials:

- SSH user: `service`
- SSH password: `service`
- Wi-Fi AP SSID: `fieldkit`
- Wi-Fi AP password: `fieldkit`

Change the default password immediately on any real deployment.

## Bootstrap options

The script can be customized with environment variables:

```bash
sudo FIELDKIT_PASS='new-password' \
  FIELDKIT_HOSTNAME=fieldkit \
  FIELDKIT_ROOT=/opt/fieldkit \
  FIELDKIT_REPO_URL=https://github.com/infragilis/fieldkitV2.git \
  FIELDKIT_BRANCH=main \
  bash scripts/bootstrap_fresh_pi.sh
```

Supported variables:

- `FIELDKIT_ROOT` defaults to `/opt/fieldkit`
- `FIELDKIT_USER` defaults to `service`
- `FIELDKIT_PASS` defaults to `service`
- `FIELDKIT_HOSTNAME` defaults to `fieldkit`
- `FIELDKIT_REPO_URL` defaults to the public GitHub repo URL
- `FIELDKIT_BRANCH` defaults to `main`
- `INSTALL_AP_SUPPORT` defaults to `1`
- `INSTALL_TRANSFER_SUPPORT` defaults to `1`
- `START_SERVICES` defaults to `1`

## Manual install pieces

The bootstrap script wraps the existing lower-level installers. They can still be run individually when debugging or updating one subsystem.

Provision runtime layout:

```bash
sudo FIELDKIT_ROOT=/opt/fieldkit \
  FIELDKIT_USER=service \
  FIELDKIT_PASS=service \
  FIELDKIT_HOSTNAME=fieldkit \
  bash scripts/provision_pi.sh
```

Install systemd units:

```bash
cd /opt/fieldkit
sudo FIELDKIT_ROOT=/opt/fieldkit SERVICE_USER=service bash scripts/install_systemd.sh
```

Install transfer service support:

```bash
cd /opt/fieldkit
sudo bash scripts/install_transfer_services.sh
```

Install dedicated Wi-Fi AP support:

```bash
cd /opt/fieldkit
sudo bash scripts/install_wifi_ap_support.sh
```

Install or refresh nginx plain HTTP export mode:

```bash
cd /opt/fieldkit
sudo bash scripts/install_export_http_mode.sh
```

## Notes

- Use wired Ethernet during first setup and AP mode testing so the Pi remains reachable for recovery.
- TFTP and FTP are installed disabled by default and can be enabled later from the Settings page.
- SCP works through the normal SSH service.
- If `/opt/fieldkit` already exists and is not a Git checkout, move it aside or set `FIELDKIT_ROOT` before running the bootstrap script.
