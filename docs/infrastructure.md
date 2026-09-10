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
- Two repositories: this **public** Fieldkit repo (app/UI/tool) and a separate **private** server repo (VM/server code — never public). See `## Secrets` for the split.
- Explicitly requested work may span both repositories. Read each repository's own `AGENTS.md` and deployment instructions before working there; keep code, operational context, and memory in the repository that owns them. Unrelated projects/infrastructure remain out of scope.
- Production hostname: `https://fieldkit.infragilis.org` (public; the server base URL is configurable, not hard-coded).

## Environments

| Environment | Role | Notes |
|---|---|---|
| Dev host | appliance source checkout | edit/review source here; do not run the appliance app, tests, or builds here |
| Appliance (Raspberry Pi) | deployed Fieldkit + isolated test/build copies | app root `/opt/fieldkit`, DHCP address (see `HANDOFF.md`); keep test runtime data separate from production and attached USB media |
| Server project | server source/runtime/testing | follow the private server repository's own instructions and deployment runbook |

## Hosts & Services (appliance)

- `fieldkit-web.service` — FastAPI/uvicorn on `0.0.0.0:8000`, user `service` (current shipped and verified deployed binding)
- `nginx` — front end on port 80 (HTTP) and 443 (HTTPS, self-signed cert at `/etc/nginx/ssl/fieldkit.{crt,key}`); no HTTP→HTTPS redirect, so both work
- OpenSSH — SCP + the local-shell account
- NetworkManager — primary network control plane
- `fieldkit-ap-hostapd` + `fieldkit-ap-dnsmasq` — dedicated AP mode (SSID `fieldkit`)
- `fieldkit-startup-network.service` — applies stored network mode before the web service
- `fieldkit-server-sync.timer` + `.service` — start a background sync 10 minutes after boot, then hourly; manual Sync now does not reset this timer
- `vsftpd` (FTP) + `tftpd-hpa` (TFTP) — installed disabled; toggled from Settings

## Network

- AP gateway: `http://10.42.0.1/` (and `http://fieldkit.local/` on Bonjour clients)
- Static eth0 default: `192.168.200.120/24` (also the smoke-test default host)
- Live appliance IP is DHCP and changes — confirm via UniFi (hostname `fieldkit`); current value in `HANDOFF.md`

## Storage & Runtime (appliance)

- `/opt/fieldkit` — app root (git checkout where credentials exist; copied tree on the current appliance)
- `runtime/content` + `runtime/state` — mutable data and settings
- Libraries: `data` (shared), `personal` (uploads), `usb`, `serial-logs` (GUI-only, excluded from the shared export tree)
- Built-in data subdirectories: `ontap`, `bes`, `cisco`, `nvidia`, `fos`; server manifest paths determine placement
- `runtime/state/server-sync-status.json` — persisted sync attempt/outcome; the Server Sync page polls in-memory job progress while running

## Deployment

- Fresh install: `sudo bash scripts/install_fieldkit.sh` (or `scripts/bootstrap_fresh_pi.sh` for a minimal OS)
- Update path: `docs/update-and-reload.md` (copy-deploy for the current appliance; `git pull` for git-capable installs)
- Sync scheduling, status API, and folder behavior: [Server Sync](server-sync.md)
- sudoers allowlists: `deploy/sudoers/fieldkit-network`, `deploy/sudoers/fieldkit-transfer`

## Dependencies

- Runtime: FastAPI, Pydantic, Uvicorn, python-multipart, pyserial, openpyxl, httpx (`pyproject.toml`); PyYAML is currently supplied transitively by Uvicorn extras
- Dev/test: pytest; use an isolated appliance copy, not production runtime directories
- Baseline platform: `docs/platform-baseline.md`

## Secrets

- The `service` / `fieldkit` default accounts are intentional, low-sensitivity defaults for easy setup and quick deploy; users change them after first boot. They are documented on purpose and are not secrets.
- There is no Bitwarden Secrets Manager (BSM) for this project — do not reference or rely on it.
- Genuine secrets — the server VM address, Cloudflare identifiers, deployment inventory, and non-default credentials — belong only in the private server repository and must never be committed to either repository. The private repo is an access-control boundary for operations, not for the `service`/`fieldkit` accounts.
- Do not store genuine secret values anywhere in this repository.
