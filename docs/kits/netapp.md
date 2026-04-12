# NetApp

Starter commands for ONTAP clusters and nodes.

## Common checks

1. `cluster show`
2. `version`
3. `system node show`
4. `network interface show`
5. `network port show`
6. `storage disk show`
7. `storage aggregate show`
8. `volume show`
9. `system health alert show`
10. `event log show -time >1h`

## Typical first actions

- Confirm cluster and node health before touching images or config.
- Check management and data LIF state.
- Verify disk and aggregate visibility before storage troubleshooting.

## Image transfer patterns from Fieldkit

- HTTP: `http://<fieldkit-ip>/data/<image>`
- SCP: copy from the Fieldkit user-hosted path when SCP serving is added
- TFTP: use for platforms or maintenance workflows that expect TFTP delivery

## Upgrade-oriented checks

1. `cluster image show`
2. `system node image show`
3. `storage failover show`
4. `cluster ring show`
5. `system health subsystem show`

## Example workflow

1. Verify health:
   `cluster show`
   `system health alert show`
2. Confirm current images:
   `cluster image show`
3. Copy or stage the target package through the preferred NetApp workflow.
4. Validate that both HA and cluster state are healthy before disruptive steps.
5. Re-check:
   `cluster image show`
   `event log show -time >1h`

## Rollback cues

- Do not proceed with disruptive image changes if cluster health, HA state, or networking is degraded.
- Keep current package names and prior image state noted before staging a new image.
- Re-check node image state and recent events immediately after any failed activation attempt.
