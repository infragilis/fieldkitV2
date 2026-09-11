# Fieldkit

Fieldkit is a Raspberry Pi toolkit for field work on network equipment. It gives you a local web interface for console access, file handling, transfer services, and appliance management.
Apple devices can reach the GUI at http://fieldkit.local/ while connected to the Fieldkit AP. Direct fallback: http://10.42.0.1/

Current appliance version: **v0.1.6**. Cluster Import and Server Sync are marked
with amber **beta** badges in the menu.

## What Fieldkit Does

- Provides two USB serial console sessions with popup console windows
- Stores files locally in `data`, `personal`, `usb`, and `serial-logs`
- Supports browser uploads and downloads from the kit
- Captures serial session logs for later download
- Shares files over HTTP
- Shares files over SCP
- Can enable FTP and TFTP when needed
- Includes a local shell page for direct access to the Pi from the browser
- Includes built-in vendor reference notes for field use
- Supports multiple UI languages in the web interface and README view

## Hardware Recommendations

- Raspberry Pi 3 Model B or newer
- 64-bit Debian 13 (`trixie`)
- Two USB serial adapters or console cables if you want to use both console ports
- A USB flash drive if you want removable local storage on the kit
- Wired Ethernet recommended for setup, updates, and AP cutover testing

## Storage Recommendation

Fieldkit stores uploaded files, exported files, and serial session logs on the appliance itself.

- Minimum recommended microSD card size: `32 GB`
- Use larger storage if you expect to keep firmware images, switch software, or long serial log history on the kit

## Main Features

- Dashboard for quick access to consoles, files, docs, and settings
- Settings page for connectivity, transfer-service toggles, password change, and serial presets
- Files page for browsing `data`, `personal`, `usb`, and `serial-logs`
- Cluster workbook import and draft Ansible output at `/cluster-import` (beta)
- Background server sync, progress and last-result history at `/server-sync` (beta)
- Raw export browser at `/fieldkit` for direct file access
- Browser shell at `/pi-shell`
- Local documentation index at `/kit-docs`
- Localized README page at `/readme`

## Server Sync And File Libraries

Configure the server URL and your device token on the appliance's **Server Sync**
page. Checks run 10 minutes after boot and hourly, with **Sync now** for an immediate
check. Downloaded files are size/checksum verified before publication.

- **`data/{fos,bes,cisco,ontap,nvidia}`** is the shared vendor library for software,
  firmware and reference files. **`personal`** holds your configs and user-specific files.
- On the **server webfront**, **Data** provides folder browsing, Download buttons
  and **My sync subscriptions**. Choose folders and save; every kit using your
  token follows those choices on its next sync. Personal files always sync.
- Existing accounts keep all-folder sync until edited; new accounts start with
  personal files only. Unsubscribing leaves already-downloaded files on the kit.
- The server uploader supports resumable 8 MiB chunks, progress/speed/ETA,
  retry/cancel and verified completion. Uploading a shared file does not
  automatically subscribe you to its folder.
- On the **appliance**, use **Files → data** or **Files → personal** to browse and
  download local content. The Data picker and subscriptions belong to the server.

See [Server Sync](docs/server-sync.md) for setup and behavior, and
[Cluster Import](docs/cluster-import.md) for workbook import.

## Transfer Options

Fieldkit can make shared files available through:

- HTTP
- SCP
- FTP
- TFTP

HTTP export is available by default for `/fieldkit/...`. FTP and TFTP can be enabled from the Settings page when needed.

## Wi-Fi Access Point

Fieldkit can run a dedicated Wi-Fi access point for direct local access:

- SSID: `fieldkit`
- Password: `fieldkit`

Use wired Ethernet for setup and recovery while testing AP mode changes.

## Default Access

Default appliance access credentials:

- SSH user: `service`
- SSH password: `service`
- Wi-Fi AP SSID: `fieldkit`
- Wi-Fi AP password: `fieldkit`

When the appliance is in AP mode, clients can connect to the GUI at:

- `http://10.42.0.1/`
- `http://fieldkit.local/` on Bonjour-capable clients such as iPadOS and macOS

Change this immediately on any real deployment.

## Recommended Platform

- Raspberry Pi 3 Model B or newer
- Debian 13 (`trixie`) 64-bit
- Python 3.13
- NetworkManager
- OpenSSH server

## Install On A Raspberry Pi

Start from a clean Debian 13 64-bit Raspberry Pi install with SSH enabled, internet access, and wired Ethernet available for recovery. Run these commands from the initial account created during OS setup.

```bash
sudo apt-get update
sudo apt-get install -y git
sudo git clone --branch main --depth 1 https://github.com/infragilis/fieldkitV2.git /opt/fieldkit
cd /opt/fieldkit
sudo bash scripts/install_fieldkit.sh
```

The clone command explicitly installs the current `main` branch. The installer configures the `service` user, Python environment, systemd units, nginx plain HTTP dashboard, transfer services, Wi-Fi AP support, and runtime directories.

Verify the appliance locally before disconnecting the wired connection:

```bash
systemctl is-active fieldkit-web.service
systemctl is-active nginx
curl -fsS http://127.0.0.1/ >/dev/null && echo "Fieldkit web UI is available"
```

Default access after setup:

- `http://fieldkit.local/`
- `http://10.42.0.1/` when AP mode is enabled

Default bootstrap credentials are `service` / `service`. The Fieldkit Wi-Fi AP starts automatically with SSID `fieldkit` and password `fieldkit`.

## Documentation

- Fresh install after cloning: `sudo bash scripts/install_fieldkit.sh`
- [docs/pi-setup.md](docs/pi-setup.md)
- [docs/update-and-reload.md](docs/update-and-reload.md)
- [docs/golden-image-checklist.md](docs/golden-image-checklist.md)
- [docs/architecture.md](docs/architecture.md)
- [docs/server-sync.md](docs/server-sync.md)
- [docs/cluster-import.md](docs/cluster-import.md)
- [Device API contract](docs/fieldkit-server-api.openapi.yaml)

## Open Source

Fieldkit is open source and available under the MIT license in [LICENSE](https://github.com/infragilis/fieldkitV2/blob/main/LICENSE).

Issues and feature requests:

- <https://github.com/infragilis/fieldkitV2/issues>
