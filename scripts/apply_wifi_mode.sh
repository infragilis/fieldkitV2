#!/usr/bin/env bash
set -euo pipefail

MODE=${1:-${MODE:-disabled}}
WIFI_INTERFACE=${2:-${WIFI_INTERFACE:-wlan0}}
WIFI_SSID=${3:-${WIFI_SSID:-fieldkit}}
WIFI_COUNTRY=${4:-${WIFI_COUNTRY:-US}}
WIFI_PASSWORD=${WIFI_PASSWORD:-}
CLIENT_SSID=${WIFI_SSID}
CLIENT_PASSWORD=${WIFI_PASSWORD}
if [[ ${MODE} == "ap" && -z ${WIFI_PASSWORD} ]]; then
  WIFI_PASSWORD=fieldkit
fi
if [[ ${MODE} == "ap" || ${MODE} == "client" ]]; then
  PASSWORD_INPUT=
  if IFS= read -r PASSWORD_INPUT; then
    WIFI_PASSWORD=${PASSWORD_INPUT}
  fi
  CLIENT_PASSWORD=${WIFI_PASSWORD}
fi
AP_ADDRESS=${AP_ADDRESS:-10.42.0.1/24}
AP_DHCP_START=${AP_DHCP_START:-10.42.0.10}
AP_DHCP_END=${AP_DHCP_END:-10.42.0.150}
AP_CHANNEL=${AP_CHANNEL:-6}
AP_CONFIG_DIR=${AP_CONFIG_DIR:-/etc/fieldkit/ap}
RESTORE_DNSMASQ=${RESTORE_DNSMASQ:-1}

if [[ ${EUID} -ne 0 ]]; then
  echo "Run as root."
  exit 1
fi

if ! command -v nmcli >/dev/null 2>&1; then
  echo "nmcli is required."
  exit 1
fi

if ! command -v ip >/dev/null 2>&1; then
  echo "iproute2 is required."
  exit 1
fi

ensure_ap_configs() {
  install -d -m 0700 "${AP_CONFIG_DIR}"
  local hostapd_tmp dnsmasq_tmp
  hostapd_tmp=$(mktemp "${AP_CONFIG_DIR}/hostapd.conf.XXXXXX")
  dnsmasq_tmp=$(mktemp "${AP_CONFIG_DIR}/dnsmasq.conf.XXXXXX")
  chmod 0600 "${hostapd_tmp}" "${dnsmasq_tmp}"
  cat >"${hostapd_tmp}" <<EOF
country_code=${WIFI_COUNTRY}
interface=${WIFI_INTERFACE}
driver=nl80211
ssid=${WIFI_SSID}
hw_mode=g
channel=${AP_CHANNEL}
ieee80211d=1
wmm_enabled=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_key_mgmt=WPA-PSK
rsn_pairwise=CCMP
wpa_passphrase=${WIFI_PASSWORD}
EOF
  cat >"${dnsmasq_tmp}" <<EOF
interface=${WIFI_INTERFACE}
bind-interfaces
domain-needed
bogus-priv
dhcp-authoritative
dhcp-range=${AP_DHCP_START},${AP_DHCP_END},255.255.255.0,12h
dhcp-option=option:router,${AP_ADDRESS%/*}
dhcp-option=option:dns-server,${AP_ADDRESS%/*}
port=53
listen-address=${AP_ADDRESS%/*}
EOF
  mv -f "${hostapd_tmp}" "${AP_CONFIG_DIR}/hostapd.conf"
  mv -f "${dnsmasq_tmp}" "${AP_CONFIG_DIR}/dnsmasq.conf"
}

stop_ap_services() {
  systemctl disable --now fieldkit-ap-hostapd >/dev/null 2>&1 || true
  systemctl disable --now fieldkit-ap-dnsmasq >/dev/null 2>&1 || true
}

disconnect_wifi_clients() {
  local active_connection
  active_connection=$(nmcli -g GENERAL.CONNECTION dev show "${WIFI_INTERFACE}" 2>/dev/null | head -n 1 || true)
  if [[ -n ${active_connection} && ${active_connection} != "--" ]]; then
    nmcli connection down "${active_connection}" >/dev/null 2>&1 || true
  fi
  nmcli device disconnect "${WIFI_INTERFACE}" >/dev/null 2>&1 || true
}

restore_networkmanager_control() {
  nmcli device set "${WIFI_INTERFACE}" managed yes >/dev/null 2>&1 || true
  nmcli general reload >/dev/null 2>&1 || true
  ip link set "${WIFI_INTERFACE}" up >/dev/null 2>&1 || true
  for _ in 1 2 3 4 5; do
    if ! nmcli -t -f DEVICE,STATE dev status 2>/dev/null | grep -q "^${WIFI_INTERFACE}:unmanaged"; then
      break
    fi
    sleep 1
    nmcli device set "${WIFI_INTERFACE}" managed yes >/dev/null 2>&1 || true
  done
}

take_networkmanager_offline() {
  disconnect_wifi_clients
  nmcli device set "${WIFI_INTERFACE}" managed no >/dev/null 2>&1 || true
}

configure_ap_link() {
  ip link set "${WIFI_INTERFACE}" down || true
  ip addr flush dev "${WIFI_INTERFACE}" || true
  ip link set "${WIFI_INTERFACE}" up
  ip addr add "${AP_ADDRESS}" dev "${WIFI_INTERFACE}"
}

clear_ap_link() {
  ip addr flush dev "${WIFI_INTERFACE}" || true
  ip link set "${WIFI_INTERFACE}" down || true
}

restart_system_dnsmasq_if_needed() {
  if [[ ${RESTORE_DNSMASQ} == "1" ]] && systemctl list-unit-files dnsmasq.service >/dev/null 2>&1; then
    systemctl start dnsmasq >/dev/null 2>&1 || true
  fi
}

start_ap_mode() {
  ensure_ap_configs
  systemctl stop dnsmasq >/dev/null 2>&1 || true
  take_networkmanager_offline
  configure_ap_link
  systemctl enable fieldkit-ap-dnsmasq fieldkit-ap-hostapd >/dev/null 2>&1 || true
  systemctl restart fieldkit-ap-dnsmasq
  systemctl restart fieldkit-ap-hostapd
  sleep 2
  systemctl is-active --quiet fieldkit-ap-dnsmasq
  systemctl is-active --quiet fieldkit-ap-hostapd
  ip -4 addr show dev "${WIFI_INTERFACE}" | grep -q "${AP_ADDRESS%/*}"
  echo "AP mode active on ${WIFI_INTERFACE} (${WIFI_SSID}, ${AP_ADDRESS})."
}

start_client_mode() {
  stop_ap_services
  clear_ap_link
  restore_networkmanager_control
  restart_system_dnsmasq_if_needed
  nmcli radio wifi on >/dev/null 2>&1 || true
  ip link set "${WIFI_INTERFACE}" up >/dev/null 2>&1 || true
  if [[ -n ${CLIENT_SSID} ]]; then
    if [[ -n ${CLIENT_PASSWORD} ]]; then
      # --ask reads the PSK from stdin, keeping it out of nmcli's argv.
      printf '%s\n' "${CLIENT_PASSWORD}" | nmcli --ask device wifi connect "${CLIENT_SSID}" ifname "${WIFI_INTERFACE}"
    else
      nmcli device wifi connect "${CLIENT_SSID}" ifname "${WIFI_INTERFACE}"
    fi
  else
    nmcli device connect "${WIFI_INTERFACE}" >/dev/null 2>&1 || true
  fi
  echo "Client mode restored on ${WIFI_INTERFACE}."
}

start_disabled_mode() {
  stop_ap_services
  clear_ap_link
  restore_networkmanager_control
  restart_system_dnsmasq_if_needed
  nmcli device disconnect "${WIFI_INTERFACE}" >/dev/null 2>&1 || true
  ip link set "${WIFI_INTERFACE}" down >/dev/null 2>&1 || true
  echo "Wi-Fi disabled on ${WIFI_INTERFACE}."
}

case "${MODE}" in
  ap)
    start_ap_mode
    ;;
  client)
    start_client_mode
    ;;
  disabled)
    start_disabled_mode
    ;;
  *)
    echo "Unsupported MODE=${MODE}"
    exit 1
    ;;
esac
