# Fieldkit

Fieldkit ist eine Raspberry-Pi-Appliance fuer den technischen Feldeinsatz an Netzwerkgeraeten. Sie bietet:

- Eine Weboberflaeche fuer serielle Konsole, Dateitransfer, Konnektivitaetspruefung und Appliance-Einstellungen
- Zwei USB-Seriell-Konsolen mit getrennten Einstellungen und Popup-Fenstern
- Eine lokale Inhaltsbibliothek mit `data`, `personal`, `usb` und `serial-logs`
- Ein modulares Backend, damit Pi-spezifische Logik von der Webschicht getrennt bleibt

## Hardware-Hinweis

Der Konsolenzugriff erfordert USB-zu-Seriell-Kabel oder USB-Seriell-Adapter, die als `ttyUSB*` oder `ttyACM*` erscheinen.

USB-Gadget-Export, bei dem Fieldkit fuer ein anderes Geraet wie ein direkt angeschlossener USB-Stick wirkt, benoetigt ein OTG-faehiges USB-Device-Port-Modell. Die aktuelle Referenzbox, Raspberry Pi 3 Model B Rev 1.2, unterstuetzt das nicht.

## Standardzugang

Der Standard-SSH-Zugang ist `service` / `service`.

Dieses Fabrik-Standardkennwort muss auf echten Geraeten sofort geaendert werden.

## Open Source

Fieldkit ist Open Source und kann gemaess MIT-Lizenz in [LICENSE](https://github.com/infragilis/fieldkitV2/blob/main/LICENSE) verwendet, veraendert und weitergegeben werden.

## Fehler Und Funktionen

- <https://github.com/infragilis/fieldkitV2/issues>

## Aktueller Funktionsumfang

- FastAPI-Backend mit modularen Routern und Diensten
- Hauptdashboard fuer Konsole, Dokumentation und Uploads
- Seite `/settings` fuer Konnektivitaet, Netzwerk, Passwort und serielle Presets
- Seite `/files` fuer `data`, `personal`, `usb` und `serial-logs`
- Uploads in `personal` oder `usb`
- Schutz vor stillem Ueberschreiben bestehender Dateien
- Loeschaktionen fuer `personal` und `serial-logs`
- Automatische USB-Erkennung unter `/media/service`, `/media` und `/mnt`
- Ausblenden versteckter und macOS-Metadaten in Dateiansichten
- Lokale Hersteller-Referenznotizen in der Weboberflaeche
- Persistente Einstellungen fuer Ethernet, Wi-Fi und serielle Profile
- Schnelle Umschaltung zwischen `9600 8N1` und `115200 8N1`
- Automatische Erkennung von Seriell-Adaptern
- Seite `/serial-settings` fuer detaillierte serielle Konfiguration je Konsole
- Gemeinsamer `/fieldkit`-Exportbaum fuer HTTP, TFTP, FTP und SCP
- Schalter fuer HTTP-Export, TFTP und FTP; SCP bleibt ueber SSH verfuegbar
- Popup-Konsolen unter `/serial-console/0` und `/serial-console/1`
- Direkte Tastaturerfassung in Popup-Konsolen
- Zeitgestempelte Sitzungslogs unter `runtime/state/serial-logs`
- Reset-Aktionen fuer laufende Konsolensitzungen
- Dry-run-Netzwerkplanung fuer Hostname- und Ethernet-Aenderungen

Pi-spezifische Integrationen wie `hostapd`, `dnsmasq`, `nmcli`, `tftpd`, `vsftpd`, `ssh/scp` und serielles Streaming sind hinter Servicemodulen gekapselt.

## Weboberflaeche

Wichtige Routen:

- `/`
- `/settings`
- `/serial-settings`
- `/files`
- `/fieldkit`
- `/readme`
- `/kit-docs`

## Dateibibliotheken

Fieldkit stellt vier Bibliotheken ueber die Seite `Files` bereit:

- `data`
- `personal`
- `usb`
- `serial-logs`

Sie sind ausserdem verfuegbar ueber:

- HTTP unter `/fieldkit/data`, `/fieldkit/personal` und `/fieldkit/usb`
- FTP aus derselben Exportwurzel
- SCP unter `/opt/fieldkit/runtime/content/fieldkit/<library>/...`
- TFTP mit derselben Struktur nach Anwendung von `scripts/install_transfer_services.sh`

`serial-logs` gehoeren bewusst nicht zum gemeinsam exportierten Baum.

## Aktuelles USB-Verhalten

- Automatisch eingehangte Datentraeger unter `/media/service`, `/media` oder `/mnt` werden als `usb` verwendet
- Fieldkit verwendet den ersten passenden eingehangten Ordner, was fuer den typischen Ein-Stick-Fall gedacht ist
- Mehrfachlaufwerksauswahl, sichtbare Volumenlabels und automatisches Hot-Plug-Refresh fehlen noch

## Aktuelles Dateiverhalten

- Uploads nach `personal` und `usb` sind erlaubt
- Uploads nach `data` und `serial-logs` sind blockiert
- Doppelte Dateinamen erzeugen einen Konflikt statt zu ueberschreiben
- Loeschen ist fuer `personal` und `serial-logs` erlaubt
- `usb` bleibt beim Loeschen derzeit schreibgeschuetzt

## Lokal Starten

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
uvicorn app.main:app --reload
```

Dann `http://127.0.0.1:8000` oeffnen.

Wenn keine feste Geraetevorgabe gespeichert ist, weist Fieldkit den naechsten gefundenen `ttyUSB*`- oder `ttyACM*`-Adapter zu.

## Kit-Dokumentation

Lokale Referenznotizen liegen in `docs/kits` und sind ueber die Hauptseite sowie `/kit-docs` erreichbar.

Aktuelle Themen:

- `NetApp`
- `Cisco`
- `NVIDIA`
- `Brocade Fabric OS`
- `Broadcom Ethernet Switching`

## Mindestplattform

- Raspberry Pi 3 Model B oder neuer
- Debian 13 (`trixie`) 64 Bit
- Python 3.13
- NetworkManager / `nmcli`
- OpenSSH server

Referenzdetails: [docs/platform-baseline.md](docs/platform-baseline.md)

## Deployment-Dokumente

- [docs/pi-setup.md](docs/pi-setup.md)
- [docs/update-and-reload.md](docs/update-and-reload.md)
- [docs/golden-image-checklist.md](docs/golden-image-checklist.md)

## Aktuelle Einschraenkungen

- USB-Browsing verwendet den zuerst erkannten eingehangten Pfad unter `/media/service`, `/media` oder `/mnt`; Mehrfachauswahl fehlt
- Sichtbare USB-Labels und automatisches Hot-Plug-Refresh sind noch nicht vorhanden
- Serielle Profile bevorzugen einen passenden `device_hint`, sonst den naechsten `ttyUSB*` oder `ttyACM*`; stabile Identitaet ueber USB-Seriennummer oder Port-Topologie fehlt
- Passwortaenderung ist noch ein Backend-Platzhalter
- Netzwerkanwendung ist noch Dry-run statt echter Re-Konfiguration
- Ansible-Workflows vom Kit aus sind noch nicht umgesetzt

## Naechste Schritte

1. USB fuer mehrere Laufwerke, Labels und Live-Refresh erweitern
2. Mehr serielle Steuerungen wie Break und robustere Reconnect-Logik ergaenzen
3. Netzwerkaktionen an echte NetworkManager- oder systemd-networkd-Aenderungen anbinden
4. HTTP/TFTP/FTP-Workflows fuer Images und Firmware erweitern
5. Ansible-Ausfuehrung und NetApp-Runbooks hinzufuegen

## Deployment-Ressourcen

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
