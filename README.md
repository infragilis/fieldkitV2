# Fieldkit

Fieldkit is a Raspberry Pi toolkit for field work on network equipment. It gives you a local web interface for console access, file handling, transfer services, and appliance management.
Apple devices can reach the GUI at http://fieldkit.local/ while connected to the Fieldkit AP. Direct fallback: http://10.42.0.1/

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
- Raw export browser at `/fieldkit` for direct file access
- Browser shell at `/pi-shell`
- Local documentation index at `/kit-docs`
- Localized README page at `/readme`

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

## Documentation

- [docs/pi-setup.md](docs/pi-setup.md)
- [docs/update-and-reload.md](docs/update-and-reload.md)
- [docs/golden-image-checklist.md](docs/golden-image-checklist.md)
- [docs/architecture.md](docs/architecture.md)

## Open Source

Fieldkit is open source and available under the MIT license in [LICENSE](https://github.com/infragilis/fieldkitV2/blob/main/LICENSE).

Issues and feature requests:

- <https://github.com/infragilis/fieldkitV2/issues>
