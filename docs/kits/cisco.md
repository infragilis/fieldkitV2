# Cisco

Starter commands for IOS, IOS-XE, and adjacent Cisco switching workflows.

## Common checks

1. `show version`
2. `show running-config`
3. `show startup-config`
4. `show interfaces status`
5. `show ip interface brief`
6. `show inventory`
7. `show logging`
8. `show cdp neighbors detail`
9. `show environment all`
10. `show boot`

## Typical first actions

- Confirm exact platform and software version before loading images.
- Check interface/link state and management reachability.
- Compare running and startup config before changes or reloads.

## File transfer patterns from Fieldkit

- HTTP: `copy http://<fieldkit-ip>/data/<image> flash:`
- SCP: `copy scp: flash:` when SCP access is available on the kit
- TFTP: `copy tftp: flash:` for simpler recovery or ROMMON-adjacent workflows

## Upgrade-oriented checks

1. `dir flash:`
2. `verify /md5 flash:<image>`
3. `show install summary`
4. `show boot`
5. `show reload`

## Example workflow

1. Capture baseline:
   `show version`
   `show running-config`
   `show boot`
2. Copy image from Fieldkit:
   `copy http://<fieldkit-ip>/data/<image> flash:`
3. Validate storage and image integrity:
   `dir flash:`
   `verify /md5 flash:<image>`
4. Set boot variables as required by the platform.
5. Save config:
   `write memory`
6. Re-check after reload:
   `show version`
   `show install summary`

## Rollback cues

- Keep the previous boot target present in flash until the new image is validated.
- Confirm startup config and boot variables before reload.
- If the switch comes up unexpectedly, inspect:
  `show boot`
  `show logging`
