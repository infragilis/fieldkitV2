# Raspberry Pi Setup

This document describes how to prepare a Raspberry Pi to the minimum supported Fieldkit baseline before deploying the app.

## Minimum supported target

- Raspberry Pi 3 Model B or newer
- Debian 13 (`trixie`) 64-bit
- NetworkManager enabled
- `service` user available for Fieldkit operations

## Default SSH Access

The default appliance SSH login is `service` / `service`.

This should be treated as a temporary bootstrap credential and changed as soon as the kit is provisioned.

Reference baseline details are in [platform-baseline.md](platform-baseline.md).

## Base OS preparation

Start from a clean Debian 13 64-bit Raspberry Pi install with SSH access.

Update packages:

```bash
sudo apt-get update
sudo apt-get upgrade -y
```

Install the minimum package set:

```bash
sudo apt-get install -y \
  git \
  python3 \
  python3-venv \
  python3-pip \
  network-manager \
  openssh-server \
  hostapd \
  dnsmasq \
  tftpd-hpa \
  vsftpd \
  nginx \
  openssl
```

## Create the appliance user

If the `service` user does not exist yet:

```bash
sudo useradd -m -s /bin/bash service
echo 'service:service' | sudo chpasswd
sudo usermod -aG sudo,dialout,netdev,plugdev service
```

Change that default password immediately after initial access:

```bash
passwd service
```

## Set the hostname

```bash
sudo hostnamectl set-hostname fieldkit
```

Update `/etc/hosts` so sudo and local resolution stay clean:

```bash
sudo sed -i 's/127.0.1.1.*/127.0.1.1\tfieldkit/' /etc/hosts
```

## Enable NetworkManager

```bash
sudo systemctl enable NetworkManager
sudo systemctl disable systemd-networkd || true
sudo systemctl restart NetworkManager
```

## Clone the repo

Use the SSH remote if you have access:

```bash
git clone git@github.com:infragilis/fieldkitV2.git
cd fieldkitV2
```

If the repo remains private, the Pi will need a deploy key or user SSH key with access.

## Provision the runtime layout

From the repo root:

```bash
sudo FIELDKIT_ROOT=/opt/fieldkit \
  FIELDKIT_USER=service \
  FIELDKIT_PASS=service \
  FIELDKIT_HOSTNAME=fieldkit \
  bash scripts/provision_pi.sh
```

## Install transfer service support

This configures the shared export tree used by HTTP, TFTP, FTP, and SCP for `data`, `personal`, and `usb`, and installs the sudoers policy needed for the Settings page toggles. Plain HTTP export for `/fieldkit/...` is enabled by default. TFTP and FTP support are installed disabled by default and can be turned on later from the Settings page.

```bash
cd /opt/fieldkit
sudo bash scripts/install_transfer_services.sh
```
