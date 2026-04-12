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
