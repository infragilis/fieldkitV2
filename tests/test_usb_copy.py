"""Copy-to-USB behaviour: path mapping, safety, and progress reporting."""

import pytest

from app.core.config import RuntimeSettings
from app.services.storage import StorageService, UsbNotMounted


def make_service(tmp_path, monkeypatch, usb=None) -> StorageService:
    settings = RuntimeSettings(content_root=tmp_path / "content", state_root=tmp_path / "state")
    service = StorageService(settings)
    monkeypatch.setattr(service, "_detect_usb_mount", lambda: usb)
    return service


def test_copy_file_preserves_library_folder(tmp_path, monkeypatch):
    usb = tmp_path / "usb"
    usb.mkdir()
    service = make_service(tmp_path, monkeypatch, usb=usb)
    source = service.library_paths()["data"] / "brocade" / "fw.bin"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_bytes(b"firmware")

    result = service.copy_to_usb("data", "brocade/fw.bin")

    assert result["destination"] == "brocade/fw.bin"
    assert (usb / "brocade" / "fw.bin").read_bytes() == b"firmware"


def test_copy_refuses_symlinked_usb_destination(tmp_path, monkeypatch):
    usb = tmp_path / "usb"
    usb.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (usb / "brocade").symlink_to(outside)
    service = make_service(tmp_path, monkeypatch, usb=usb)
    source = service.library_paths()["data"] / "brocade" / "fw.bin"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_bytes(b"firmware")

    with pytest.raises(ValueError):
        service.copy_to_usb("data", "brocade/fw.bin")

    assert not (outside / "fw.bin").exists()


def test_copy_ontap_file_lands_in_usb_root(tmp_path, monkeypatch):
    usb = tmp_path / "usb"
    usb.mkdir()
    service = make_service(tmp_path, monkeypatch, usb=usb)
    source = service.library_paths()["data"] / "ontap" / "image.tgz"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_bytes(b"ontap")

    result = service.copy_to_usb("data", "ontap/image.tgz")

    assert result["destination"] == "image.tgz"
    assert (usb / "image.tgz").read_bytes() == b"ontap"
    assert not (usb / "ontap").exists()


def test_copy_ontap_folder_flattens_into_root(tmp_path, monkeypatch):
    usb = tmp_path / "usb"
    usb.mkdir()
    service = make_service(tmp_path, monkeypatch, usb=usb)
    root = service.library_paths()["data"] / "ontap"
    (root / "nested").mkdir(parents=True, exist_ok=True)
    (root / "a.tgz").write_bytes(b"a")
    (root / "nested" / "b.tgz").write_bytes(b"b")

    result = service.copy_to_usb("data", "ontap")

    assert result["files"] == 2
    assert (usb / "a.tgz").read_bytes() == b"a"
    assert (usb / "nested" / "b.tgz").read_bytes() == b"b"


def test_copy_without_usb_is_refused(tmp_path, monkeypatch):
    service = make_service(tmp_path, monkeypatch, usb=None)
    source = service.library_paths()["data"] / "brocade" / "fw.bin"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_bytes(b"x")

    with pytest.raises(UsbNotMounted):
        service.copy_to_usb("data", "brocade/fw.bin")


def test_copy_reports_progress_and_replaces_existing(tmp_path, monkeypatch):
    usb = tmp_path / "usb"
    usb.mkdir()
    service = make_service(tmp_path, monkeypatch, usb=usb)
    source = service.library_paths()["data"] / "cisco" / "big.bin"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_bytes(b"new-content")
    existing = usb / "cisco" / "big.bin"
    existing.parent.mkdir(parents=True, exist_ok=True)
    existing.write_bytes(b"old")
    updates = []

    result = service.copy_to_usb("data", "cisco/big.bin", progress=updates.append)

    assert result["replaced"] == 1
    assert updates and updates[-1]["copied_bytes"] == len(b"new-content")
    assert existing.read_bytes() == b"new-content"


def test_copy_skips_hidden_files_and_refuses_empty_folder(tmp_path, monkeypatch):
    usb = tmp_path / "usb"
    usb.mkdir()
    service = make_service(tmp_path, monkeypatch, usb=usb)
    folder = service.library_paths()["personal"] / "empty"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / ".hidden").write_bytes(b"x")

    with pytest.raises(ValueError):
        service.copy_to_usb("personal", "empty")


def test_copy_refuses_usb_as_source(tmp_path, monkeypatch):
    usb = tmp_path / "usb"
    usb.mkdir()
    service = make_service(tmp_path, monkeypatch, usb=usb)
    with pytest.raises(ValueError):
        service.copy_to_usb("usb", "anything.bin")


def test_listing_marks_files_already_on_usb(tmp_path, monkeypatch):
    usb = tmp_path / "usb"
    usb.mkdir()
    service = make_service(tmp_path, monkeypatch, usb=usb)
    data = service.library_paths()["data"]
    (data / "brocade" / "fw.bin").write_bytes(b"fw")
    (data / "ontap" / "os.tgz").write_bytes(b"os")
    (usb / "brocade").mkdir(parents=True)
    (usb / "brocade" / "fw.bin").write_bytes(b"fw")
    (usb / "os.tgz").write_bytes(b"os")

    brocade = {item["path"]: item for item in service.list_library("data", "brocade")["items"]}
    assert brocade["brocade/fw.bin"]["on_usb"] is True
    # ONTAP maps to the USB root, so the marker follows the flattened path.
    ontap = {item["path"]: item for item in service.list_library("data", "ontap")["items"]}
    assert ontap["ontap/os.tgz"]["on_usb"] is True


def test_listing_not_on_usb_until_copied(tmp_path, monkeypatch):
    usb = tmp_path / "usb"
    usb.mkdir()
    service = make_service(tmp_path, monkeypatch, usb=usb)
    (service.library_paths()["data"] / "cisco" / "fw.bin").write_bytes(b"fw")

    items = {item["path"]: item for item in service.list_library("data", "cisco")["items"]}

    assert items["cisco/fw.bin"]["on_usb"] is False


def test_usb_files_are_deletable(tmp_path, monkeypatch):
    usb = tmp_path / "usb"
    usb.mkdir()
    service = make_service(tmp_path, monkeypatch, usb=usb)
    (usb / "stale.bin").write_bytes(b"x")

    service.delete_file("usb", "stale.bin")

    assert not (usb / "stale.bin").exists()
