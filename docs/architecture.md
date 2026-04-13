# Architecture Overview

This document is the technical companion to the user-facing README.

## Application Layout

- `app/main.py` serves the main HTML routes
- `app/api` contains HTTP and WebSocket routes
- `app/services` contains Pi-facing service logic such as storage, serial, networking, transfer services, password handling, and local shell access
- `app/static` contains frontend assets
- `runtime/content` stores user-visible files
- `runtime/state` stores mutable kit state such as settings and serial logs

## Main Runtime Areas

- `data` for built-in shared content
- `personal` for user uploads
- `usb` for mounted removable storage
- `serial-logs` for captured console sessions

## External Service Boundaries

- `fieldkit-web.service` runs the FastAPI app
- `nginx` provides the front end for HTTP and HTTPS
- SSH provides SCP access and the system account used by the local shell
- FTP and TFTP are optional transfer services managed from the Fieldkit UI
- NetworkManager handles appliance networking

## Notes

- The README is intentionally user-focused
- Deployment and operating steps stay in `docs/`
- Pi-specific implementation details should be documented here rather than expanding the main README
