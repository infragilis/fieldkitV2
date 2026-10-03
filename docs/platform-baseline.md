# Platform Baseline

This document records the reference Raspberry Pi appliance state that Fieldkit was first built against and defines the minimum supported hardware/software baseline for other field engineers.

## Minimum supported hardware

- Raspberry Pi 3 Model B or newer
- 64-bit userspace is the reference target
- **microSD card: 64 GB minimum for kits that use Server Sync** (synced files exist twice — the local library plus the HTTP export mirror — and the kit refuses syncs it cannot fit). 32 GB remains adequate for kits that do not use Server Sync.
- Two USB-to-serial console cables or USB serial adapters for `ttyUSB` or `ttyACM` access
- Ethernet uplink for direct servicing workflows

If USB gadget export is a requirement, do not treat the Raspberry Pi 3 Model B as the preferred platform. Use a Raspberry Pi with an OTG-capable USB device port so the appliance can potentially present Fieldkit exports like a connected USB key.

Pi models older than Raspberry Pi 3 are below the intended baseline because onboard Wi-Fi is required for field connectivity workflows. Older boards may still work for limited ethernet-only cases, but they should be treated as unsupported unless an external Wi-Fi adapter strategy is added and tested.

## Reference device inventory

Collected from the current appliance at `192.168.200.120` on April 12, 2026 via SSH before convergence.

- Hostname: `servicetools`
- Model: `Raspberry Pi 3 Model B Rev 1.2`
- OS: `Debian GNU/Linux 13 (trixie)` / `13.2`
- Kernel: `6.12.47+rpt-rpi-v8`
- Architecture: `aarch64`
- Python: `3.13.5`
- `pip`: `25.1.1`
- `NetworkManager`: `1.52.1-1+rpt4`
- `nmcli`: `1.52.1`
- `openssh-server`: `1:10.0p1-7`

## Services present on the reference device

- `NetworkManager`: enabled
- `systemd-networkd`: disabled
- `hostapd`: not installed
- `dnsmasq`: not installed
- `tftpd-hpa`: not installed

## Current appliance state after convergence

The same appliance was updated on April 12, 2026 to align more closely with the intended Fieldkit baseline.

- Hostname: `fieldkit`
- `python3-venv`: installed
- `python3-pip`: installed and updated to the Raspberry Pi package build
- `hostapd`: installed, currently `masked`
- `dnsmasq`: installed and `enabled`
- `tftpd-hpa`: installed and `enabled`

The `/etc/hosts` entry was also updated so `fieldkit` resolves locally without sudo hostname warnings.

## Fieldkit baseline requirement

Fieldkit should assume this minimum software platform:

- Debian 13 (`trixie`) or a newer compatible Debian-based release
- Python 3.13 available from the system package manager
- NetworkManager and `nmcli` available and used as the primary network control plane
- OpenSSH server available for remote maintenance

These packages should be considered required for the first supported Fieldkit appliance build:

- `python3`
- `python3-venv`
- `python3-pip`
- `network-manager`
- `openssh-server`

These packages are part of the planned Fieldkit feature set and are now installed on the current reference appliance:

- `hostapd`
- `dnsmasq`
- `tftpd-hpa`

## Notes for compatibility

- Pi 3 and newer should expose Wi-Fi client and AP flows in Fieldkit.
- Older models should keep Wi-Fi features disabled unless explicit adapter support is implemented.
- Fieldkit code should continue to discover both `ttyUSB*` and `ttyACM*` serial adapters.
- Console slots are pinned to a stable adapter identity (`/dev/serial/by-id/...`, keyed by the adapter's unique USB serial), not to a `ttyUSBn` number, because kernel enumeration order changes across reboots and re-plugs. Prefer FTDI/CP210x-style adapters that expose a unique serial; adapters without one fall back to `/dev/serial/by-path` (physical port).
- Field console workflows require compatible USB-to-serial console cables or USB serial adapters.
- The current Raspberry Pi 3 Model B reference appliance does not expose a usable USB gadget controller, so it cannot emulate a USB storage device over cable.
- USB gadget export should be considered a hardware-driven enhancement path that requires a different Raspberry Pi choice.
- The appliance hostname target is `fieldkit`.
