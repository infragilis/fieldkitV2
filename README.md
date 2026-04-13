# Fieldkit

Fieldkit is a Raspberry Pi toolkit for field work on network equipment. It gives you a local web interface for console access, file handling, transfer services, and appliance management.

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

## Wi-Fi Access Point Prep

Fieldkit can be prepared with a precreated Wi-Fi access-point profile:

- SSID: `fieldkit`
- Password: `fieldkit`

This profile can be created in advance and left disabled until the kit is ready to switch to AP mode.

## Default Access

The default appliance SSH login is `service` / `service`.

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
