# Raspberry Pi Setup

This document describes how to prepare a fresh Raspberry Pi as a Fieldkit appliance.

## Minimum supported target

- Raspberry Pi 3 Model B or newer
- Debian 13 (`trixie`) 64-bit
- NetworkManager enabled
- SSH access during setup

Reference baseline details are in [platform-baseline.md](platform-baseline.md).

## Standard install after cloning

Start from a clean Debian 13 64-bit Raspberry Pi install with SSH enabled, internet access, and wired Ethernet available for recovery. Run these commands from the initial account created during OS setup.

Install only what is needed to fetch the repo, then clone Fieldkit directly to the intended appliance root:

```bash
sudo apt-get update
sudo apt-get install -y git
sudo git clone --branch main --depth 1 https://github.com/infragilis/fieldkitV2.git /opt/fieldkit
cd /opt/fieldkit
sudo bash scripts/install_fieldkit.sh
```

The clone command explicitly installs the current `main` branch. The installer script installs OS packages, creates or updates the `service` user, configures NetworkManager, creates the Python virtualenv, installs Fieldkit, installs systemd/nginx/transfer/AP support, and starts the web service.

Verify the appliance locally before disconnecting wired Ethernet:

```bash
systemctl is-active fieldkit-web.service
systemctl is-active nginx
curl -fsS http://127.0.0.1/ >/dev/null && echo "Fieldkit web UI is available"
```

Fieldkit serves the dashboard over plain HTTP only.

## Fresh OS bootstrap helper

If you are starting from a minimal shell and want the script to install bootstrap prerequisites and clone/update `/opt/fieldkit` for you, use:

```bash
git clone --branch main --depth 1 https://github.com/infragilis/fieldkitV2.git
cd fieldkitV2
sudo bash scripts/bootstrap_fresh_pi.sh
```

The bootstrap helper installs `git`, clones or updates `/opt/fieldkit` from `main`, then runs `scripts/install_fieldkit.sh` from that checkout.

Default access after setup:

- `http://fieldkit.local/`
- `http://10.42.0.1/` when AP mode is enabled

Default credentials:

- SSH user: `service`
- SSH password: `service`
- Wi-Fi AP SSID: `fieldkit`
- Wi-Fi AP password: `fieldkit`

The Fieldkit Wi-Fi AP starts automatically with SSID `fieldkit` and password `fieldkit`.

## Install options

Both install scripts can be customized with environment variables:

```bash
sudo FIELDKIT_PASS='new-password' \
  FIELDKIT_HOSTNAME=fieldkit \
  FIELDKIT_ROOT=/opt/fieldkit \
  bash scripts/install_fieldkit.sh
```

Supported variables:

- `FIELDKIT_ROOT` defaults to the current checkout root for `install_fieldkit.sh` and `/opt/fieldkit` for `bootstrap_fresh_pi.sh`
- `FIELDKIT_USER` defaults to `service`
- `FIELDKIT_PASS` defaults to `service`
- `FIELDKIT_HOSTNAME` defaults to `fieldkit`
- `INSTALL_OS_PACKAGES` defaults to `1` for `install_fieldkit.sh`
- `INSTALL_AP_SUPPORT` defaults to `1`
- `INSTALL_TRANSFER_SUPPORT` defaults to `1`
- `START_SERVICES` defaults to `1`
- `FIELDKIT_REPO_URL` and `FIELDKIT_BRANCH` are supported by `bootstrap_fresh_pi.sh` only

## Manual install pieces

The main installer wraps the existing lower-level installers. They can still be run individually when debugging or updating one subsystem.

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

Install or refresh nginx plain HTTP mode:

```bash
cd /opt/fieldkit
sudo bash scripts/install_export_http_mode.sh
```

## Notes

- Use wired Ethernet during first setup and AP mode testing so the Pi remains reachable for recovery.
- TFTP and FTP are installed disabled by default and can be enabled later from the Settings page.
- SCP works through the normal SSH service.
- If `/opt/fieldkit` already exists and is not a Git checkout, move it aside or set `FIELDKIT_ROOT` before running the bootstrap script.
