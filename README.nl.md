# Fieldkit

Fieldkit is een Raspberry Pi-tool voor veldwerk aan netwerkapparatuur. Het biedt een lokale webinterface voor consoletoegang, bestanden, transferdiensten en beheer van het appliance.

Huidige applianceversie: **v0.1.7**. Cluster Import en Server Sync hebben amberkleurige
**beta**-labels in het menu.

## Serversynchronisatie En Bestanden

- Stel de server-URL en je apparaattoken in op **Server Sync** op het appliance.
  Synchronisatie start 10 minuten na het opstarten en daarna elk uur; **Sync now**
  start direct een controle. Downloads worden op grootte en checksum gecontroleerd.
- **`data/{cisco,ontap,brocade,efos,nvidia}`** bevat gedeelde leveranciersbestanden;
  **`personal`** is voor configuraties en gebruikersspecifieke bestanden.
- Op de **serverwebinterface** biedt **Data** een mapkiezer, downloads en
  **My sync subscriptions**. Kies je mappen en sla op. Alle kits met jouw token
  volgen die keuze; persoonlijke bestanden worden altijd gesynchroniseerd.
- Bestaande accounts behouden alle mappen tot ze dit aanpassen. Nieuwe accounts
  beginnen met alleen persoonlijke bestanden. Afmelden voor een map verwijdert
  geen eerder gedownloade bestanden van de kit.
- De server ondersteunt hervatbare uploads in delen van 8 MiB, met voortgang,
  snelheid, resterende tijd en opnieuw proberen/annuleren. Een upload meldt je
  niet automatisch aan voor de bijbehorende datamap.
- Op het **appliance** blijven lokale bestanden bereikbaar via **Files → data**
  en **Files → personal**; de mapabonnementen worden op de server beheerd.

Meer informatie: [Server Sync](docs/server-sync.md) en
[Cluster Import](docs/cluster-import.md) (Engels).

## Wat Fieldkit Doet

- Twee USB-seriele sessies met popupconsolevensters
- Lokale opslag in `data`, `personal`, `usb` en `serial-logs`
- Uploads en downloads via de browser
- Logging van seriele sessies voor latere download
- Gedeelde bestanden via HTTP
- Gedeelde bestanden via SCP
- FTP en TFTP kunnen indien nodig worden ingeschakeld
- Een lokale Pi-shell in de browser
- Leveranciersreferenties voor gebruik in het veld
- Meertalige webinterface en gelokaliseerde README-weergave

## Hardwareaanbevelingen

- Raspberry Pi 3 Model B of nieuwer
- Debian 13 (`trixie`) 64-bit
- Twee USB-serieeladapters of consolekabels als je beide poorten wilt gebruiken
- Een USB-stick als je verwisselbare lokale opslag wilt gebruiken
- Bekabeld ethernet aanbevolen voor setup, updates en AP-tests

## Opslagaanbeveling

Fieldkit bewaart uploads, exportbestanden en seriele sessielogs op het appliance zelf.

- Minimale aanbevolen microSD-grootte: `64 GB` met server-sync (bestanden bestaan dubbel)
- `32 GB` is voldoende voor kits zonder server-sync
- Gebruik meer opslag als je images, firmware of veel logs lokaal wilt bewaren

## Belangrijkste Functies

- Dashboard voor snelle toegang tot console, bestanden, documentatie en instellingen
- Instellingenpagina voor connectiviteit, transferdiensten, wachtwoordwijziging en seriele presets
- Bestandspagina voor `data`, `personal`, `usb` en `serial-logs`
- Raw exportbrowser op `/fieldkit`
- Browsershell op `/pi-shell`
- Lokale documentatie-index op `/kit-docs`
- Gelokaliseerde README-pagina op `/readme`

## Transferopties

Fieldkit kan gedeelde bestanden aanbieden via:

- HTTP
- SCP
- FTP
- TFTP

HTTP-export voor `/fieldkit/...` is standaard beschikbaar. FTP en TFTP kunnen indien nodig op de instellingenpagina worden ingeschakeld.

## Wi-Fi-Access-Point

Fieldkit kan een dedicated Wi-Fi-access-point draaien voor directe lokale toegang:

- SSID: `fieldkit`
- Wachtwoord: `fieldkit`

Gebruik bekabeld ethernet voor setup en herstel terwijl je AP-wijzigingen test.

## Standaardtoegang

De standaard SSH-login is `service` / `service`.

Wijzig dit direct op elke echte uitrol.

## Aanbevolen Platform

- Raspberry Pi 3 Model B of nieuwer
- Debian 13 (`trixie`) 64-bit
- Python 3.13
- NetworkManager
- OpenSSH server

## Documentatie

- [docs/pi-setup.md](docs/pi-setup.md)
- [docs/update-and-reload.md](docs/update-and-reload.md)
- [docs/golden-image-checklist.md](docs/golden-image-checklist.md)
- [docs/architecture.md](docs/architecture.md)

## Open Source

Fieldkit is open source en beschikbaar onder de MIT-licentie in [LICENSE](https://github.com/infragilis/fieldkitV2/blob/main/LICENSE).

Issues en featureverzoeken:

- <https://github.com/infragilis/fieldkitV2/issues>
