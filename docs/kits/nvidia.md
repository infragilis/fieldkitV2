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
