from pathlib import Path

import yaml


def test_device_api_contract_contains_update_report_and_sync_response():
    document = yaml.safe_load(Path("docs/fieldkit-server-api.openapi.yaml").read_text())
    paths = document["paths"]
    assert "/device/update-latest" in paths
    assert "/device/report-requested" in paths
    response = paths["/device/sync-results"]["post"]["responses"]["202"]
    assert response["content"]["application/json"]["schema"]["$ref"].endswith("/SyncResultsAccepted")


def test_transfer_and_provisioning_contracts_are_restrictive():
    transfer = Path("scripts/install_transfer_services.sh").read_text()
    provision = Path("scripts/provision_pi.sh").read_text()
    http = Path("scripts/install_export_http_mode.sh").read_text()
    assert "--create" not in transfer
    assert "write_enable=NO" in transfer
    assert "install -d -m 0700" in provision
    assert "tempfile.mkstemp" in provision and "os.fchmod" in provision and "0o600" in provision
    assert 'chmod 0600 "${SETTINGS_PATH}"' in provision
    sudoers = Path("deploy/sudoers/fieldkit-transfer").read_text()
    assert "/bin/bash /opt/fieldkit/scripts/install_export_http_mode.sh enable" in sudoers
    assert "/bin/bash /opt/fieldkit/scripts/install_export_http_mode.sh disable" in sudoers
    assert "os.replace(temp, path)" in provision
    assert "location ^~ /fieldkit" in http
    assert "proxy_pass http://127.0.0.1:8000" in http or "deploy/nginx/fieldkit.conf" in http
    assert "nginx -t && (systemctl reload nginx || systemctl restart nginx)" in http
    assert "rollback failed" in http
