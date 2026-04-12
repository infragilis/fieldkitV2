# Brocade Fabric OS

Starter commands for Fibre Channel switches running Fabric OS.

## Common checks

1. `version`
2. `switchshow`
3. `switchstatusshow`
4. `fabricshow`
5. `nsshow`
6. `portshow <port>`
7. `porterrshow`
8. `cfgshow`
9. `alishow`
10. `errdump`

## Typical first actions

- Confirm fabric membership and principal switch behavior.
- Inspect port errors before assuming optics or cabling are good.
- Review zoning and aliases before making pathing changes.

## File transfer patterns from Fieldkit

- SCP: preferred when supported by the switch and workflow
- FTP/TFTP style workflows: use only when the exact maintenance procedure requires them
- HTTP delivery can still be useful for laptops or jump hosts supporting the fabric work

## Upgrade-oriented checks

1. `firmwareshow`
2. `firmwaredownloadstatus`
3. `slotshow`
4. `chassisshow`
5. `supportshow`

## Example workflow

1. Capture current state:
   `version`
   `firmwareshow`
   `switchshow`
2. Verify fabric and zoning stability:
   `fabricshow`
   `cfgshow`
3. Stage or reference the firmware from the Fieldkit-hosted transfer path.
4. Follow the Fabric OS firmware procedure for the target generation.
5. Validate after upgrade:
   `firmwareshow`
   `switchstatusshow`
   `errdump`

## Rollback cues

- Verify dual-partition or standby image state before upgrading.
- Avoid fabric-wide changes while principal-switch or ISL state is unstable.
- Keep `supportshow` output for any failed or partial upgrade.
