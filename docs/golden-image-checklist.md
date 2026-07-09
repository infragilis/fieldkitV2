# Golden Image Checklist

Use this checklist when preparing a Raspberry Pi as a Fieldkit appliance for another field engineer.

## Hardware baseline

- [ ] Raspberry Pi 3 Model B or newer
- [ ] 64-bit Debian 13 (`trixie`) installed
- [ ] Network connectivity available for package install and repo clone
- [ ] Two USB serial adapters available for validation

## OS baseline

- [ ] `sudo apt-get update && sudo apt-get upgrade -y`
- [ ] Repo cloned to `/opt/fieldkit`
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
- [ ] HTTP path validated locally on the Pi

## Validation

- [ ] `curl -fsS http://127.0.0.1/` returns the Fieldkit UI
- [ ] Main page loads from another machine on the same network
- [ ] `/readme` renders as a web page
- [ ] `/tools` renders the offline subnet calculator
- [ ] `/pi-shell` renders as a working in-browser terminal
- [ ] `/kit-docs` loads
- [ ] Serial adapters are visible in the UI when attached

## Handoff notes

- [ ] Repo access method documented for the next engineer
- [ ] Fieldkit IP or access method documented
- [ ] Local content/data sync expectations documented
