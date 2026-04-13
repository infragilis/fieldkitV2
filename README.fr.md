# Fieldkit

Fieldkit est une appliance Raspberry Pi pour les interventions terrain sur des equipements reseau. Elle fournit :

- Une interface web pour la console serie, le transfert de fichiers, la verification reseau et les parametres de l'appliance
- Deux consoles serie USB avec parametres independants et fenetres popup
- Une bibliotheque locale divisee en `data`, `personal`, `usb` et `serial-logs`
- Un backend modulaire afin d'isoler l'integration specifique au Pi de la couche web

## Note Materielle

L'acces console necessite des cables USB-serie ou des adaptateurs USB serie presentes en `ttyUSB*` ou `ttyACM*`.

L'export USB gadget, ou Fieldkit apparait a un autre appareil comme une cle USB directement branchee, exige un modele Raspberry Pi avec port OTG compatible mode device. La reference actuelle, Raspberry Pi 3 Model B Rev 1.2, ne le prend pas en charge.

## Acces Par Defaut

Le login SSH par defaut est `service` / `service`.

Ce mot de passe d'usine doit etre change immediatement sur tout kit reel.

## Open Source

Fieldkit est open source et disponible sous licence MIT dans [LICENSE](https://github.com/infragilis/fieldkitV2/blob/main/LICENSE).

## Problemes Et Fonctions

- <https://github.com/infragilis/fieldkitV2/issues>

## Fonctionnalites Actuelles

- Backend FastAPI avec routes et services modulaires
- Tableau de bord principal axe sur console, docs et envois
- Page `/settings` pour connectivite, reseau, mot de passe et presets serie
- Page `/files` pour `data`, `personal`, `usb` et `serial-logs`
- Envois du bureau vers `personal` ou `usb`
- Protection contre l'ecrasement silencieux des fichiers existants
- Suppression dans `personal` et `serial-logs`
- Detection automatique des supports USB sous `/media/service`, `/media` et `/mnt`
- Filtrage des fichiers caches et metadonnees macOS dans le navigateur de fichiers
- Notes de reference fournisseurs accessibles depuis l'interface
- Parametres persistants pour ethernet, Wi-Fi et profils serie
- Bascule rapide entre `9600 8N1` et `115200 8N1`
- Detection automatique des adaptateurs serie
- Page `/serial-settings` pour la configuration detaillee par console
- Arbre d'export partage `/fieldkit` pour HTTP, TFTP, FTP et SCP
- Interrupteurs pour HTTP simple, TFTP et FTP ; SCP reste disponible via SSH
- Fenetres popup sur `/serial-console/0` et `/serial-console/1`
- Capture clavier directe dans les sessions popup
- Journaux de session horodates dans `runtime/state/serial-logs`
- Actions de reset pour les consoles actives
- Planification reseau en mode dry-run

## Interface Web

Routes principales :

- `/`
- `/settings`
- `/serial-settings`
- `/files`
- `/fieldkit`
- `/readme`
- `/kit-docs`

## Bibliotheques De Fichiers

Fieldkit expose quatre bibliotheques via la page `Files` :

- `data`
- `personal`
- `usb`
- `serial-logs`

Elles sont aussi disponibles via :

- HTTP sur `/fieldkit/data`, `/fieldkit/personal` et `/fieldkit/usb`
- FTP depuis la meme racine d'export
- SCP sous `/opt/fieldkit/runtime/content/fieldkit/<library>/...`
- TFTP avec la meme structure apres application de `scripts/install_transfer_services.sh`

`serial-logs` ne fait volontairement pas partie de l'arbre d'export partage.

## Comportement USB Actuel

- Si un support amovible est monte automatiquement sous `/media/service`, `/media` ou `/mnt`, Fieldkit l'utilise comme bibliotheque `usb`
- Fieldkit prend le premier chemin monte correspondant, ce qui convient surtout au cas courant d'une seule cle USB
- La selection multi-disques, les labels de volume visibles et le rafraichissement automatique hot-plug ne sont pas encore implementes

## Comportement Fichiers Actuel

- Les envois sont autorises vers `personal` et `usb`
- Les envois vers `data` et `serial-logs` sont bloques
- Les doublons de nom de fichier renvoient un conflit au lieu d'ecraser
- La suppression est autorisee pour `personal` et `serial-logs`
- Les fichiers `usb` restent traites comme non supprimables

## Execution Locale

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
uvicorn app.main:app --reload
```

Ouvrez `http://127.0.0.1:8000`.

## Documentation Du Kit

Des notes rapides locales sont servies depuis `docs/kits` et exposees depuis la page principale ainsi que via `/kit-docs`.

Sujets actuels :

- `NetApp`
- `Cisco`
- `NVIDIA`
- `Brocade Fabric OS`
- `Broadcom Ethernet Switching`

## Plateforme Minimale Supportee

- Raspberry Pi 3 Model B ou plus recent
- Debian 13 (`trixie`) 64 bits
- Python 3.13
- NetworkManager / `nmcli`
- OpenSSH server

Reference : [docs/platform-baseline.md](docs/platform-baseline.md)

## Guides De Deploiement

- [docs/pi-setup.md](docs/pi-setup.md)
- [docs/update-and-reload.md](docs/update-and-reload.md)
- [docs/golden-image-checklist.md](docs/golden-image-checklist.md)

## Limitations Actuelles

- La navigation USB utilise le premier chemin monte detecte sous `/media/service`, `/media` ou `/mnt` ; la selection multi-disques n'existe pas encore
- Les labels de volume USB visibles et le rafraichissement automatique hot-plug ne sont pas encore implementes
- Les profils serie privilegient `device_hint` s'il correspond a un adaptateur detecte, sinon le prochain `ttyUSB*` ou `ttyACM*` ; l'identite stable via numero de serie USB ou topologie physique n'existe pas encore
- Le changement de mot de passe reste un chemin backend provisoire
- L'application reseau reste un flux dry-run
- Les workflows Ansible cote appareil ne sont pas encore implementes

## Etapes Suivantes

1. Ameliorer la gestion USB pour plusieurs disques, labels et rafraichissement en direct
2. Ajouter des controles serie plus riches comme break et meilleure reconnexion
3. Relier les actions reseau a de vrais changements NetworkManager ou systemd-networkd
4. Etendre les flux HTTP/TFTP/FTP pour images et firmwares
5. Ajouter l'execution Ansible et les runbooks NetApp

## Ressources De Deploiement

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
