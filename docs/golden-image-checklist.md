# Golden Image Checklist

Use this checklist when preparing a Raspberry Pi as a Fieldkit appliance for another field engineer.

## Hardware baseline

- [ ] Raspberry Pi 3 Model B or newer
- [ ] 64-bit Raspberry Pi OS Lite (Trixie, Debian 13-based) installed
- [ ] Network connectivity available for package install and repo clone
- [ ] Two USB serial adapters available for validation

## OS baseline

- [ ] `sudo apt-get update && sudo apt-get upgrade -y`
- [ ] Repo cloned to `/opt/fieldkit`
- [ ] Clone used `--branch main` so the current release branch was installed
- [ ] `sudo bash scripts/install_fieldkit.sh` completed successfully from `/opt/fieldkit`
- [ ] `network-manager` installed and enabled
- [ ] `openssh-server` installed and reachable
- [ ] `python3`, `python3-venv`, `python3-pip`, and `sudo` installed
- [ ] `hostapd`, `dnsmasq`, `tftpd-hpa`, `nginx` installed

## Appliance identity

- [ ] Hostname set to `fieldkit`
- [ ] `/etc/hosts` contains `127.0.1.1 fieldkit`
- [ ] `service` user exists
- [ ] `service` password changed from the default `service`
- [ ] `service` user is in `sudo`, `dialout`, `netdev`, and `plugdev`

## Repo and runtime

- [ ] Runtime provisioned by `scripts/install_fieldkit.sh`
- [ ] Deployed app rooted at `/opt/fieldkit`
- [ ] Python venv created at `/opt/fieldkit/.venv`
- [ ] `pip install -e .` completed successfully

## Services

- [ ] `fieldkit-web.service` installed, enabled, and active
- [ ] `nginx` installed, enabled, and active
- [ ] dedicated Fieldkit Wi-Fi AP support installed if the kit will offer direct wireless access later
- [ ] Fieldkit AP is active on `wlan0` with SSID `fieldkit`
- [ ] HTTP path validated locally on the Pi
- [ ] `curl -fsS http://127.0.0.1/` succeeds before disconnecting wired Ethernet

## Validation

- [ ] `curl -fsS http://127.0.0.1/` returns the Fieldkit UI
- [ ] Main page loads from another machine on the same network
- [ ] `/readme` renders as a web page
- [ ] `/tools` renders the offline subnet calculator
- [ ] `/pi-shell` renders as a working in-browser terminal
- [ ] `/kit-docs` loads
- [ ] Serial adapters are visible in the UI when attached

## Golden image acceptance (fresh flash, Pi 3 / Pi 4 / Pi 5)

Run the strict offline audit first (`scripts/golden-image-audit.sh` must pass).
Then flash a **fresh card** per board and boot each board twice (first boot +
one cold reboot). A publish is blocked unless all three pass both boots.

Per board (within 180 s of first boot):

- [ ] HDMI shows `fieldkit login:` and a USB keyboard works
- [ ] `systemctl is-system-running --wait` reports `running`; `systemctl --failed` is empty
- [ ] `ssh service@<eth-ip>` works with password `service`
- [ ] `curl -fsS http://127.0.0.1/` returns the UI (nginx + `fieldkit-web` active)
- [ ] Ethernet has a DHCP address on `eth0`
- [ ] `fieldkit` AP is visible from an independent Wi-Fi client; client gets a
      `10.42.0.10–150` lease and `curl -fsS http://10.42.0.1/` works
- [ ] `iw dev wlan0 info` reports AP mode
- [ ] Root partition/fs grew to fill the card (no ~10 MB+ free tail)
- [ ] `rpi-resize.service` is `disabled` (it disarms itself)
- [ ] `/etc/machine-id` is a 32-hex id; `ssh-keygen -lf` works

Cold reboot each board:

- [ ] machine-id and host-key fingerprint unchanged from first boot
- [ ] Ethernet, SSH, nginx/web, and the AP all return
- [ ] No resize or host-key generation repeats

Record the machine-id and host-key fingerprint for each board; they must differ
across the three boards.

## Handoff notes

- [ ] Repo access method documented for the next engineer
- [ ] Fieldkit IP or access method documented
- [ ] Local content/data sync expectations documented
