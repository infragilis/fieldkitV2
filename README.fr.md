# Fieldkit

Fieldkit est un outil Raspberry Pi pour le travail terrain sur des equipements reseau. Il fournit une interface web locale pour la console, les fichiers, les services de transfert et la gestion de l'appliance.

Version actuelle de l'appliance : **v0.2.2**. Cluster Import et Server Sync portent
des etiquettes **beta** ambre dans le menu.

## Synchronisation Serveur Et Fichiers

- Configurez l'URL du serveur et votre jeton dans **Server Sync** sur l'appliance.
  La verification commence 10 minutes apres le demarrage, puis chaque heure;
  **Sync now** la lance immediatement. La taille et la somme de controle sont verifiees.
- **`data/{cisco,ontap,brocade,efos,nvidia}`** contient les fichiers fournisseurs partages;
  **`personal`** est reserve aux configurations et fichiers propres a l'utilisateur.
- Dans l'**interface web du serveur**, **Data** propose le choix des dossiers,
  les telechargements et **My sync subscriptions**. Selectionnez puis enregistrez
  vos dossiers. Tous les kits utilisant votre jeton suivent ce choix; les fichiers personnels restent inclus.
- Les comptes existants conservent tous les dossiers jusqu'a modification. Les
  nouveaux comptes commencent avec les fichiers personnels uniquement. Se desabonner
  ne supprime pas les fichiers deja telecharges sur le kit.
- Le serveur accepte les envois reprenables par blocs de 8 MiB, avec progression,
  vitesse, temps restant et reprise/annulation. Un envoi n'abonne pas automatiquement
  l'utilisateur au dossier de donnees.
- Sur l'**appliance**, ouvrez **Files → data** ou **Files → personal** pour les
  fichiers locaux. Les abonnements se gerent sur le serveur.

Details : [Server Sync](docs/server-sync.md) et
[Cluster Import](docs/cluster-import.md) (anglais).

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

- Taille minimale recommandee de la microSD : `64 GB` avec la synchronisation serveur (fichiers en double)
- `32 GB` suffisent pour les kits sans synchronisation serveur
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

## Point D'Acces Wi-Fi

Fieldkit peut faire fonctionner un point d'acces Wi-Fi dedie pour un acces local direct :

- SSID : `fieldkit`
- Mot de passe : `fieldkit`

Utilisez l'Ethernet filaire pour l'installation et la recuperation pendant les tests du mode AP.

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
