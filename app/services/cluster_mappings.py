"""Versioned label-to-field mappings for the NetApp cluster workbook import.

Keeping the mappings here (separate from the extraction and validation logic)
lets new fields and new workbook variants be added without touching the parser.
Bump ``MAPPING_VERSION`` whenever a mapping changes so that parsed results
record which mapping produced them.
"""

MAPPING_VERSION = 1

# Label aliases are matched against a normalized form of the workbook cell
# text (lower-cased, whitespace-collapsed). A cell matches an alias when its
# normalized text equals the alias, or starts with "<alias> " / "<alias>(" /
# "<alias>:" / "<alias>[".
#
# Extraction strategy per field:
#   span         - how many columns to the right of the label to scan.
#   gaps_allowed - whether empty cells between values are tolerated (used for
#                  multi-column layouts such as Site A / Site B), or stop at
#                  the first empty cell.
#   split        - extra in-cell separators so "192.0.2.11 , 192.0.2.12" yields
#                  two values.
FIELD_MAPPINGS: dict[str, dict] = {
    "cluster_name": {
        "aliases": ["cluster name", "clustername", "ontap cluster"],
        "span": 3,
        "gaps_allowed": True,
        "split": [],
    },
    "nodes": {
        "aliases": ["node name", "controller name"],
        "span": 8,
        "gaps_allowed": False,
        "split": [],
    },
    "dns_servers": {
        "aliases": ["dns server", "dns servers", "name server", "name servers"],
        "span": 8,
        "gaps_allowed": False,
        "split": [",", ";", "\n", " / "],
    },
    "ntp_servers": {
        "aliases": ["ntp server", "ntp servers", "time server", "time servers"],
        "span": 8,
        "gaps_allowed": False,
        "split": [",", ";", "\n", " / "],
    },
}

# Sheets searched for the labels, in order. The NetApp "Config Builder /
# AsBuilt" workbooks keep the cluster/network summary in this sheet.
PREFERRED_SHEETS = ["NodeClusterInfo"]

# When the preferred sheets are absent, fall back to scanning every sheet but
# bounded to avoid traversing huge reference tables.
FALLBACK_MAX_ROW = 2000
FALLBACK_MAX_COL = 40
