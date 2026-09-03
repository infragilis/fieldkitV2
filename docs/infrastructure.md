# Infrastructure Index

Single source of truth for Fieldkit hosts, services, environments, and
deployment. Live access details (current DHCP address, default credentials,
pre-deploy backups) stay in `HANDOFF.md` (local-only); do not duplicate them
here or in any tracked file.

## Repository & Ownership

- Remote: `git@github-fieldkit:infragilis/fieldkitV2.git` (public: `https://github.com/infragilis/fieldkitV2`)
- License: MIT (`LICENSE`)
- Owner: Infragilis. Public Fieldkit email: `info@infragilis.org`.
- CI/CD: none — deployment is manual (scripts + copy).

## Environments

| Environment | Role | Notes |
|---|---|---|
| Dev host | source checkout + tests | this checkout; `pytest` runs the suite |
| Appliance (Raspberry Pi) | deployed Fieldkit | app root `/opt/fieldkit`, DHCP address (see `HANDOFF.md`) |

## Hosts & Services (appliance)

- `fieldkit-web.service` — FastAPI/uvicorn on `127.0.0.1:8000`, user `service`
- `nginx` — plain-HTTP front end on port 80 (no TLS)
- OpenSSH — SCP + the local-shell account
- NetworkManager — primary network control plane
- `fieldkit-ap-hostapd` + `fieldkit-ap-dnsmasq` — dedicated AP mode (SSID `fieldkit`)
- `fieldkit-startup-network.service` — applies stored network mode before the web service
- `vsftpd` (FTP) + `tftpd-hpa` (TFTP) — installed disabled; toggled from Settings

## Network

- AP gateway: `http://10.42.0.1/` (and `http://fieldkit.local/` on Bonjour clients)
- Static eth0 default: `192.168.200.120/24` (also the smoke-test default host)
- Live appliance IP is DHCP and changes — confirm via UniFi (hostname `fieldkit`); current value in `HANDOFF.md`

## Storage & Runtime (appliance)

- `/opt/fieldkit` — app root (git checkout where credentials exist; copied tree on the current appliance)
- `runtime/content` + `runtime/state` — mutable data and settings
- Libraries: `data` (shared), `personal` (uploads), `usb`, `serial-logs` (GUI-only, excluded from the shared export tree)

## Deployment

- Fresh install: `sudo bash scripts/install_fieldkit.sh` (or `scripts/bootstrap_fresh_pi.sh` for a minimal OS)
- Update path: `docs/update-and-reload.md` (copy-deploy for the current appliance; `git pull` for git-capable installs)
- sudoers allowlists: `deploy/sudoers/fieldkit-network`, `deploy/sudoers/fieldkit-transfer`

## Dependencies

- Runtime: FastAPI, Pydantic, Uvicorn, python-multipart, pyserial (`pyproject.toml`)
- Dev/test: httpx, pytest
- Baseline platform: `docs/platform-baseline.md`

## Secrets

- Machine access lives in the Bitwarden Secrets Manager project `fieldkit`.
- Default credentials are documented only in `HANDOFF.md`; never copy them into public docs or commits.
- Do not store secret values anywhere in this repository.
