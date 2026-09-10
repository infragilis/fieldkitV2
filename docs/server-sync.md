# Server Sync

The kit pulls files listed by the server into its local `data` and `personal`
libraries. Configure the server URL and a device token on **Server Sync**
(`/server-sync`). Leaving the token field blank when saving keeps the saved
token. `FIELDKIT_DEVICE_TOKEN` can override it for managed installations.

## Automatic and manual checks

- `fieldkit-server-sync.timer` starts a check **10 minutes after boot**, then
  **hourly** using `OnUnitActiveSec=1h`.
- The timer calls the kit's local API; the page does not need to be open.
- **Sync now** starts an immediate background check without changing the timer.
- Only one job runs at a time. If a scheduled/manual request arrives during a
  job, it returns that job's current status rather than starting another.
- Unconfigured automatic checks are skipped. Offline/failed checks are shown
  as failures; the next hourly check tries again, or use **Sync now**.
- Enabling the timer on an already-running kit more than 10 minutes after boot
  makes its first check immediately due. Later boots use the 10-minute delay.

## Progress and history

The sync page polls status once per second while running, and every 10 seconds
while idle. It shows the current stage/file, bytes downloaded, files checked,
elapsed time, and estimated remaining download time based on measured speed.
ETA is unavailable while checking files, publishing exports, awaiting an initial
transfer, or when progress has stalled. It is an estimate, not a guaranteed
completion time.

The last result includes start/end times, duration, manual/automatic trigger,
downloaded/unchanged/failed counts, errors, and the last successful time. A
bounded list of up to 200 per-file results is retained. Status is atomically
persisted in `runtime/state/server-sync-status.json` at start/end, not per chunk.
An unfinished persisted run is marked interrupted after a web-service restart.

Downloads are streamed into temporary files and verified against the manifest's
size and checksum before replacing an existing file. The transfer export mirror
is refreshed before finishing. No local files are deleted because they vanished
from a manifest.

## Data folders

The runtime creates these folders without moving existing content:

```text
runtime/content/data/
  ontap/
  bes/
  cisco/
  nvidia/
  fos/
```

The server manifest determines placement. For example, `library: data` and
`path: ontap/image.tgz` downloads to `runtime/content/data/ontap/image.tgz`.
Files still published with a root-level path stay at the root; the kit does not
guess a vendor from filenames. Server upload placement is configured separately
in the server project. The Files page supports opening folders and moving up a
level, including links such as `/files?library=data&path=ontap`.

## API

- `POST /api/server-sync/sync`: HTTP 202 with `started` and a job snapshot.
  Completion is asynchronous; older callers expecting the complete result in
  this response must poll status instead.
- `POST /api/server-sync/sync?trigger=scheduled`: same behavior, but an
  unconfigured kit returns `started: false, reason: not_configured`.
- `GET /api/server-sync/status`: configuration indicators, schedule intervals,
  `running`, `current_sync`, `last_sync`, and `last_success_at`.
- `PUT /api/server-sync/config`: save URL/token; rejected while a job is running.

The current job coordinator assumes the existing single Uvicorn worker. Do not
add multiple workers without a shared job/locking mechanism.

## Install / verify

Fresh installation installs/enables the timer through `install_systemd.sh` and
starts it after the web service in `install_fieldkit.sh`.

For a copy-deploy, copy the new service/timer units and app files, then on the Pi:

```bash
sudo install -m 0644 /opt/fieldkit/deploy/systemd/fieldkit-server-sync.service /etc/systemd/system/
sudo install -m 0644 /opt/fieldkit/deploy/systemd/fieldkit-server-sync.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl restart fieldkit-web.service
# Wait for the API to answer before enabling the timer on an already-booted kit.
curl -fsS http://127.0.0.1:8000/api/server-sync/status
sudo systemctl enable --now fieldkit-server-sync.timer
systemctl list-timers fieldkit-server-sync.timer
```

Use `systemctl status fieldkit-server-sync.timer` for actual timer state. The
schedule text on the page describes the installed policy, not proof a manually
disabled system timer is still enabled.
