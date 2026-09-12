from typing import Literal

from pydantic import BaseModel, Field, field_validator


class EthernetConfig(BaseModel):
    mode: Literal["static", "dhcp"] = "static"
    address: str = "192.168.200.120/24"
    gateway: str = ""
    dns: list[str] = Field(default_factory=list)
    interface: str = "eth0"


class WifiConfig(BaseModel):
    mode: Literal["ap", "client", "disabled"] = "ap"
    ssid: str = Field(default="fieldkit", max_length=32)
    password: str = Field(default="fieldkit", max_length=63)
    country_code: str = "US"

    @field_validator("ssid", "password")
    @classmethod
    def _reject_control_characters(cls, value: str) -> str:
        if any(ord(ch) < 32 or ord(ch) == 127 for ch in value):
            raise ValueError("must not contain control characters")
        return value

    @field_validator("country_code")
    @classmethod
    def _normalize_country(cls, value: str) -> str:
        value = value.strip().upper()
        if len(value) != 2 or not value.isalpha():
            raise ValueError("country_code must be two letters")
        return value


class SerialPortConfig(BaseModel):
    label: str
    device_hint: str
    baud_rate: int = 9600
    data_bits: int = 8
    parity: Literal["none", "even", "odd"] = "none"
    stop_bits: int = 1


class TransferServicesConfig(BaseModel):
    http_export_enabled: bool = True
    tftp_enabled: bool = False
    ftp_enabled: bool = False


class ServerSyncConfig(BaseModel):
    base_url: str = "https://fieldkit.infragilis.org"
    device_token: str = ""
    prune: bool = False


class AppSettingsPayload(BaseModel):
    hostname: str = Field(
        default="fieldkit",
        max_length=63,
        pattern=r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?$",
    )
    ethernet: EthernetConfig = Field(default_factory=EthernetConfig)
    wifi: WifiConfig = Field(default_factory=WifiConfig)
    serial_ports: list[SerialPortConfig] = Field(
        default_factory=lambda: [
            SerialPortConfig(label="Console 1", device_hint=""),
            SerialPortConfig(label="Console 2", device_hint=""),
        ]
    )
    transfer_services: TransferServicesConfig = Field(default_factory=TransferServicesConfig)
    server_sync: ServerSyncConfig = Field(default_factory=ServerSyncConfig)


class ApplyResult(BaseModel):
    applied: bool
    dry_run: bool
    commands: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class CellLocation(BaseModel):
    sheet: str
    cell: str


class NodeConfig(BaseModel):
    name: str
    location: CellLocation | None = None


class ClusterSource(BaseModel):
    filename: str
    parser_version: int = 1
    template: str = "unknown"


class ClusterConfig(BaseModel):
    schema_version: int = 1
    cluster_name: str | None = None
    nodes: list[NodeConfig] = Field(default_factory=list)
    dns_servers: list[str] = Field(default_factory=list)
    ntp_servers: list[str] = Field(default_factory=list)
    source: ClusterSource


class FieldMatch(BaseModel):
    field: str
    value: str
    label: str
    alias: str
    location: CellLocation


class FieldIssue(BaseModel):
    field: str
    code: str
    message: str


class ParseResult(BaseModel):
    config: ClusterConfig
    matches: list[FieldMatch] = Field(default_factory=list)
    issues: list[FieldIssue] = Field(default_factory=list)


class GeneratedAnsibleFile(BaseModel):
    name: str
    content: str


class AnsibleGeneration(BaseModel):
    draft: bool
    variables: GeneratedAnsibleFile
    playbook: GeneratedAnsibleFile
    required_inputs: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
