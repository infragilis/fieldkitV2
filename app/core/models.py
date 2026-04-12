from typing import Literal

from pydantic import BaseModel, Field


class EthernetConfig(BaseModel):
    mode: Literal["static", "dhcp"] = "static"
    address: str = "192.168.200.120/24"
    gateway: str = ""
    dns: list[str] = Field(default_factory=list)
    interface: str = "eth0"


class WifiConfig(BaseModel):
    mode: Literal["ap", "client", "disabled"] = "disabled"
    ssid: str = ""
    password: str = ""
    country_code: str = "US"


class SerialPortConfig(BaseModel):
    label: str
    device_hint: str
    baud_rate: int = 9600
    data_bits: int = 8
    parity: Literal["none", "even", "odd"] = "none"
    stop_bits: int = 1


class AppSettingsPayload(BaseModel):
    hostname: str = "fieldkit"
    ethernet: EthernetConfig = Field(default_factory=EthernetConfig)
    wifi: WifiConfig = Field(default_factory=WifiConfig)
    serial_ports: list[SerialPortConfig] = Field(
        default_factory=lambda: [
            SerialPortConfig(label="Console 1", device_hint=""),
            SerialPortConfig(label="Console 2", device_hint=""),
        ]
    )


class ApplyResult(BaseModel):
    applied: bool
    dry_run: bool
    commands: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
