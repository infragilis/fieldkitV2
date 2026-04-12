from pathlib import Path


DOCS_DIR = Path("docs/kits")

TOPICS = {
    "netapp": "NetApp",
    "cisco": "Cisco",
    "nvidia": "NVIDIA",
    "brocade-fabric-os": "Brocade Fabric OS",
    "broadcom-ethernet-switching": "Broadcom Ethernet Switching",
}


def list_topics() -> list[dict]:
    return [{"slug": slug, "title": title} for slug, title in TOPICS.items()]


def topic_path(slug: str) -> Path | None:
    if slug not in TOPICS:
        return None
    path = DOCS_DIR / f"{slug}.md"
    return path if path.exists() else None
