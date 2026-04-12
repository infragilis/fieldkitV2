# NVIDIA

Starter commands for NVIDIA Ethernet switching environments, commonly Cumulus Linux based.

## Common checks

1. `nv show system`
2. `nv show interface`
3. `nv show platform`
4. `nv show bridge domain`
5. `nv show vlan`
6. `nv show vrf`
7. `ip -br addr`
8. `ip route`
9. `cl-support`
10. `journalctl -xe`

## Typical first actions

- Identify whether the box is NVUE-managed and whether config changes should use `nv`.
- Confirm management IP, platform, and switchd-related health.
- Collect `cl-support` early when dealing with escalations.

## File transfer patterns from Fieldkit

- HTTP: use `curl` or `wget` against `http://<fieldkit-ip>/data/<image-or-config>`
- SCP: copy from Fieldkit once SCP service paths are enabled
- Browser: use the Fieldkit UI from the management network to locate exact filenames

## Upgrade-oriented checks

1. `nv show system image`
2. `nv show system`
3. `systemctl status switchd`
4. `dpkg -l | grep -i cumulus`
5. `uname -a`

## Example workflow

1. Capture baseline:
   `nv show system`
   `nv show interface`
2. Pull the image or package from Fieldkit:
   `wget http://<fieldkit-ip>/data/<image>`
3. Validate platform and package compatibility.
4. Apply according to the NOS method in use.
5. Re-check:
   `nv show system`
   `systemctl status switchd`
   `journalctl -u switchd -n 100`

## Rollback cues

- Confirm whether rollback is package-based, filesystem-based, or NOS-specific before proceeding.
- Save `cl-support` before and after any failed upgrade.
- If interfaces do not recover, inspect switchd and platform logs before repeating the change.
