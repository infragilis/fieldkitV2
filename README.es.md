# Fieldkit

Fieldkit es un appliance basado en Raspberry Pi para tareas de servicio en campo sobre dispositivos de red. Incluye:

- Una interfaz web para consola serie, transferencia de archivos, revision de conectividad y ajustes del appliance
- Dos endpoints de consola serie USB con ajustes independientes y ventanas emergentes
- Una biblioteca de contenido local dividida en `data`, `personal`, `usb` y `serial-logs`
- Un backend modular para aislar la logica especifica de Raspberry Pi de la capa web

## Nota De Hardware

El acceso por consola requiere cables USB a serie o adaptadores USB serie que aparezcan como `ttyUSB*` o `ttyACM*`.

La exportacion USB gadget, donde Fieldkit aparece ante otro equipo como si fuera una memoria USB conectada directamente, requiere una Raspberry Pi con puerto USB OTG en modo dispositivo. La caja de referencia actual es una Raspberry Pi 3 Model B Rev 1.2 y no admite ese modo.

Si el modo USB gadget es importante para su flujo de trabajo, use una Raspberry Pi con soporte real de modo dispositivo USB.

## Acceso Predeterminado

El acceso SSH predeterminado del appliance es `service` / `service`.

Es una credencial inicial de fabrica y debe cambiarse inmediatamente en cualquier equipo real.

## Codigo Abierto

Fieldkit es software de codigo abierto y puede usarse, modificarse y distribuirse bajo la licencia MIT en [LICENSE](https://github.com/infragilis/fieldkitV2/blob/main/LICENSE).

Este proyecto se entrega `AS IS`, sin garantia expresa ni implicita.

## Problemas Y Funciones

Publique errores, problemas y solicitudes de funciones en:

- <https://github.com/infragilis/fieldkitV2/issues>

## Funcionalidad Actual

El repositorio actual y el kit en vivo ofrecen:

- Backend FastAPI con routers y servicios modulares
- Panel principal centrado en consola, documentacion y cargas
- Pagina `/settings` para conectividad, red, cambio de contrasena y presets serie
- Pagina `/files` para navegar `data`, `personal`, `usb` y `serial-logs`
- Cargas desde el escritorio hacia `personal` o `usb`
- Proteccion contra sobrescritura accidental de archivos existentes
- Borrado de archivos en `personal` y de logs en `serial-logs`
- Deteccion automatica de USB en `/media/service`, `/media` y `/mnt`
- Filtrado de metadatos ocultos o de macOS en la vista de archivos
- Notas de referencia de fabricantes enlazadas desde la interfaz
- Ajustes persistentes para ethernet, Wi-Fi y perfiles serie
- Cambio rapido entre `9600 8N1` y `115200 8N1`
- Deteccion automatica de adaptadores serie cuando no hay ruta fija definida
- Pagina `/serial-settings` para configuracion detallada por consola
- Arbol de exportacion compartido en `/fieldkit` para descargas HTTP con la misma estructura usada por TFTP, FTP y SCP
- Conmutadores para HTTP plano, TFTP y FTP; SCP sigue disponible por SSH
- Ventanas emergentes de consola en `/serial-console/0` y `/serial-console/1`
- Captura directa de teclado en sesiones de consola
- Logs de sesiones serie con marca de tiempo en `runtime/state/serial-logs`
- Acciones de reinicio para sesiones de consola activas
- Planificacion de cambios de red en modo dry-run
- Unidad systemd e instalador para el servicio web

Las integraciones especificas de Pi como `hostapd`, `dnsmasq`, `nmcli`, `tftpd`, `vsftpd`, `ssh/scp` y streaming serie se mantienen detras de modulos de servicio.

## Requisitos Operativos

- Fieldkit debe poder ejecutar flujos de trabajo Ansible contra dispositivos desde el propio kit.
- Las sesiones de consola serie deben quedar registradas con archivos fechados.

## Interfaz Web

Rutas principales:

- `/` panel principal
- `/settings` conectividad, red, contrasena y presets serie
- `/serial-settings` perfiles serie detallados
- `/files` exploracion, carga y borrado de archivos
- `/fieldkit` explorador de exportaciones y descargas directas
- `/readme` README del repositorio servido localmente
- `/kit-docs` indice de documentacion local

## Bibliotecas De Archivos

Fieldkit expone cuatro bibliotecas en la pagina `Files`:

- `data`
- `personal`
- `usb`
- `serial-logs`

Estas mismas bibliotecas tambien se exponen por:

- HTTP en `/fieldkit/data`, `/fieldkit/personal` y `/fieldkit/usb`
- FTP desde la misma raiz compartida cuando `vsftpd` esta habilitado
- SCP en `/opt/fieldkit/runtime/content/fieldkit/<library>/...`
- TFTP con la misma estructura cuando se aplica `scripts/install_transfer_services.sh`

`serial-logs` no forma parte del arbol de exportacion compartido. Solo se ofrece por la GUI y el endpoint de descarga de archivos.

La exportacion HTTP simple para `/fieldkit/...` esta activada por defecto para clientes de mantenimiento que no soportan HTTPS.

## Comportamiento USB Actual

- Si hay almacenamiento montado automaticamente en `/media/service`, `/media` o `/mnt`, Fieldkit lo usa como biblioteca `usb`
- Fieldkit elige el primer directorio montado que encuentra en esas rutas, lo cual funciona mejor en el caso comun de una sola memoria USB
- Aun no existe seleccion de multiples unidades, etiquetas visibles de volumen ni refresco automatico por hot-plug

## Comportamiento Actual De Archivos

- Se permiten cargas a `personal` y `usb`
- Las cargas a `data` y `serial-logs` estan bloqueadas
- Los nombres duplicados devuelven una advertencia en lugar de sobrescribir
- Se permite borrar en `personal` y `serial-logs`
- Los archivos de `usb` siguen tratandose como solo lectura para borrado

## Ejecucion Local

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
uvicorn app.main:app --reload
```

Abra `http://127.0.0.1:8000`.

Cada sesion WebSocket de consola crea un log con marca UTC en `runtime/state/serial-logs`. Si no existe una preferencia guardada de dispositivo, Fieldkit asigna el siguiente `ttyUSB*` o `ttyACM*` detectado.

## Documentacion Del Kit

Fieldkit incluye notas rapidas de referencia de fabricantes servidas localmente desde `docs/kits` y visibles tanto desde la pagina principal como desde `/kit-docs`.

Temas actuales:

- `NetApp`
- `Cisco`
- `NVIDIA`
- `Brocade Fabric OS`
- `Broadcom Ethernet Switching`

## Plataforma Minima Soportada

- Raspberry Pi 3 Model B o superior
- Debian 13 (`trixie`) de 64 bits
- Python 3.13
- NetworkManager / `nmcli`
- OpenSSH server

La referencia de plataforma esta documentada en [docs/platform-baseline.md](docs/platform-baseline.md).

## Guias De Despliegue

- [docs/pi-setup.md](docs/pi-setup.md)
- [docs/update-and-reload.md](docs/update-and-reload.md)
- [docs/golden-image-checklist.md](docs/golden-image-checklist.md)

## Limitaciones Actuales

- La exploracion USB usa la primera ruta montada detectada bajo `/media/service`, `/media` o `/mnt`, por lo que no hay seleccion de multiples unidades
- No existen etiquetas de volumen USB visibles ni refresco automatico por hot-plug
- Los perfiles serie prefieren `device_hint` si coincide con un adaptador detectado; en otro caso usan el siguiente `ttyUSB*` o `ttyACM*` disponible. No existe identidad estable por numero de serie USB o topologia fisica
- El cambio de contrasena sigue siendo un flujo placeholder en backend
- La aplicacion de red sigue siendo dry-run y no reconfiguracion real
- Los flujos Ansible del lado del dispositivo aun no estan implementados

## Siguientes Pasos

1. Mejorar el manejo USB para multiples unidades, etiquetas y refresco en vivo
2. Anadir controles serie mas ricos, como break y mejor reconexion
3. Conectar las acciones de red a cambios reales de NetworkManager o systemd-networkd
4. Ampliar los flujos HTTP/TFTP/FTP para imagenes y firmware
5. Anadir ejecucion Ansible y runbooks de NetApp

## Recursos De Despliegue

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

## Estado HTTPS

HTTPS autofirmado esta preparado pero no activado por defecto en el kit vivo. Cuando haga falta:

```bash
sudo bash /opt/fieldkit/scripts/install_https_self_signed.sh
```
