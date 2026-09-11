# Server Sync

The kit pulls files listed by the server into its local `data` and `personal`
libraries. Configure the server URL and a device token on **Server Sync**
(`/server-sync`). Leaving the token field blank when saving keeps the saved
token. `FIELDKIT_DEVICE_TOKEN` can override it for managed installations.

The main shared vendor structure is **`data/{cisco,ontap,brocade,efos,nvidia}`**, for
software, firmware and reference files. **`personal`** is for configuration files
and other user-specific content. Select **Shared data** when uploading vendor
files to the server; it is the default for users with shared-data upload permission.
The selected library and folder determine where files appear on the kit.

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

On the **server webfront**, open **Data**, then choose a folder from the picker
to view its contents and download files. This server page also contains **My sync
subscriptions**. On the appliance, use **Files → data** or **Files → personal**
to browse downloaded files; folder links and **Up one level** handle navigation.

The runtime creates these folders without moving existing content:

```text
runtime/content/data/
  cisco/
  ontap/
  brocade/
  efos/
  nvidia/
```

The server manifest determines placement. For example, `library: data` and
`path: ontap/image.tgz` downloads to `runtime/content/data/ontap/image.tgz`.
Files still published with a root-level path stay at the root; the kit does not
guess a vendor from filenames. Server upload placement is configured separately
in the server project. The Files page supports opening folders and moving up a
level, including links such as `/files?library=data&path=ontap`.

## Subscribe to the server folders you need

In the server webfront's **Data → My sync subscriptions**, turn off **Sync all
current and future data folders** to choose individual folders, then click
**Save subscriptions**. The next scheduled check or **Sync now** uses that selection.

- Choices apply to all kits using that server user's device token.
- Personal files always sync. Selected top-level data folders include their
  descendants. Root data files have a separate checkbox.
- Select none for personal-only sync. The all-folder option includes future data
  folders too.
- Existing users retain all-folder behavior until they change it. New accounts
  start with no data subscriptions and choose their folders explicitly.
- Uploading a shared file does not subscribe a user automatically.
- Already-downloaded files remain on the kit after unsubscribing. Changing a
  selection during a running sync takes full effect at the next manifest check.

Subscriptions are implemented by the server's per-user manifest filtering. No
appliance token change or new client configuration is required. Server browsing
and manual downloads remain available independently of automatic sync choices.

## Uploading large files to the server

The server dashboard supports resumable uploads in 8 MiB chunks, with upload
progress, transferred bytes, speed/ETA, retry/cancel, and an explicit verified
completion result. Choose the library and optional relative folder (for example,
`ontap`) before uploading. Shared-data upload requires the server account's
permission.

After an interruption, use **Retry / resume**. If the page was reopened, reselect
the original file first. Pending uploads are retained for seven days; the browser
remembers one pending upload per signed-in user. Files become visible to kit sync
only after the server verifies all uploaded bytes and publishes the complete file.
Server-upload progress and the kit's subsequent download progress are separate.

The server implementation and upload API are documented in the private server
repository's `UPLOADS.md`. The kit continues to use the same device API contract.

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

## Sync window and pruning

The server limits each kit's manifest with a per-user **sync window** (newest
N files per subscribed data folder, default 5) plus per-file **pin/exclude**
overrides. Personal files are always included.

Kits that need to stay small can enable **Remove synced files no longer
offered by the server** on the Server Sync page (opt-in, stored in
`settings.json` as `server_sync.prune`). With pruning enabled the kit keeps a
managed-files list in `runtime/state/server-sync-managed.json`: files it
downloaded (or confirmed present) from `data/` are removed together with their
export-mirror copies when they disappear from the manifest. User-placed files
and personal content are never touched.

## Storage planning and the disk-space check

Synced files exist twice on the kit — the local library and the HTTP export
mirror — so plan storage accordingly: a **64 GB microSD card is the minimum
for kits that use Server Sync**; 32 GB remains fine for kits that do not.

Before downloading anything, the sync estimates the space the library, the
export mirror, the largest in-flight file and a safety margin will need and
compares it against the free space. When it does not fit, the sync fails fast
with a clear "Not enough disk space" error that points at the server Data
page, and nothing is downloaded. Pruning runs before this check, so shrinking
the sync window on the server lets a full kit recover on its next sync.
