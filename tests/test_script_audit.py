from pathlib import Path


ROOT = Path(__file__).parents[1]


def read(name):
    return (ROOT / "scripts" / name).read_text()


def test_wifi_script_uses_atomic_restricted_configs_and_stdin_password():
    text = read("apply_wifi_mode.sh")
    assert 'install -d -m 0700 "${AP_CONFIG_DIR}"' in text
    assert 'chmod 0600 "${hostapd_tmp}" "${dnsmasq_tmp}"' in text
    assert 'IFS= read -r PASSWORD_INPUT' in text
    assert 'WIFI_PASSWORD=fieldkit' in text
    assert 'if IFS= read -r PASSWORD_INPUT; then' in text
    assert 'printf \'%s\\n\' "${CLIENT_PASSWORD}" | nmcli --ask' in text


def test_password_script_does_not_take_password_argv():
    text = read("change_password.sh")
    assert "CURRENT_PASSWORD=${2" not in text
    assert "NEW_PASSWORD=${3" not in text
    assert "read -r CURRENT_PASSWORD" in text


def test_install_roots_and_update_locking_are_hardened():
    assert 'FIELDKIT_ROOT} != "/opt/fieldkit"' in read("install_fieldkit.sh")
    assert 'FIELDKIT_ROOT} != "/opt/fieldkit"' in read("install_systemd.sh")
    text = read("update_appliance.sh")
    assert 'mkdir -p "${STATE_DIR}"' in text
    assert 'exec 9>"${LOCK_FILE}"' in text
    assert "flock -n 9" in text
    assert "--connect-timeout 10" in text and "--max-time 300" in text


def test_startup_wrapper_uses_new_wifi_contract():
    text = read("apply_startup_network_mode.sh")
    assert '<<<"${WIFI_PASSWORD:-fieldkit}"' in text
    assert '<<<"${WIFI_PASSWORD:-}"' in text
    assert '"${WIFI_PASSWORD:-fieldkit}"' not in text.split("ap)", 1)[1].split(";;", 1)[0].split("<<<", 1)[0]
