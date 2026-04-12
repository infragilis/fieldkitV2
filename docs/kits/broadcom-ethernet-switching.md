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

## File transfer patterns from Fieldkit

- HTTP: use the platform CLI or Linux shell to fetch images or configs from `http://<fieldkit-ip>/data/`
- SCP: preferred when the NOS supports direct secure copy
- TFTP: keep as a low-friction recovery path for simple image loads

## Upgrade-oriented checks

1. `show boot`
2. `show system`
3. `show logging`
4. `show interfaces counters errors`
5. `show platform`

## Example workflow

1. Identify the NOS and platform:
   `show version`
   `show system`
2. Capture interface and environmental state:
   `show interfaces status`
   `show environment`
3. Fetch target software or config from Fieldkit.
4. Follow the NOS-specific install procedure.
5. Validate after reload:
   `show version`
   `show logging`
   `show interfaces status`

## Rollback cues

- Broadcom-based systems vary heavily by NOS, so keep the existing boot image and boot variables intact until validation is complete.
- If ASIC-level behavior looks wrong, collect CLI state first and use `bcm shell` only when normal CLI data is insufficient.
- Save logs before rebooting again after a failed image attempt.
