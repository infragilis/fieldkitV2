# Broadcom Ethernet Switching

Starter commands for Broadcom-based switch platforms. Exact command sets vary by NOS, so these focus on common operational checks and SDK-shell workflows when available.

## Common checks

1. `show version`
2. `show interfaces status`
3. `show vlan`
4. `show mac address-table`
5. `show lldp neighbors`
6. `show logging`
7. `show environment`
8. `bcm shell`
9. `ps`
10. `ip -br addr`

## Typical first actions

- Identify the NOS first; Broadcom silicon alone does not define the CLI.
- Use the normal switch CLI for state checks before dropping into SDK shell tools.
- Capture platform, ASIC, and port-mapping context before low-level debugging.
