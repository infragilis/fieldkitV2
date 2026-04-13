# Fieldkit

Fieldkit ist ein Raspberry-Pi-Werkzeug fuer den Feldeinsatz an Netzwerkgeraeten. Es bietet eine lokale Weboberflaeche fuer Konsole, Dateien, Transferdienste und Appliance-Verwaltung.

## Was Fieldkit Bietet

- Zwei USB-Seriell-Sitzungen mit Popup-Konsolenfenstern
- Lokale Dateien in `data`, `personal`, `usb` und `serial-logs`
- Uploads und Downloads direkt im Browser
- Protokollierung von Seriell-Sitzungen fuer den spaeteren Download
- Gemeinsame Dateien ueber HTTP
- Gemeinsame Dateien ueber SCP
- FTP und TFTP koennen bei Bedarf aktiviert werden
- Eine lokale Pi-Shell im Browser
- Hersteller-Referenznotizen fuer den Feldeinsatz
- Mehrsprachige Weboberflaeche und lokalisierte README-Ansicht

## Hardware-Empfehlungen

- Raspberry Pi 3 Model B oder neuer
- Debian 13 (`trixie`) 64-Bit
- Zwei USB-Seriell-Adapter oder Konsolenkabel fuer beide Ports
- Ein USB-Stick fuer wechselbaren lokalen Speicher
- Kabelgebundenes Ethernet fuer Einrichtung, Updates und AP-Tests empfohlen

## Speicher-Empfehlung

Fieldkit speichert Uploads, Exportdateien und serielle Sitzungslogs auf der Appliance selbst.

- Empfohlene Mindestgroesse der microSD-Karte: `32 GB`
- Mehr Speicher ist sinnvoll, wenn Images, Firmware oder viele Logs auf dem Kit bleiben sollen

## Hauptfunktionen

- Dashboard fuer schnellen Zugriff auf Konsole, Dateien, Dokumentation und Einstellungen
- Einstellungsseite fuer Konnektivitaet, Transferdienste, Passwortaenderung und serielle Presets
- Dateiseite fuer `data`, `personal`, `usb` und `serial-logs`
- Rohexport-Browser unter `/fieldkit`
- Browser-Shell unter `/pi-shell`
- Lokaler Dokumentationsindex unter `/kit-docs`
- Lokalisierte README-Ansicht unter `/readme`

## Transferoptionen

Fieldkit kann gemeinsame Dateien bereitstellen ueber:

- HTTP
- SCP
- FTP
- TFTP

HTTP-Export fuer `/fieldkit/...` ist standardmaessig verfuegbar. FTP und TFTP koennen bei Bedarf auf der Einstellungsseite aktiviert werden.

## Wi-Fi-Access-Point

Fieldkit kann einen dedizierten Wi-Fi-Access-Point fuer direkten lokalen Zugriff bereitstellen:

- SSID: `fieldkit`
- Passwort: `fieldkit`

Fuer Einrichtung und Wiederherstellung waehrend AP-Tests sollte kabelgebundenes Ethernet verwendet werden.

## Standardzugang

Der Standard-SSH-Zugang ist `service` / `service`.

Dieses Kennwort sollte bei jeder echten Bereitstellung sofort geaendert werden.

## Empfohlene Plattform

- Raspberry Pi 3 Model B oder neuer
- Debian 13 (`trixie`) 64-Bit
- Python 3.13
- NetworkManager
- OpenSSH server

## Dokumentation

- [docs/pi-setup.md](docs/pi-setup.md)
- [docs/update-and-reload.md](docs/update-and-reload.md)
- [docs/golden-image-checklist.md](docs/golden-image-checklist.md)
- [docs/architecture.md](docs/architecture.md)

## Open Source

Fieldkit ist Open Source und unter der MIT-Lizenz in [LICENSE](https://github.com/infragilis/fieldkitV2/blob/main/LICENSE) verfuegbar.

Fehler und Funktionswuensche:

- <https://github.com/infragilis/fieldkitV2/issues>
