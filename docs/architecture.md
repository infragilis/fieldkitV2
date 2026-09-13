# Architecture Overview

This document is the technical companion to the user-facing README.

## Application Layout

- `app/main.py` serves the main HTML routes
- `app/api` contains HTTP and WebSocket routes
- `app/services` contains Pi-facing service logic such as storage, serial, networking, transfer services, password handling, and local shell access
- `app/static` contains frontend assets
- `runtime/content` stores user-visible files
- `runtime/state` stores mutable kit state such as settings and serial logs
- `app/services/server_sync.py` performs streamed, verified server downloads; `server_sync_job.py` coordinates one background job and persists its last outcome

## Main Runtime Areas

- `data` for built-in shared content
- `personal` for user uploads
- `usb` for mounted removable storage
- `serial-logs` for captured console sessions

`data` contains the built-in `cisco`, `ontap`, `brocade`, `efos`, and `nvidia`
subdirectories. Files retain the relative path supplied by the server manifest;
Fieldkit does not infer a vendor from the filename. The Files page supports
nested-folder navigation.

## External Service Boundaries

- `fieldkit-web.service` runs the FastAPI app
- `nginx` provides the front end on HTTP port 80; Settings controls whether
  the `/fieldkit` export is available while the normal web UI remains served.
  The checked-in template uses a loopback-only HTTP upstream.
- SSH provides SCP access and the system account used by the local shell
- FTP and TFTP are optional transfer services managed from the Fieldkit UI
- NetworkManager handles normal client-side networking
- Dedicated `hostapd` and `dnsmasq` units provide the Fieldkit Wi-Fi AP mode
- `fieldkit-server-sync.timer` triggers a local API request 10 minutes after boot and hourly thereafter

## Server Integration

The public [device API contract](fieldkit-server-api.openapi.yaml) connects the
kit to the private `fieldkit-server` project. That project owns the server web
upload interface, access control, and file publication; this repository owns
the kit's download/sync client and local UI.

Sync runs independently of the browser. A start request returns HTTP 202;
the UI polls status for current phase/file/bytes, download ETA, and last outcome.
Files are downloaded to temporary files, checked for size/hash, atomically
replaced, and then mirrored to the transfer export tree. The current job
coordinator assumes the existing single Uvicorn worker. Details are in
[Server Sync](server-sync.md).

Cross-repository tasks require explicit user scope and each repository's own
startup/deployment instructions. Keep server implementation and private
operational details out of the public appliance repository.

## Notes

- The README is intentionally user-focused
- Deployment and operating steps stay in `docs/`
- Pi-specific implementation details should be documented here rather than expanding the main README
