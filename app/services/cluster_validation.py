"""Normalization and validation for extracted cluster configuration."""

import ipaddress
import re

from app.core.models import (
    ClusterConfig,
    ClusterSource,
    FieldIssue,
    FieldMatch,
    NodeConfig,
)

_HOSTNAME_LABEL = re.compile(r"^[A-Za-z0-9]([A-Za-z0-9-]{0,61}[A-Za-z0-9])?$")


def is_valid_hostname(value: str) -> bool:
    text = value.strip()
    if not text or len(text) > 253:
        return False
    for label in text.split("."):
        if not _HOSTNAME_LABEL.fullmatch(label):
            return False
    return True


def is_valid_ip(value: str) -> bool:
    try:
        ipaddress.ip_address(value.strip())
        return True
    except ValueError:
        return False


def classify_address(value: str) -> str:
    if is_valid_ip(value):
        return "ip"
    if is_valid_hostname(value):
        return "hostname"
    return "invalid"


def _dedupe_preserve_order(values: list[str]) -> tuple[list[str], list[str]]:
    seen: set[str] = set()
    clean: list[str] = []
    duplicates: list[str] = []
    for value in values:
        if value in seen:
            if value not in duplicates:
                duplicates.append(value)
            continue
        seen.add(value)
        clean.append(value)
    return clean, duplicates


def validate(
    matches: list[FieldMatch],
    filename: str,
    template: str,
    parser_version: int,
) -> tuple[ClusterConfig, list[FieldIssue]]:
    """Normalize raw matches into a ClusterConfig and field-level issues."""
    issues: list[FieldIssue] = []

    by_field: dict[str, list[FieldMatch]] = {field: [] for field in ("cluster_name", "nodes", "dns_servers", "ntp_servers")}
    for match in matches:
        if match.field in by_field:
            by_field[match.field].append(match)

    cluster_names, cluster_dupes = _dedupe_preserve_order(
        [m.value for m in by_field["cluster_name"]]
    )
    cluster_name = cluster_names[0] if cluster_names else None
    if not cluster_names:
        issues.append(FieldIssue(field="cluster_name", code="missing", message="Cluster name is required but was not found."))
    elif len(cluster_names) > 1:
        issues.append(
            FieldIssue(
                field="cluster_name",
                code="ambiguous",
                message=f"Multiple cluster names found ({', '.join(cluster_names)}). Using '{cluster_name}'.",
            )
        )
    elif not is_valid_hostname(cluster_name):
        issues.append(FieldIssue(field="cluster_name", code="invalid_hostname", message=f"'{cluster_name}' is not a valid cluster name."))

    nodes: list[NodeConfig] = []
    node_names, node_dupes = _dedupe_preserve_order([m.value for m in by_field["nodes"]])
    for match in by_field["nodes"]:
        if match.value in {n.name for n in nodes}:
            continue
        nodes.append(NodeConfig(name=match.value, location=match.location))
    for node in nodes:
        if not is_valid_hostname(node.name):
            issues.append(FieldIssue(field="nodes", code="invalid_hostname", message=f"Node name '{node.name}' is not valid."))
    if not nodes:
        issues.append(FieldIssue(field="nodes", code="missing", message="At least one node name is required but none were found."))
    for duplicate in node_dupes:
        issues.append(FieldIssue(field="nodes", code="duplicate", message=f"Duplicate node name '{duplicate}' was ignored."))

    dns_values = [m.value for m in by_field["dns_servers"]]
    dns_servers, dns_dupes = _dedupe_preserve_order(dns_values)
    for value in dns_servers:
        if classify_address(value) == "invalid":
            issues.append(FieldIssue(field="dns_servers", code="invalid_address", message=f"'{value}' is not a valid DNS server address."))
    for duplicate in dns_dupes:
        issues.append(FieldIssue(field="dns_servers", code="duplicate", message=f"Duplicate DNS server '{duplicate}' was ignored."))

    ntp_values = [m.value for m in by_field["ntp_servers"]]
    ntp_servers, ntp_dupes = _dedupe_preserve_order(ntp_values)
    for value in ntp_servers:
        if classify_address(value) == "invalid":
            issues.append(FieldIssue(field="ntp_servers", code="invalid_address", message=f"'{value}' is not a valid NTP server address."))
    for duplicate in ntp_dupes:
        issues.append(FieldIssue(field="ntp_servers", code="duplicate", message=f"Duplicate NTP server '{duplicate}' was ignored."))

    config = ClusterConfig(
        cluster_name=cluster_name,
        nodes=nodes,
        dns_servers=dns_servers,
        ntp_servers=ntp_servers,
        source=ClusterSource(filename=filename, parser_version=parser_version, template=template),
    )
    return config, issues
