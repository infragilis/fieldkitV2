# Cluster Import (NetApp workbook → Ansible)

Fieldkit can import a customer-completed NetApp workbook, extract the cluster
configuration values needed to bootstrap a new cluster, present them for
review, and generate Ansible inputs for the `netapp.ontap` collection.

## Supported workbook formats

- Excel OpenXML workbooks: `.xlsx` and `.xlsm` (macro-enabled).
- Macros, formulas (beyond cached values), and external links are **never
  executed** — the file is read as data only.
- Content is validated by decoding, not by filename or client MIME type.
- Two NetApp "Config Builder / AsBuilt" layout variants are understood today:
  - **Standard** (single cluster, e.g. `AFF C30`): `Cluster Name` in one cell,
    `Node Name` row, `DNS Server` / `NTP Server` as multiple cells to the right.
  - **MetroCluster** (`MCC`, two sites): two cluster-name columns (Site A /
    Site B), four node names, DNS as a single comma-separated cell, and a
    free-text `Name: … / Address: …` NTP cell.

Extraction is **label-driven**, not coordinate-based, so other layouts that
share the same labels are also recognized.

## Current extracted fields

| Field | Label aliases | Notes |
|---|---|---|
| `cluster_name` | `Cluster Name`, `Clustername`, `ONTAP Cluster` | first match; extra matches are flagged `ambiguous` |
| `nodes` | `Node Name`, `Controller Name` | one or more, read across the row |
| `dns_servers` | `DNS Server(s)`, `Name Server(s)` | IP or hostname, comma-splitting supported |
| `ntp_servers` | `NTP Server(s)`, `Time Server(s)` | IP or hostname, `Name:`/`Address:` prefixes stripped |

Required for review: `cluster_name` and at least one `nodes` entry. DNS and NTP
are optional — a fresh ONTAP cluster can be provisioned first and its DNS/NTP
set afterwards.

## How to add another field or workbook mapping

All label rules live in `app/services/cluster_mappings.py` (versioned by
`MAPPING_VERSION`). To add a field:

1. Add an entry to `FIELD_MAPPINGS` with its `aliases`, `span`,
   `gaps_allowed`, and `split` separators.
2. Add the field to the `ClusterConfig` model in `app/core/models.py`.
3. Handle normalization/validation in `app/services/cluster_validation.py`.
4. Bump `MAPPING_VERSION`.

The extraction logic in `app/services/cluster_parser.py` is generic and does
not need to change for new fields.

## Missing inputs for a fresh-cluster run

The MVP extracts only naming and DNS/NTP. A real `netapp.ontap` deployment
also needs (and the generated playbook is flagged as a **draft** until these
are supplied):

- cluster management IP, netmask, gateway
- node management IPs (one per node)
- node serial numbers (one per node)
- ONTAP admin username/password (via Ansible Vault)
- ONTAP target version/image
- license keys (NLF)

## Previewing and safely running the generated automation

1. Upload a workbook on the **Cluster Import** page (drag-and-drop or picker).
2. Review and correct the extracted values; fix any flagged issues.
3. Click **Generate Ansible inputs** to produce:
   - `cluster_vars.yml` — deterministic variables (the reviewed values plus
     clearly-marked `CHANGE_ME` placeholders).
   - `deploy_cluster.yml` — a clearly-labelled **draft** playbook using
     `netapp.ontap.na_ontap_cluster`, `na_ontap_dns`, and `na_ontap_ntp`.

To run it safely once all inputs are available:

```bash
ansible-vault create group_vars/all/vault.yml   # store the admin password
# fill in the CHANGE_ME values in cluster_vars.yml
ansible-playbook --syntax-check deploy_cluster.yml   # validate
ansible-playbook --check deploy_cluster.yml          # dry-run
ansible-playbook deploy_cluster.yml                  # apply
```

The generated playbook is intentionally not runnable as-is; it is a draft
whose arguments should be verified against the installed collection
(`ansible-doc netapp.ontap.na_ontap_cluster`).

## Notes

- Uploaded workbooks are parsed in memory and **never persisted** to disk.
- Audit events (upload/parse/generate, with counts only — no customer values
  or credentials) are appended to `runtime/state/cluster-import-audit.log`.
- `openpyxl` is a new runtime dependency (`pyproject.toml`); install it into
  the appliance venv before deploying (`/opt/fieldkit/.venv/bin/pip install openpyxl`).
