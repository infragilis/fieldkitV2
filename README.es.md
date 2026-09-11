# Fieldkit

Fieldkit es una herramienta basada en Raspberry Pi para trabajo de campo sobre equipos de red. Ofrece una interfaz web local para consola, archivos, servicios de transferencia y gestion del appliance.

Version actual del appliance: **v0.1.7**. Cluster Import y Server Sync muestran
etiquetas **beta** ambar en el menu.

## Sincronizacion Del Servidor Y Archivos

- Configure la URL del servidor y su token en **Server Sync** del appliance.
  La comprobacion comienza 10 minutos despues del arranque y luego cada hora;
  **Sync now** la inicia inmediatamente. Se verifican el tamano y la suma de comprobacion.
- **`data/{cisco,ontap,brocade,efos,nvidia}`** contiene archivos compartidos de fabricantes;
  **`personal`** es para configuraciones y archivos propios del usuario.
- En la **interfaz web del servidor**, **Data** ofrece un selector de carpetas,
  descargas y **My sync subscriptions**. Seleccione las carpetas y guarde. Todos
  los kits con su token siguen esa seleccion; los archivos personales siempre se sincronizan.
- Las cuentas existentes conservan todas las carpetas hasta modificarlas. Las
  cuentas nuevas empiezan solo con archivos personales. Cancelar una suscripcion
  no elimina archivos ya descargados en el kit.
- El servidor permite cargas reanudables en bloques de 8 MiB, con progreso,
  velocidad, tiempo restante y reintento/cancelacion. Subir un archivo no activa
  automaticamente la suscripcion a su carpeta.
- En el **appliance**, use **Files → data** o **Files → personal** para los archivos
  locales. Las suscripciones se administran en el servidor.

Mas informacion: [Server Sync](docs/server-sync.md) y
[Cluster Import](docs/cluster-import.md) (ingles).

## Que Hace Fieldkit

- Ofrece dos sesiones de consola serie USB con ventanas emergentes
- Guarda archivos locales en `data`, `personal`, `usb` y `serial-logs`
- Permite subir y descargar archivos desde el navegador
- Registra sesiones serie para descarga posterior
- Comparte archivos por HTTP
- Comparte archivos por SCP
- Puede activar FTP y TFTP cuando haga falta
- Incluye una shell local del Pi accesible desde el navegador
- Incluye notas de referencia de fabricantes para uso en campo
- Soporta varios idiomas en la interfaz y en la vista README

## Recomendaciones De Hardware

- Raspberry Pi 3 Model B o superior
- Debian 13 (`trixie`) de 64 bits
- Dos adaptadores USB serie o cables de consola si quiere usar ambos puertos
- Una memoria USB si quiere almacenamiento removible en el kit
- Ethernet cableado recomendado para instalacion, actualizaciones y pruebas del modo AP

## Recomendacion De Almacenamiento

Fieldkit guarda en el propio appliance los archivos subidos, los archivos exportados y los logs de consola.

- Tamano minimo recomendado de la microSD: `64 GB` si usas la sincronizacion de servidor (los archivos existen dos veces)
- `32 GB` es suficiente para kits que no usan la sincronizacion de servidor
- Use mas capacidad si piensa guardar imagenes, firmware o muchos logs serie

## Funciones Principales

- Panel principal para acceso rapido a consolas, archivos, documentacion y ajustes
- Pagina de ajustes para conectividad, servicios de transferencia, cambio de contrasena y presets serie
- Pagina de archivos para `data`, `personal`, `usb` y `serial-logs`
- Explorador de exportaciones en bruto en `/fieldkit`
- Shell del navegador en `/pi-shell`
- Indice de documentacion local en `/kit-docs`
- Vista README localizada en `/readme`

## Opciones De Transferencia

Fieldkit puede exponer archivos compartidos por:

- HTTP
- SCP
- FTP
- TFTP

La exportacion HTTP para `/fieldkit/...` esta disponible por defecto. FTP y TFTP pueden activarse desde la pagina Settings cuando haga falta.

## Punto De Acceso Wi-Fi

Fieldkit puede ejecutar un punto de acceso Wi-Fi dedicado para acceso local directo:

- SSID: `fieldkit`
- Contrasena: `fieldkit`

Use Ethernet cableado para instalacion y recuperacion mientras prueba cambios del modo AP.

## Acceso Predeterminado

El acceso SSH predeterminado es `service` / `service`.

Cambielo inmediatamente en cualquier despliegue real.

## Plataforma Recomendada

- Raspberry Pi 3 Model B o superior
- Debian 13 (`trixie`) de 64 bits
- Python 3.13
- NetworkManager
- OpenSSH server

## Documentacion

- [docs/pi-setup.md](docs/pi-setup.md)
- [docs/update-and-reload.md](docs/update-and-reload.md)
- [docs/golden-image-checklist.md](docs/golden-image-checklist.md)
- [docs/architecture.md](docs/architecture.md)

## Codigo Abierto

Fieldkit es software abierto y esta disponible bajo licencia MIT en [LICENSE](https://github.com/infragilis/fieldkitV2/blob/main/LICENSE).

Errores y solicitudes de funciones:

- <https://github.com/infragilis/fieldkitV2/issues>
