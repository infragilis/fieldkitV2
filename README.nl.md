# Fieldkit

Fieldkit is een Raspberry Pi-appliance voor veldservice aan netwerkapparatuur. Het biedt:

- Een webinterface voor seriele console, bestandsoverdracht, connectiviteitscontrole en apparaatinstellingen
- Twee USB-seriele console-eindpunten met eigen instellingen en popupvensters
- Een lokale inhoudsbibliotheek met `data`, `personal`, `usb` en `serial-logs`
- Een modulaire backend zodat Pi-specifieke logica gescheiden blijft van de weblayer

## Hardwareopmerking

Consoletoegang vereist USB-naar-serieel-kabels of USB-serieeladapters die verschijnen als `ttyUSB*` of `ttyACM*`.

USB gadget-export, waarbij Fieldkit zich voor een ander apparaat gedraagt als een rechtstreeks aangesloten USB-stick, vereist een Raspberry Pi met OTG-geschikte USB device-modus. De huidige referentiebox, een Raspberry Pi 3 Model B Rev 1.2, ondersteunt dit niet.

## Standaardtoegang

De standaard SSH-login is `service` / `service`.

Wijzig dit standaardwachtwoord direct op echte systemen.

## Open Source

Fieldkit is open source en beschikbaar onder de MIT-licentie in [LICENSE](https://github.com/infragilis/fieldkitV2/blob/main/LICENSE).

## Problemen En Functies

- <https://github.com/infragilis/fieldkitV2/issues>

## Huidige Functionaliteit

- FastAPI-backend met modulaire routers en services
- Hoofddashboard voor console, documentatie en uploads
- `/settings` voor connectiviteit, netwerk, wachtwoord en seriele presets
- `/files` voor `data`, `personal`, `usb` en `serial-logs`
- Uploads naar `personal` en `usb`
- Bescherming tegen stil overschrijven van bestaande bestanden
- Verwijderen voor `personal` en `serial-logs`
- Automatische USB-detectie onder `/media/service`, `/media` en `/mnt`
- Verbergen van verborgen en macOS-metadatabestanden in de bestandsbrowser
- Lokale leveranciersnotities in de webinterface
- Persistente instellingen voor ethernet, Wi-Fi en seriele profielen
- Snelle omschakeling tussen `9600 8N1` en `115200 8N1`
- Automatische detectie van seriele adapters
- `/serial-settings` voor uitgebreide per-console-instellingen
- Een gedeelde `/fieldkit` exportboom voor HTTP, TFTP, FTP en SCP
- Schakelaars voor plain HTTP-export, TFTP en FTP; SCP blijft beschikbaar via SSH
- Popupconsolevensters op `/serial-console/0` en `/serial-console/1`
- Directe toetsenbordinvoer in popupconsoles
- Tijdgestempelde logs in `runtime/state/serial-logs`
- Resetacties voor actieve consolesessies
- Dry-run netwerkplanning

## Webinterface

Belangrijkste routes:

- `/`
- `/settings`
- `/serial-settings`
- `/files`
- `/fieldkit`
- `/readme`
- `/kit-docs`

## Bestandsbibliotheken

Fieldkit toont vier bibliotheken op de pagina `Files`:

- `data`
- `personal`
- `usb`
- `serial-logs`

Deze zijn ook beschikbaar via:

- HTTP op `/fieldkit/data`, `/fieldkit/personal` en `/fieldkit/usb`
- FTP vanuit dezelfde exportroot
- SCP op `/opt/fieldkit/runtime/content/fieldkit/<library>/...`
- TFTP met dezelfde structuur na `scripts/install_transfer_services.sh`

`serial-logs` maken bewust geen deel uit van de gedeelde exportboom.

## Huidig USB-Gedrag

- Als verwisselbare opslag automatisch wordt gemount onder `/media/service`, `/media` of `/mnt`, gebruikt Fieldkit die mount als `usb`
- Fieldkit kiest het eerste passende gemounte pad dat het vindt; dat werkt het best voor het gebruikelijke geval met een enkele USB-stick
- Selectie van meerdere schijven, zichtbare volumelabels en automatische hot-plug-refresh zijn nog niet aanwezig

## Huidig Bestandsgedrag

- Uploads naar `personal` en `usb` zijn toegestaan
- Uploads naar `data` en `serial-logs` zijn geblokkeerd
- Dubbele bestandsnamen geven een conflict in plaats van overschrijven
- Verwijderen is toegestaan voor `personal` en `serial-logs`
- `usb` wordt voor verwijderen nog als alleen-lezen behandeld

## Lokaal Draaien

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000`.

## Kitdocumentatie

Lokale leveranciersreferenties staan in `docs/kits` en zijn bereikbaar via de hoofdpagina en via `/kit-docs`.

Onderwerpen:

- `NetApp`
- `Cisco`
- `NVIDIA`
- `Brocade Fabric OS`
- `Broadcom Ethernet Switching`

## Minimale Ondersteunde Platform

- Raspberry Pi 3 Model B of nieuwer
- Debian 13 (`trixie`) 64-bit
- Python 3.13
- NetworkManager / `nmcli`
- OpenSSH server

Referentieplatform: [docs/platform-baseline.md](docs/platform-baseline.md)

## Deploydocumenten

- [docs/pi-setup.md](docs/pi-setup.md)
- [docs/update-and-reload.md](docs/update-and-reload.md)
- [docs/golden-image-checklist.md](docs/golden-image-checklist.md)

## Huidige Beperkingen

- USB-browsing gebruikt het eerste gedetecteerde gemounte pad onder `/media/service`, `/media` of `/mnt`; selectie van meerdere schijven ontbreekt
- Zichtbare USB-volumelabels en automatische hot-plug-refresh zijn nog niet geimplementeerd
- Seriele profielen gebruiken bij voorkeur een passende `device_hint`, anders de volgende `ttyUSB*` of `ttyACM*`; stabiele identiteit via USB-serienummer of poorttopologie ontbreekt
- Wachtwoordwijziging is nog een backend-placeholder
- Netwerktoepassing is nog dry-run in plaats van echte herconfiguratie
- Ansible-workflows vanaf de kit zijn nog niet geimplementeerd

## Volgende Stappen

1. USB-afhandeling verbeteren voor meerdere schijven, labels en live refresh
2. Rijkere seriele bediening toevoegen zoals break en betere reconnect-status
3. Netwerkacties koppelen aan echte wijzigingen via NetworkManager of systemd-networkd
4. HTTP/TFTP/FTP-workflows uitbreiden voor images en firmware
5. Ansible-uitvoering en NetApp-runbooks toevoegen

## Deploymiddelen

- [scripts/provision_pi.sh](scripts/provision_pi.sh)
- [scripts/install_systemd.sh](scripts/install_systemd.sh)
- [scripts/install_transfer_services.sh](scripts/install_transfer_services.sh)
- [scripts/smoke_test_appliance.sh](scripts/smoke_test_appliance.sh)
- [scripts/install_nginx.sh](scripts/install_nginx.sh)
- [scripts/install_https_self_signed.sh](scripts/install_https_self_signed.sh)
- [deploy/systemd/fieldkit-web.service](deploy/systemd/fieldkit-web.service)
- [deploy/nginx/fieldkit.conf](deploy/nginx/fieldkit.conf)
- [deploy/nginx/fieldkit-ssl.conf](deploy/nginx/fieldkit-ssl.conf)
- [docs/https-self-signed.md](docs/https-self-signed.md)
