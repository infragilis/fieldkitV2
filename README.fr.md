# Fieldkit

Fieldkit est un outil Raspberry Pi pour le travail terrain sur des equipements reseau. Il fournit une interface web locale pour la console, les fichiers, les services de transfert et la gestion de l'appliance.

## Ce Que Fait Fieldkit

- Deux sessions serie USB avec fenetres popup
- Stockage local dans `data`, `personal`, `usb` et `serial-logs`
- Envois et telechargements depuis le navigateur
- Journalisation des sessions serie pour telechargement ulterieur
- Fichiers partages via HTTP
- Fichiers partages via SCP
- FTP et TFTP peuvent etre actives si necessaire
- Shell locale du Pi accessible depuis le navigateur
- Notes de reference fournisseurs pour le terrain
- Interface multilingue et vue README localisee

## Recommandations Materielles

- Raspberry Pi 3 Model B ou plus recent
- Debian 13 (`trixie`) 64 bits
- Deux adaptateurs USB serie ou cables console si vous voulez utiliser les deux ports
- Une cle USB si vous voulez du stockage amovible sur le kit
- Ethernet filaire recommande pour l'installation, les mises a jour et les tests AP

## Recommandation De Stockage

Fieldkit stocke sur l'appliance elle-meme les fichiers envoyes, les fichiers exportes et les journaux de console.

- Taille minimale recommandee de la microSD : `32 GB`
- Utilisez plus d'espace si vous comptez garder des images, firmwares ou de nombreux logs serie sur le kit

## Fonctions Principales

- Tableau de bord pour acces rapide a la console, aux fichiers, a la documentation et aux parametres
- Page Settings pour connectivite, services de transfert, changement de mot de passe et presets serie
- Page Files pour `data`, `personal`, `usb` et `serial-logs`
- Navigateur d'export brut sur `/fieldkit`
- Shell navigateur sur `/pi-shell`
- Index de documentation locale sur `/kit-docs`
- Vue README localisee sur `/readme`

## Options De Transfert

Fieldkit peut exposer des fichiers partages via :

- HTTP
- SCP
- FTP
- TFTP

L'export HTTP pour `/fieldkit/...` est disponible par defaut. FTP et TFTP peuvent etre actives depuis la page Settings si necessaire.

## Preparation Du Point D'Acces Wi-Fi

Fieldkit peut etre prepare avec un profil de point d'acces Wi-Fi precree :

- SSID : `fieldkit`
- Mot de passe : `fieldkit`

Ce profil peut etre cree a l'avance et laisse desactive jusqu'au passage en mode AP.

## Acces Par Defaut

Le login SSH par defaut est `service` / `service`.

Changez-le immediatement sur tout deploiement reel.

## Plateforme Recommandee

- Raspberry Pi 3 Model B ou plus recent
- Debian 13 (`trixie`) 64 bits
- Python 3.13
- NetworkManager
- OpenSSH server

## Documentation

- [docs/pi-setup.md](docs/pi-setup.md)
- [docs/update-and-reload.md](docs/update-and-reload.md)
- [docs/golden-image-checklist.md](docs/golden-image-checklist.md)
- [docs/architecture.md](docs/architecture.md)

## Open Source

Fieldkit est open source et disponible sous licence MIT dans [LICENSE](https://github.com/infragilis/fieldkitV2/blob/main/LICENSE).

Problemes et demandes de fonctions :

- <https://github.com/infragilis/fieldkitV2/issues>
