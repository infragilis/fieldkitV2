# Fieldkit

Fieldkit ist ein Raspberry-Pi-Werkzeug fuer den Feldeinsatz an Netzwerkgeraeten. Es bietet eine lokale Weboberflaeche fuer Konsole, Dateien, Transferdienste und Appliance-Verwaltung.

Aktuelle Appliance-Version: **v0.2.2**. Cluster Import und Server Sync tragen
bernsteinfarbene **beta**-Markierungen im Menue.

## Serversynchronisierung Und Dateien

- Server-URL und Geraetetoken auf der Appliance unter **Server Sync** eintragen.
  Die Pruefung startet 10 Minuten nach dem Booten und danach stuendlich;
  **Sync now** startet sie sofort. Downloads werden nach Groesse und Pruefsumme geprueft.
- **`data/{cisco,ontap,brocade,efos,nvidia}`** enthaelt gemeinsame Herstellerdateien;
  **`personal`** ist fuer Konfigurationen und benutzerspezifische Dateien bestimmt.
- In der **Server-Weboberflaeche** bietet **Data** Ordnerauswahl, Downloads und
  **My sync subscriptions**. Ordner auswaehlen und speichern. Alle Kits mit
  demselben Benutzertoken verwenden diese Auswahl; persoenliche Dateien bleiben enthalten.
- Bestehende Konten behalten alle Ordner bis zur Aenderung. Neue Konten starten
  nur mit persoenlichen Dateien. Abbestellte Ordner werden nicht von der Kit-Festplatte geloescht.
- Der Server unterstuetzt fortsetzbare Uploads in 8-MiB-Bloecken mit Fortschritt,
  Geschwindigkeit, Restzeit sowie Wiederholen/Abbrechen. Ein Upload aktiviert
  kein automatisches Ordnerabonnement.
- Auf der **Appliance** lokale Dateien ueber **Files → data** oder **Files → personal**
  oeffnen. Die Abonnements werden auf dem Server verwaltet.

Weitere Informationen: [Server Sync](docs/server-sync.md) und
[Cluster Import](docs/cluster-import.md) (Englisch).

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
- Raspberry Pi OS Lite (Trixie, Debian 13) 64-Bit
- Zwei USB-Seriell-Adapter oder Konsolenkabel fuer beide Ports
- Ein USB-Stick fuer wechselbaren lokalen Speicher
- Kabelgebundenes Ethernet fuer Einrichtung, Updates und AP-Tests empfohlen

## Speicher-Empfehlung

Fieldkit speichert Uploads, Exportdateien und serielle Sitzungslogs auf der Appliance selbst.

- Empfohlene Mindestgroesse der microSD-Karte: `64 GB` bei Server-Sync (Dateien existieren doppelt)
- `32 GB` reichen fuer Kits ohne Server-Sync
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
- Raspberry Pi OS Lite (Trixie, Debian 13) 64-Bit
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
