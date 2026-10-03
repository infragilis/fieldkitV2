const STORAGE_KEYS = {
  theme: "fieldkit-theme",
  language: "fieldkit-language",
};

const LANGUAGES = {
  en: { flag: "GB", label: "English" },
  es: { flag: "ES", label: "Espanol" },
  de: { flag: "DE", label: "Deutsch" },
  nl: { flag: "NL", label: "Nederlands" },
  fr: { flag: "FR", label: "Francais" },
};

const TRANSLATIONS = {
  en: {
    nav_home: "Home",
    nav_console: "Console",
    nav_files: "Files",
    nav_cluster: "Cluster Import",
    nav_server_sync: "Server Sync",
    nav_docs: "Docs",
    nav_tools: "Tools",
    nav_settings: "Settings",
    nav_readme: "README",
    hero_kicker: "Field service appliance",
    hero_subhead: "Serial consoles, file libraries, transfer services and field reference notes - for network equipment work anywhere.",
    kicker_live: "Live",
    theme_dark: "Dark",
    theme_light: "Light",
    serial_consoles: "Serial Consoles",
    open_console_1: "Open Console 1",
    open_console_2: "Open Console 2",
    popup_note: "Each console opens in its own movable popup window for field use.",
    quick_access: "Quick Access",
    jump_console: "Jump to Console",
    browse_files: "Browse Files",
    raw_exports: "Raw Exports",
    open_settings: "Open Settings",
    reference_docs: "Reference Docs",
    docs_note: "Vendor quick-reference topics stored locally on the kit.",
    docs_index: "Open docs index",
    upload_title: "Upload",
    destination: "Destination",
    upload_file: "Upload File",
    subnet_calculator: "Subnet Calculator",
    subnet_note: "Calculate IPv4 network details for field addressing and handoff notes.",
    ip_address: "IP Address",
    cidr_prefix: "CIDR Prefix",
    calculate: "Calculate",
    subnet_invalid_ip: "Enter an IPv4 address like 192.168.200.120.",
    subnet_invalid_prefix: "Enter a CIDR prefix from 0 to 32.",
    subnet_network: "Network",
    subnet_netmask: "Netmask",
    subnet_wildcard: "Wildcard",
    subnet_broadcast: "Broadcast",
    subnet_host_range: "Usable Range",
    subnet_hosts: "Usable Hosts",
    subnet_single_host: "Single host route",
    subnet_point_to_point: "Point-to-point range",
    settings_title: "Settings",
    appliance_controls: "Appliance Controls",
    settings_subhead: "Connectivity status, network configuration, password changes, and serial console settings.",
    networking: "Networking",
    transfer_services: "Transfer services",
    serial_presets: "Serial presets",
    password: "Password",
    operational_notes: "Operational Notes",
    export_browser: "Export Browser",
    open_local_shell: "Open Local Shell",
    full_serial_profiles: "Full Serial Profiles",
    open_readme: "Open README",
    back_to_console: "Back to Console",
    connectivity: "Connectivity",
    active_links: "Active Links",
    nearby_wifi: "Nearby Wi-Fi",
    hostname: "Hostname",
    ethernet_mode: "Ethernet Mode",
    static: "Static",
    dhcp: "DHCP",
    ethernet_address: "Ethernet Address",
    wifi_mode: "Wi-Fi Mode",
    wifi_ssid: "Wi-Fi SSID",
    wifi_password: "Wi-Fi AP Password",
    wifi_access_note: "Apple devices can reach the GUI at http://{hostname}.local/ while connected to the Fieldkit AP. Direct fallback: http://10.42.0.1/",
    disabled: "Disabled",
    ap: "AP",
    client: "Client",
    save_network_settings: "Save Network Settings",
    apply_network_settings: "Apply Network Settings",
    network_apply_note: "Apply Network Settings saves the current form values and executes the live appliance network change.",
    applying_network_settings: "Applying network settings...",
    network_apply_failed: "Network apply failed: {message}",
    transfer_services_title: "Transfer Services",
    http_export_access: "HTTP Export Access",
    tftp_access: "TFTP Access",
    ftp_access: "FTP Access",
    apply_transfer_services: "Apply Transfer Services",
    transfer_services_note: "HTTP export access exposes only /fieldkit on plain port 80 for device downloads. FTP and TFTP stay off until enabled here. SCP remains available through the normal SSH service.",
    serial_settings: "Serial Settings",
    console_1_preset: "Console 1 Preset",
    console_2_preset: "Console 2 Preset",
    custom: "Custom",
    save_serial_settings: "Save Serial Settings",
    serial_settings_note: "For nonstandard baud, parity, stop bits, or device paths, use Serial Profiles.",
    change_password: "Change Password",
    current_password: "Current Password",
    new_password: "New Password",
    files_title: "Files",
    files_note: "Browse the local file libraries available on the kit.",
    upload_from_desktop: "Upload From Local Desktop",
    upload_current_library: "Upload To Current Library",
    exports_title: "Fieldkit Exports",
    export_path: "HTTP: /fieldkit{path}",
    export_root_note: "TFTP, FTP, and SCP use the same library structure rooted at {root}.",
    up_one_level: "Up one level",
    readme_title: "README",
    docs_title: "Fieldkit Reference Notes",
    docs_intro: "Starter command references for common vendor platforms.",
    back_to_docs: "Back to docs index",
    serial_profiles_title: "Serial Profiles",
    serial_profiles_note: "Serial adapters are auto-detected by default. Pin a console to a stable adapter so it keeps the same cable across reboots and re-plugs.",
    label: "Label",
    device_preference: "Device Preference",
    device_optional_0: "Optional: /dev/ttyUSB0",
    device_optional_1: "Optional: /dev/ttyUSB1",
    device_auto: "Auto-detect (lowest port)",
    device_not_detected: "(not detected)",
    device_not_present: "No adapter detected for this console.",
    resolved_to: "Resolved",
    pinned: "pinned",
    pin_console: "Pin",
    unpinned: "auto",
    baud_rate: "Baud Rate",
    data_bits: "Data Bits",
    parity: "Parity",
    stop_bits: "Stop Bits",
    none: "None",
    even: "Even",
    odd: "Odd",
    console_1: "Console 1",
    console_2: "Console 2",
    save_serial_profiles: "Save Serial Profiles",
    upload_failed: "Upload failed",
    saved_to: "Saved {name} to {library}",
    uploads_not_allowed: "Uploads are not allowed to {library}.",
    uploads_managed_by_server: "Uploads for vendor data are managed by the server.",
    no_entries: "No entries",
    directory_path: "directory: {path}",
    download: "Download",
    copy_to_usb: "Copy to USB",
    copying_to_usb: "Copying {name} to USB…",
    copied_to_usb: "Copied {name} to USB ({destination}).",
    on_usb: "On USB",
    copy_failed: "Copy failed",
    usb_not_mounted: "No USB storage is mounted on the kit.",
    usb_copy_running: "A copy is already running.",
    delete: "Delete",
    reset: "Reset",
    delete_confirm: "Delete {path} from {library}?",
    delete_failed: "Delete failed",
    no_files: "No files",
    directory: "Directory",
    preset: "Preset",
    preset_title: "{label} serial line preset",
    reset_session: "Reset session",
    reset_session_title: "Reset {label} session",
    bytes: "{size} bytes",
    secure: "secure",
    preferred: "preferred",
    auto_detect: "auto-detect",
    unavailable: "unavailable",
    yes: "yes",
    no: "no",
    http_label: "HTTP",
    root_label: "Root",
    http_export_label: "HTTP Export",
    tftp_label: "TFTP",
    ftp_label: "FTP",
    scp_label: "SCP",
    usb_gadget_label: "USB Gadget Export",
    configured: "configured",
    active: "active",
    enabled: "enabled",
    built_in_over_ssh: "built in over SSH",
    popup_blocked: "Popup blocked for Console {index}. Allow popups for this site.",
    serial_preset_saving: "Saving serial preset...",
    serial_set: "{label} set to {baud} 8N1.",
    serial_preset_save_failed: "Serial preset save failed: {message}",
    resetting_console: "Resetting Console {index}...",
    console_reset: "Console {index} session reset.",
    console_no_session: "Console {index} had no active session to reset.",
    console_reset_failed: "Console reset failed: {message}",
    reconnect: "Reconnect",
    opening_session: "Opening session...",
    connecting: "Connecting...",
    reconnecting: "Reconnecting",
    connected: "Connected",
    disconnected: "Disconnected",
    connecting_to_console: "Connecting to console {index}...",
    console_disconnected: "Console disconnected",
    console_window_title: "Console {index}",
    console_move_note: "This popup can be moved independently by the field engineer.",
    console_capture_note: "Keyboard input is captured directly in this window. Click the terminal area if input focus is lost.",
    applying_transfer_services: "Applying transfer service settings...",
    transfer_apply_failed: "Transfer service apply failed: {message}",
    password_change_accepted: "Password changed for the local service account.",
    password_change_rejected: "Password change rejected.",
    local_shell_title: "Local Pi Shell",
    local_shell_note: "This terminal runs directly on the Fieldkit appliance as the local service account.",
    serial_profiles_saved: "Serial profiles saved.",
    serial_profile_save_failed: "Serial profile save failed.",
    failed_load_profiles: "Failed to load serial profiles: {message}",
    input_voltage_ok: "Input voltage: OK",
    input_voltage_low_now: "Input voltage: LOW",
    input_voltage_low_seen: "Input voltage: LOW SEEN",
    input_voltage_unavailable: "Input voltage unavailable",
  },
};
TRANSLATIONS.es = { ...TRANSLATIONS.en,
  nav_home: "Inicio",
  nav_console: "Consola",
  nav_files: "Archivos",
  nav_tools: "Herramientas",
  nav_settings: "Configuración",
  hero_kicker: "Aparato de servicio de campo",
  hero_subhead: "Consolas serie, bibliotecas de archivos, servicios de transferencia y notas de referencia - para trabajar con equipos de red en cualquier lugar.",
  kicker_live: "En vivo",
  theme_dark: "Oscuro",
  theme_light: "Claro",
  serial_consoles: "Consolas serie",
  open_console_1: "Abrir Consola 1",
  open_console_2: "Abrir Consola 2",
  popup_note: "Cada consola se abre en su propia ventana emergente móvil para uso en campo.",
  quick_access: "Acceso rápido",
  jump_console: "Ir a consola",
  browse_files: "Explorar archivos",
  raw_exports: "Exportaciones",
  open_settings: "Abrir ajustes",
  reference_docs: "Documentación",
  docs_note: "Temas de referencia de fabricantes guardados localmente en el kit.",
  docs_index: "Abrir índice de documentos",
  upload_title: "Subir",
  destination: "Destino",
  upload_file: "Subir archivo",
  subnet_calculator: "Calculadora de subred",
  subnet_note: "Calcula detalles IPv4 para direccionamiento en campo y notas de traspaso.",
  ip_address: "Dirección IP",
  cidr_prefix: "Prefijo CIDR",
  calculate: "Calcular",
  subnet_invalid_ip: "Introduzca una dirección IPv4 como 192.168.200.120.",
  subnet_invalid_prefix: "Introduzca un prefijo CIDR de 0 a 32.",
  subnet_network: "Red",
  subnet_netmask: "Máscara de red",
  subnet_wildcard: "Comodín",
  subnet_broadcast: "Difusión",
  subnet_host_range: "Rango útil",
  subnet_hosts: "Hosts útiles",
  subnet_single_host: "Ruta de host único",
  subnet_point_to_point: "Rango punto a punto",
  settings_title: "Configuración",
  appliance_controls: "Controles del aparato",
  settings_subhead: "Estado de conectividad, configuración de red, cambio de contraseña y ajustes de consola serie.",
  networking: "Red",
  transfer_services: "Servicios de transferencia",
  serial_presets: "Perfiles serie",
  password: "Contraseña",
  operational_notes: "Notas operativas",
  export_browser: "Explorador de exportaciones",
  open_local_shell: "Abrir shell local",
  full_serial_profiles: "Perfiles serie completos",
  open_readme: "Abrir README",
  back_to_console: "Volver a consola",
  connectivity: "Conectividad",
  active_links: "Enlaces activos",
  nearby_wifi: "Wi-Fi cercano",
  hostname: "Nombre de host",
  ethernet_mode: "Modo Ethernet",
  static: "Estática",
  ethernet_address: "Dirección Ethernet",
  wifi_mode: "Modo Wi-Fi",
  wifi_ssid: "SSID de Wi-Fi",
  wifi_password: "Contraseña del AP Wi-Fi",
  wifi_access_note: "Los dispositivos Apple pueden acceder a la interfaz en http://{hostname}.local/ mientras están conectados al AP Fieldkit. Alternativa directa: http://10.42.0.1/",
  disabled: "Deshabilitado",
  client: "Cliente",
  save_network_settings: "Guardar red",
  apply_network_settings: "Aplicar red",
  network_apply_note: "Aplicar red guarda los valores del formulario y ejecuta el cambio de red real en el aparato.",
  applying_network_settings: "Aplicando ajustes de red...",
  network_apply_failed: "La aplicación de red falló: {message}",
  transfer_services_title: "Servicios de transferencia",
  http_export_access: "Acceso HTTP de exportación",
  tftp_access: "Acceso TFTP",
  ftp_access: "Acceso FTP",
  apply_transfer_services: "Aplicar servicios",
  transfer_services_note: "El acceso HTTP de exportación expone solo /fieldkit en el puerto 80 para descargas de dispositivos. FTP y TFTP permanecen apagados hasta activarlos aquí. SCP sigue disponible mediante el servicio SSH normal.",
  serial_settings: "Ajustes serie",
  console_1_preset: "Perfil Consola 1",
  console_2_preset: "Perfil Consola 2",
  custom: "Personalizado",
  save_serial_settings: "Guardar ajustes serie",
  serial_settings_note: "Para baudios, paridad, bits de parada o rutas de dispositivo no estándar, use Perfiles serie.",
  change_password: "Cambiar contraseña",
  current_password: "Contraseña actual",
  new_password: "Nueva contraseña",
  files_title: "Archivos",
  files_note: "Explore las bibliotecas de archivos locales del kit.",
  upload_from_desktop: "Subir desde el escritorio",
  upload_current_library: "Subir a la biblioteca actual",
  exports_title: "Exportaciones de Fieldkit",
  export_root_note: "TFTP, FTP y SCP usan la misma estructura de bibliotecas con raíz en {root}.",
  up_one_level: "Subir un nivel",
  docs_title: "Notas de referencia de Fieldkit",
  docs_intro: "Referencias de comandos iniciales para plataformas de fabricantes comunes.",
  back_to_docs: "Volver al índice de documentos",
  serial_profiles_title: "Perfiles serie",
  serial_profiles_note: "Los adaptadores serie se detectan automáticamente de forma predeterminada. Fije una consola a un adaptador estable para que conserve el mismo cable tras reinicios y reconexiones.",
  label: "Etiqueta",
  device_preference: "Preferencia de dispositivo",
  device_auto: "Detección automática (puerto más bajo)",
  device_not_detected: "(no detectado)",
  device_not_present: "No se detectó ningún adaptador para esta consola.",
  resolved_to: "Resuelto",
  pinned: "fijado",
  pin_console: "Fijar",
  unpinned: "automático",
  baud_rate: "Velocidad en baudios",
  data_bits: "Bits de datos",
  parity: "Paridad",
  stop_bits: "Bits de parada",
  none: "Ninguna",
  even: "Par",
  odd: "Impar",
  console_1: "Consola 1",
  console_2: "Consola 2",
  save_serial_profiles: "Guardar perfiles serie",
  upload_failed: "Error al subir",
  saved_to: "Guardado {name} en {library}",
  uploads_not_allowed: "No se permiten subidas a {library}.",
  uploads_managed_by_server: "Las subidas de datos de fabricantes se gestionan desde el servidor.",
  no_entries: "Sin entradas",
  directory_path: "directorio: {path}",
  download: "Descargar",
  copy_to_usb: "Copiar a USB",
  copying_to_usb: "Copiando {name} a USB…",
  copied_to_usb: "Copiado {name} a USB ({destination}).",
  on_usb: "En USB",
  copy_failed: "Error al copiar",
  usb_not_mounted: "No hay almacenamiento USB montado en el kit.",
  usb_copy_running: "Ya hay una copia en curso.",
  delete: "Borrar",
  reset: "Restablecer",
  delete_confirm: "¿Borrar {path} de {library}?",
  delete_failed: "Error al borrar",
  no_files: "Sin archivos",
  directory: "Directorio",
  preset: "Perfil",
  preset_title: "Perfil de línea serie de {label}",
  reset_session: "Restablecer sesión",
  reset_session_title: "Restablecer la sesión de {label}",
  bytes: "{size} bytes",
  secure: "segura",
  preferred: "preferido",
  auto_detect: "detección automática",
  unavailable: "no disponible",
  yes: "sí",
  no: "no",
  root_label: "Raíz",
  http_export_label: "Exportación HTTP",
  usb_gadget_label: "Exportación USB Gadget",
  configured: "configurado",
  active: "activo",
  enabled: "habilitado",
  built_in_over_ssh: "integrado por SSH",
  popup_blocked: "Se bloqueó la ventana emergente de la Consola {index}. Permita las ventanas emergentes para este sitio.",
  serial_preset_saving: "Guardando perfil serie...",
  serial_set: "{label} ajustada a {baud} 8N1.",
  serial_preset_save_failed: "Error al guardar el perfil serie: {message}",
  resetting_console: "Restableciendo la Consola {index}...",
  console_reset: "Sesión de la Consola {index} restablecida.",
  console_no_session: "La Consola {index} no tenía una sesión activa que restablecer.",
  console_reset_failed: "Error al restablecer la consola: {message}",
  reconnect: "Reconectar",
  opening_session: "Abriendo sesión...",
  connecting: "Conectando...",
  reconnecting: "Reconectando",
  connected: "Conectado",
  disconnected: "Desconectado",
  connecting_to_console: "Conectando a la consola {index}...",
  console_disconnected: "Consola desconectada",
  console_window_title: "Consola {index}",
  console_move_note: "El ingeniero de campo puede mover esta ventana de forma independiente.",
  console_capture_note: "La entrada del teclado se captura directamente en esta ventana. Haga clic en el área del terminal si se pierde el foco.",
  applying_transfer_services: "Aplicando los ajustes de servicios de transferencia...",
  transfer_apply_failed: "Error al aplicar los servicios de transferencia: {message}",
  password_change_accepted: "Contraseña cambiada para la cuenta de servicio local.",
  password_change_rejected: "Cambio de contraseña rechazado.",
  local_shell_title: "Shell local del Pi",
  local_shell_note: "Este terminal se ejecuta directamente en el aparato Fieldkit como la cuenta de servicio local.",
  serial_profiles_saved: "Perfiles serie guardados.",
  serial_profile_save_failed: "Error al guardar el perfil serie.",
  failed_load_profiles: "Error al cargar los perfiles serie: {message}",
  input_voltage_ok: "Voltaje de entrada: OK",
  input_voltage_low_now: "Voltaje de entrada: BAJO",
  input_voltage_low_seen: "Voltaje de entrada: BAJO DETECTADO",
  input_voltage_unavailable: "Voltaje de entrada no disponible",
};
TRANSLATIONS.de = { ...TRANSLATIONS.en,
  nav_home: "Start",
  nav_console: "Konsole",
  nav_files: "Dateien",
  nav_tools: "Werkzeuge",
  nav_settings: "Einstellungen",
  hero_kicker: "Feldservice-Gerät",
  hero_subhead: "Serielle Konsolen, Dateibibliotheken, Transferdienste und Referenznotizen - für Arbeiten an Netzwerkgeräten überall.",
  kicker_live: "Live",
  theme_dark: "Dunkel",
  theme_light: "Hell",
  serial_consoles: "Serielle Konsolen",
  open_console_1: "Konsole 1 öffnen",
  open_console_2: "Konsole 2 öffnen",
  popup_note: "Jede Konsole öffnet sich in einem eigenen verschiebbaren Popup-Fenster für den Feldeinsatz.",
  quick_access: "Schnellzugriff",
  jump_console: "Zur Konsole",
  browse_files: "Dateien durchsuchen",
  raw_exports: "Roh-Exporte",
  open_settings: "Einstellungen öffnen",
  reference_docs: "Referenzdokumente",
  docs_note: "Lokal auf dem Kit gespeicherte Hersteller-Kurzreferenzen.",
  docs_index: "Dokumentindex öffnen",
  upload_title: "Hochladen",
  destination: "Ziel",
  upload_file: "Datei hochladen",
  subnet_calculator: "Subnetz-Rechner",
  subnet_note: "IPv4-Netzwerkdetails für Feldadressierung und Übergabenotizen berechnen.",
  ip_address: "IP-Adresse",
  cidr_prefix: "CIDR-Präfix",
  calculate: "Berechnen",
  subnet_invalid_ip: "Geben Sie eine IPv4-Adresse wie 192.168.200.120 ein.",
  subnet_invalid_prefix: "Geben Sie ein CIDR-Präfix von 0 bis 32 ein.",
  subnet_network: "Netzwerk",
  subnet_netmask: "Netzmaske",
  subnet_wildcard: "Wildcard",
  subnet_broadcast: "Broadcast",
  subnet_host_range: "Nutzbarer Bereich",
  subnet_hosts: "Nutzbare Hosts",
  subnet_single_host: "Einzelhost-Route",
  subnet_point_to_point: "Punkt-zu-Punkt-Bereich",
  settings_title: "Einstellungen",
  appliance_controls: "Gerätesteuerung",
  settings_subhead: "Konnektivitätsstatus, Netzwerkkonfiguration, Passwortänderungen und serielle Einstellungen.",
  networking: "Netzwerk",
  transfer_services: "Transferdienste",
  serial_presets: "Serielle Vorgaben",
  password: "Passwort",
  operational_notes: "Betriebshinweise",
  export_browser: "Export-Browser",
  open_local_shell: "Lokale Shell öffnen",
  full_serial_profiles: "Vollständige serielle Profile",
  open_readme: "README öffnen",
  back_to_console: "Zurück zur Konsole",
  connectivity: "Konnektivität",
  active_links: "Aktive Verbindungen",
  nearby_wifi: "WLAN in der Nähe",
  hostname: "Hostname",
  ethernet_mode: "Ethernet-Modus",
  static: "Statisch",
  ethernet_address: "Ethernet-Adresse",
  wifi_mode: "WLAN-Modus",
  wifi_ssid: "WLAN-SSID",
  wifi_password: "WLAN-AP-Passwort",
  wifi_access_note: "Apple-Geräte erreichen die Oberfläche unter http://{hostname}.local/, während sie mit dem Fieldkit-AP verbunden sind. Direkter Fallback: http://10.42.0.1/",
  disabled: "Deaktiviert",
  client: "Client",
  save_network_settings: "Netzwerk speichern",
  apply_network_settings: "Netzwerk anwenden",
  network_apply_note: "Netzwerk anwenden speichert die aktuellen Formularwerte und führt die echte Netzwerkänderung am Gerät aus.",
  applying_network_settings: "Netzwerkeinstellungen werden angewendet...",
  network_apply_failed: "Netzwerkanwendung fehlgeschlagen: {message}",
  transfer_services_title: "Transferdienste",
  http_export_access: "HTTP-Exportzugang",
  tftp_access: "TFTP-Zugang",
  ftp_access: "FTP-Zugang",
  apply_transfer_services: "Transferdienste anwenden",
  transfer_services_note: "Der HTTP-Exportzugang stellt nur /fieldkit auf Port 80 für Geräte-Downloads bereit. FTP und TFTP bleiben deaktiviert, bis sie hier aktiviert werden. SCP bleibt über den normalen SSH-Dienst verfügbar.",
  serial_settings: "Serielle Einstellungen",
  console_1_preset: "Vorgabe Konsole 1",
  console_2_preset: "Vorgabe Konsole 2",
  custom: "Benutzerdefiniert",
  save_serial_settings: "Serielle Einstellungen speichern",
  serial_settings_note: "Verwenden Sie für abweichende Baudrate, Parität, Stoppbits oder Gerätepfade die seriellen Profile.",
  change_password: "Passwort ändern",
  current_password: "Aktuelles Passwort",
  new_password: "Neues Passwort",
  files_title: "Dateien",
  files_note: "Durchsuchen Sie die lokalen Dateibibliotheken des Kits.",
  upload_from_desktop: "Vom Desktop hochladen",
  upload_current_library: "In aktuelle Bibliothek hochladen",
  exports_title: "Fieldkit-Exporte",
  export_root_note: "TFTP, FTP und SCP verwenden dieselbe Bibliotheksstruktur mit Wurzel {root}.",
  up_one_level: "Eine Ebene höher",
  docs_title: "Fieldkit-Referenznotizen",
  docs_intro: "Erste Befehlsreferenzen für gängige Herstellerplattformen.",
  back_to_docs: "Zurück zum Dokumentindex",
  serial_profiles_title: "Serielle Profile",
  serial_profiles_note: "Serielle Adapter werden standardmäßig automatisch erkannt. Fixieren Sie eine Konsole an einen stabilen Adapter, damit sie nach Neustarts und erneutem Anstecken dasselbe Kabel behält.",
  label: "Bezeichnung",
  device_preference: "Geräteauswahl",
  device_auto: "Automatisch erkennen (niedrigster Port)",
  device_not_detected: "(nicht erkannt)",
  device_not_present: "Für diese Konsole wurde kein Adapter erkannt.",
  resolved_to: "Aufgelöst",
  pinned: "fixiert",
  pin_console: "Fixieren",
  unpinned: "automatisch",
  baud_rate: "Baudrate",
  data_bits: "Datenbits",
  parity: "Parität",
  stop_bits: "Stoppbits",
  none: "Keine",
  even: "Gerade",
  odd: "Ungerade",
  console_1: "Konsole 1",
  console_2: "Konsole 2",
  save_serial_profiles: "Serielle Profile speichern",
  upload_failed: "Upload fehlgeschlagen",
  saved_to: "{name} nach {library} gespeichert",
  uploads_not_allowed: "Uploads nach {library} sind nicht erlaubt.",
  uploads_managed_by_server: "Uploads für Herstellerdaten werden vom Server verwaltet.",
  no_entries: "Keine Einträge",
  directory_path: "Verzeichnis: {path}",
  download: "Herunterladen",
  copy_to_usb: "Auf USB kopieren",
  copying_to_usb: "{name} wird auf USB kopiert…",
  copied_to_usb: "{name} auf USB kopiert ({destination}).",
  on_usb: "Auf USB",
  copy_failed: "Kopieren fehlgeschlagen",
  usb_not_mounted: "Auf dem Kit ist kein USB-Speicher eingebunden.",
  usb_copy_running: "Es läuft bereits eine Kopie.",
  delete: "Löschen",
  reset: "Zurücksetzen",
  delete_confirm: "{path} aus {library} löschen?",
  delete_failed: "Löschen fehlgeschlagen",
  no_files: "Keine Dateien",
  directory: "Verzeichnis",
  preset: "Vorgabe",
  preset_title: "Serielle Vorgabe für {label}",
  reset_session: "Sitzung zurücksetzen",
  reset_session_title: "Sitzung {label} zurücksetzen",
  bytes: "{size} Bytes",
  secure: "sicher",
  preferred: "bevorzugt",
  auto_detect: "Automatisch",
  unavailable: "nicht verfügbar",
  yes: "Ja",
  no: "Nein",
  root_label: "Wurzel",
  http_export_label: "HTTP-Export",
  usb_gadget_label: "USB-Gadget-Export",
  configured: "konfiguriert",
  active: "aktiv",
  enabled: "aktiviert",
  built_in_over_ssh: "per SSH integriert",
  popup_blocked: "Popup für Konsole {index} blockiert. Erlauben Sie Popups für diese Seite.",
  serial_preset_saving: "Serielle Vorgabe wird gespeichert...",
  serial_set: "{label} auf {baud} 8N1 gesetzt.",
  serial_preset_save_failed: "Speichern der seriellen Vorgabe fehlgeschlagen: {message}",
  resetting_console: "Konsole {index} wird zurückgesetzt...",
  console_reset: "Sitzung der Konsole {index} zurückgesetzt.",
  console_no_session: "Konsole {index} hatte keine aktive Sitzung zum Zurücksetzen.",
  console_reset_failed: "Zurücksetzen der Konsole fehlgeschlagen: {message}",
  reconnect: "Neu verbinden",
  opening_session: "Sitzung wird geöffnet...",
  connecting: "Verbinden...",
  reconnecting: "Neu verbinden...",
  connected: "Verbunden",
  disconnected: "Getrennt",
  connecting_to_console: "Verbindung mit Konsole {index}...",
  console_disconnected: "Konsole getrennt",
  console_window_title: "Konsole {index}",
  console_move_note: "Dieses Popup kann vom Feldeinsatztechniker unabhängig verschoben werden.",
  console_capture_note: "Tastatureingaben werden direkt in diesem Fenster erfasst. Klicken Sie auf den Terminalbereich, wenn der Fokus verloren geht.",
  applying_transfer_services: "Transferdienst-Einstellungen werden angewendet...",
  transfer_apply_failed: "Anwenden der Transferdienste fehlgeschlagen: {message}",
  password_change_accepted: "Passwort für das lokale Dienstkonto geändert.",
  password_change_rejected: "Passwortänderung abgelehnt.",
  local_shell_title: "Lokale Pi-Shell",
  local_shell_note: "Dieses Terminal läuft direkt auf dem Fieldkit-Gerät als lokales Dienstkonto.",
  serial_profiles_saved: "Serielle Profile gespeichert.",
  serial_profile_save_failed: "Speichern des seriellen Profils fehlgeschlagen.",
  failed_load_profiles: "Serielle Profile konnten nicht geladen werden: {message}",
  input_voltage_ok: "Eingangsspannung: OK",
  input_voltage_low_now: "Eingangsspannung: NIEDRIG",
  input_voltage_low_seen: "Eingangsspannung: NIEDRIG ERKANNT",
  input_voltage_unavailable: "Eingangsspannung nicht verfügbar",
};
TRANSLATIONS.nl = { ...TRANSLATIONS.en,
  nav_home: "Home",
  nav_console: "Console",
  nav_files: "Bestanden",
  nav_tools: "Hulpmiddelen",
  nav_settings: "Instellingen",
  hero_kicker: "Apparaat voor buitendienst",
  hero_subhead: "Seriële consoles, bestandsbibliotheken, overdrachtsdiensten en referentienotities - voor werk aan netwerkapparatuur, overal.",
  kicker_live: "Live",
  theme_dark: "Donker",
  theme_light: "Licht",
  serial_consoles: "Seriële consoles",
  open_console_1: "Console 1 openen",
  open_console_2: "Console 2 openen",
  popup_note: "Elke console opent in een eigen verplaatsbaar pop-upvenster voor gebruik in het veld.",
  quick_access: "Snelle toegang",
  jump_console: "Naar console",
  browse_files: "Bestanden bekijken",
  raw_exports: "Ruwe exports",
  open_settings: "Instellingen openen",
  reference_docs: "Referentiedocumentatie",
  docs_note: "Lokaal op de kit opgeslagen beknopte leveranciersreferenties.",
  docs_index: "Documentatie-index openen",
  upload_title: "Uploaden",
  destination: "Bestemming",
  upload_file: "Bestand uploaden",
  subnet_calculator: "Subnetcalculator",
  subnet_note: "Bereken IPv4-netwerkdetails voor veldadressering en overdrachtsnotities.",
  ip_address: "IP-adres",
  cidr_prefix: "CIDR-prefix",
  calculate: "Berekenen",
  subnet_invalid_ip: "Voer een IPv4-adres in zoals 192.168.200.120.",
  subnet_invalid_prefix: "Voer een CIDR-prefix in van 0 tot 32.",
  subnet_network: "Netwerk",
  subnet_netmask: "Netmasker",
  subnet_wildcard: "Wildcard",
  subnet_broadcast: "Broadcast",
  subnet_host_range: "Bruikbaar bereik",
  subnet_hosts: "Bruikbare hosts",
  subnet_single_host: "Route voor één host",
  subnet_point_to_point: "Point-to-pointbereik",
  settings_title: "Instellingen",
  appliance_controls: "Apparaatbediening",
  settings_subhead: "Verbindingsstatus, netwerkconfiguratie, wachtwoordwijzigingen en seriële console-instellingen.",
  networking: "Netwerk",
  transfer_services: "Overdrachtsdiensten",
  serial_presets: "Seriële presets",
  password: "Wachtwoord",
  operational_notes: "Operationele notities",
  export_browser: "Exportbrowser",
  open_local_shell: "Lokale shell openen",
  full_serial_profiles: "Volledige seriële profielen",
  open_readme: "README openen",
  back_to_console: "Terug naar console",
  connectivity: "Connectiviteit",
  active_links: "Actieve verbindingen",
  nearby_wifi: "Wifi in de buurt",
  hostname: "Hostnaam",
  ethernet_mode: "Ethernet-modus",
  static: "Statisch",
  ethernet_address: "Ethernet-adres",
  wifi_mode: "Wifi-modus",
  wifi_ssid: "Wifi-SSID",
  wifi_password: "Wifi-AP-wachtwoord",
  wifi_access_note: "Apple-apparaten bereiken de interface op http://{hostname}.local/ terwijl ze verbonden zijn met het Fieldkit-AP. Directe terugvaloptie: http://10.42.0.1/",
  disabled: "Uitgeschakeld",
  client: "Client",
  save_network_settings: "Netwerk opslaan",
  apply_network_settings: "Netwerk toepassen",
  network_apply_note: "Netwerk toepassen slaat de huidige formulierwaarden op en voert de echte netwerkwijziging op het apparaat uit.",
  applying_network_settings: "Netwerkinstellingen worden toegepast...",
  network_apply_failed: "Toepassen van netwerk mislukt: {message}",
  transfer_services_title: "Overdrachtsdiensten",
  http_export_access: "HTTP-exporttoegang",
  tftp_access: "TFTP-toegang",
  ftp_access: "FTP-toegang",
  apply_transfer_services: "Overdrachtsdiensten toepassen",
  transfer_services_note: "HTTP-exporttoegang biedt alleen /fieldkit op poort 80 voor apparaatdownloads. FTP en TFTP blijven uit totdat ze hier worden ingeschakeld. SCP blijft beschikbaar via de normale SSH-dienst.",
  serial_settings: "Seriële instellingen",
  console_1_preset: "Preset Console 1",
  console_2_preset: "Preset Console 2",
  custom: "Aangepast",
  save_serial_settings: "Seriële instellingen opslaan",
  serial_settings_note: "Gebruik voor afwijkende baudrate, pariteit, stopbits of apparaatpaden de seriële profielen.",
  change_password: "Wachtwoord wijzigen",
  current_password: "Huidig wachtwoord",
  new_password: "Nieuw wachtwoord",
  files_title: "Bestanden",
  files_note: "Blader door de lokale bestandsbibliotheken op de kit.",
  upload_from_desktop: "Uploaden vanaf desktop",
  upload_current_library: "Naar huidige bibliotheek uploaden",
  exports_title: "Fieldkit-exports",
  export_root_note: "TFTP, FTP en SCP gebruiken dezelfde bibliotheekstructuur met root {root}.",
  up_one_level: "Een niveau omhoog",
  docs_title: "Fieldkit-referentienotities",
  docs_intro: "Beginners-commandoreferenties voor gangbare leveranciersplatforms.",
  back_to_docs: "Terug naar documentatie-index",
  serial_profiles_title: "Seriële profielen",
  serial_profiles_note: "Seriële adapters worden standaard automatisch gedetecteerd. Zet een console vast op een stabiele adapter zodat deze hetzelfde snoer behoudt na herstarts en opnieuw aansluiten.",
  label: "Label",
  device_preference: "Apparaatvoorkeur",
  device_auto: "Automatisch detecteren (laagste poort)",
  device_not_detected: "(niet gedetecteerd)",
  device_not_present: "Geen adapter gedetecteerd voor deze console.",
  resolved_to: "Opgelost",
  pinned: "vastgezet",
  pin_console: "Vastzetten",
  unpinned: "automatisch",
  baud_rate: "Baudsnelheid",
  data_bits: "Databits",
  parity: "Pariteit",
  stop_bits: "Stopbits",
  none: "Geen",
  even: "Even",
  odd: "Oneven",
  console_1: "Console 1",
  console_2: "Console 2",
  save_serial_profiles: "Seriële profielen opslaan",
  upload_failed: "Upload mislukt",
  saved_to: "{name} opgeslagen naar {library}",
  uploads_not_allowed: "Uploads naar {library} zijn niet toegestaan.",
  uploads_managed_by_server: "Uploads voor leveranciersgegevens worden door de server beheerd.",
  no_entries: "Geen items",
  directory_path: "map: {path}",
  download: "Downloaden",
  copy_to_usb: "Naar USB kopiëren",
  copying_to_usb: "{name} wordt naar USB gekopieerd…",
  copied_to_usb: "{name} naar USB gekopieerd ({destination}).",
  on_usb: "Op USB",
  copy_failed: "Kopiëren mislukt",
  usb_not_mounted: "Er is geen USB-opslag op de kit gekoppeld.",
  usb_copy_running: "Er loopt al een kopie.",
  delete: "Verwijderen",
  reset: "Resetten",
  delete_confirm: "{path} uit {library} verwijderen?",
  delete_failed: "Verwijderen mislukt",
  no_files: "Geen bestanden",
  directory: "Map",
  preset: "Preset",
  preset_title: "Seriële lijnpreset voor {label}",
  reset_session: "Sessie resetten",
  reset_session_title: "Sessie {label} resetten",
  bytes: "{size} bytes",
  secure: "beveiligd",
  preferred: "voorkeur",
  auto_detect: "automatisch",
  unavailable: "niet beschikbaar",
  yes: "Ja",
  no: "Nee",
  root_label: "Root",
  http_export_label: "HTTP-export",
  usb_gadget_label: "USB-gadget-export",
  configured: "geconfigureerd",
  active: "actief",
  enabled: "ingeschakeld",
  built_in_over_ssh: "ingebouwd via SSH",
  popup_blocked: "Pop-up geblokkeerd voor Console {index}. Sta pop-ups toe voor deze site.",
  serial_preset_saving: "Seriële preset wordt opgeslagen...",
  serial_set: "{label} ingesteld op {baud} 8N1.",
  serial_preset_save_failed: "Opslaan van seriële preset mislukt: {message}",
  resetting_console: "Console {index} wordt gereset...",
  console_reset: "Sessie van Console {index} gereset.",
  console_no_session: "Console {index} had geen actieve sessie om te resetten.",
  console_reset_failed: "Resetten van console mislukt: {message}",
  reconnect: "Opnieuw verbinden",
  opening_session: "Sessie wordt geopend...",
  connecting: "Verbinden...",
  reconnecting: "Opnieuw verbinden...",
  connected: "Verbonden",
  disconnected: "Verbroken",
  connecting_to_console: "Verbinden met console {index}...",
  console_disconnected: "Console verbroken",
  console_window_title: "Console {index}",
  console_move_note: "Deze pop-up kan onafhankelijk door de field engineer worden verplaatst.",
  console_capture_note: "Toetsenbordinvoer wordt direct in dit venster vastgelegd. Klik op het terminalgebied als de focus verloren gaat.",
  applying_transfer_services: "Instellingen voor overdrachtsdiensten worden toegepast...",
  transfer_apply_failed: "Toepassen van overdrachtsdiensten mislukt: {message}",
  password_change_accepted: "Wachtwoord gewijzigd voor het lokale serviceaccount.",
  password_change_rejected: "Wachtwoordwijziging geweigerd.",
  local_shell_title: "Lokale Pi-shell",
  local_shell_note: "Deze terminal draait rechtstreeks op het Fieldkit-apparaat als het lokale serviceaccount.",
  serial_profiles_saved: "Seriële profielen opgeslagen.",
  serial_profile_save_failed: "Opslaan van serieel profiel mislukt.",
  failed_load_profiles: "Seriële profielen konden niet worden geladen: {message}",
  input_voltage_ok: "Ingangsspanning: OK",
  input_voltage_low_now: "Ingangsspanning: LAAG",
  input_voltage_low_seen: "Ingangsspanning: LAAG GEZIEN",
  input_voltage_unavailable: "Ingangsspanning niet beschikbaar",
};
TRANSLATIONS.fr = { ...TRANSLATIONS.en,
  nav_home: "Accueil",
  nav_console: "Console",
  nav_files: "Fichiers",
  nav_tools: "Outils",
  nav_settings: "Paramètres",
  hero_kicker: "Appareil de service terrain",
  hero_subhead: "Consoles série, bibliothèques de fichiers, services de transfert et notes de référence - pour travailler sur des équipements réseau partout.",
  kicker_live: "En direct",
  theme_dark: "Sombre",
  theme_light: "Clair",
  serial_consoles: "Consoles série",
  open_console_1: "Ouvrir la console 1",
  open_console_2: "Ouvrir la console 2",
  popup_note: "Chaque console s'ouvre dans sa propre fenêtre contextuelle mobile pour le terrain.",
  quick_access: "Accès rapide",
  jump_console: "Aller à la console",
  browse_files: "Parcourir les fichiers",
  raw_exports: "Exports bruts",
  open_settings: "Ouvrir les paramètres",
  reference_docs: "Documentation de référence",
  docs_note: "Sujets de référence fournisseurs stockés localement sur le kit.",
  docs_index: "Ouvrir l'index de documentation",
  upload_title: "Envoyer",
  destination: "Destination",
  upload_file: "Envoyer un fichier",
  subnet_calculator: "Calculateur de sous-réseau",
  subnet_note: "Calculez les détails IPv4 pour l'adressage terrain et les notes de passation.",
  ip_address: "Adresse IP",
  cidr_prefix: "Préfixe CIDR",
  calculate: "Calculer",
  subnet_invalid_ip: "Saisissez une adresse IPv4 comme 192.168.200.120.",
  subnet_invalid_prefix: "Saisissez un préfixe CIDR de 0 à 32.",
  subnet_network: "Réseau",
  subnet_netmask: "Masque de sous-réseau",
  subnet_wildcard: "Joker",
  subnet_broadcast: "Diffusion",
  subnet_host_range: "Plage utilisable",
  subnet_hosts: "Hôtes utilisables",
  subnet_single_host: "Route d'hôte unique",
  subnet_point_to_point: "Plage point à point",
  settings_title: "Paramètres",
  appliance_controls: "Contrôles de l'appareil",
  settings_subhead: "État de connectivité, configuration réseau, changement de mot de passe et paramètres des consoles série.",
  networking: "Réseau",
  transfer_services: "Services de transfert",
  serial_presets: "Préréglages série",
  password: "Mot de passe",
  operational_notes: "Notes opérationnelles",
  export_browser: "Navigateur d'exports",
  open_local_shell: "Ouvrir le shell local",
  full_serial_profiles: "Profils série complets",
  open_readme: "Ouvrir le README",
  back_to_console: "Retour à la console",
  connectivity: "Connectivité",
  active_links: "Liens actifs",
  nearby_wifi: "Wi-Fi à proximité",
  hostname: "Nom d'hôte",
  ethernet_mode: "Mode Ethernet",
  static: "Statique",
  ethernet_address: "Adresse Ethernet",
  wifi_mode: "Mode Wi-Fi",
  wifi_ssid: "SSID Wi-Fi",
  wifi_password: "Mot de passe du point d'accès Wi-Fi",
  wifi_access_note: "Les appareils Apple peuvent accéder à l'interface via http://{hostname}.local/ lorsqu'ils sont connectés au point d'accès Fieldkit. Solution directe : http://10.42.0.1/",
  disabled: "Désactivé",
  client: "Client",
  save_network_settings: "Enregistrer le réseau",
  apply_network_settings: "Appliquer le réseau",
  network_apply_note: "Appliquer le réseau enregistre les valeurs du formulaire et exécute le changement réseau réel sur l'appareil.",
  applying_network_settings: "Application des paramètres réseau...",
  network_apply_failed: "Échec de l'application du réseau : {message}",
  transfer_services_title: "Services de transfert",
  http_export_access: "Accès export HTTP",
  tftp_access: "Accès TFTP",
  ftp_access: "Accès FTP",
  apply_transfer_services: "Appliquer les services",
  transfer_services_note: "L'accès export HTTP n'expose que /fieldkit sur le port 80 pour les téléchargements d'appareils. FTP et TFTP restent désactivés jusqu'à leur activation ici. SCP reste disponible via le service SSH normal.",
  serial_settings: "Paramètres série",
  console_1_preset: "Préréglage console 1",
  console_2_preset: "Préréglage console 2",
  custom: "Personnalisé",
  save_serial_settings: "Enregistrer les paramètres série",
  serial_settings_note: "Pour un débit, une parité, des bits d'arrêt ou des chemins d'appareil non standard, utilisez les profils série.",
  change_password: "Changer le mot de passe",
  current_password: "Mot de passe actuel",
  new_password: "Nouveau mot de passe",
  files_title: "Fichiers",
  files_note: "Parcourez les bibliothèques de fichiers locales du kit.",
  upload_from_desktop: "Envoyer depuis le bureau",
  upload_current_library: "Envoyer vers la bibliothèque actuelle",
  exports_title: "Exports Fieldkit",
  export_root_note: "TFTP, FTP et SCP utilisent la même structure de bibliothèques avec la racine {root}.",
  up_one_level: "Niveau supérieur",
  docs_title: "Notes de référence Fieldkit",
  docs_intro: "Références de commandes de départ pour les plateformes fournisseurs courantes.",
  back_to_docs: "Retour à l'index de documentation",
  serial_profiles_title: "Profils série",
  serial_profiles_note: "Les adaptateurs série sont détectés automatiquement par défaut. Fixez une console à un adaptateur stable pour qu'elle conserve le même câble après les redémarrages et rebranchements.",
  label: "Libellé",
  device_preference: "Préférence d'appareil",
  device_auto: "Détection automatique (port le plus bas)",
  device_not_detected: "(non détecté)",
  device_not_present: "Aucun adaptateur détecté pour cette console.",
  resolved_to: "Résolu",
  pinned: "épinglé",
  pin_console: "Épingler",
  unpinned: "automatique",
  baud_rate: "Débit en bauds",
  data_bits: "Bits de données",
  parity: "Parité",
  stop_bits: "Bits d'arrêt",
  none: "Aucune",
  even: "Pair",
  odd: "Impair",
  console_1: "Console 1",
  console_2: "Console 2",
  save_serial_profiles: "Enregistrer les profils série",
  upload_failed: "Échec de l'envoi",
  saved_to: "{name} enregistré dans {library}",
  uploads_not_allowed: "Les envois vers {library} ne sont pas autorisés.",
  uploads_managed_by_server: "Les envois de données fournisseurs sont gérés par le serveur.",
  no_entries: "Aucune entrée",
  directory_path: "répertoire : {path}",
  download: "Télécharger",
  copy_to_usb: "Copier vers USB",
  copying_to_usb: "Copie de {name} vers USB…",
  copied_to_usb: "{name} copié vers USB ({destination}).",
  on_usb: "Sur USB",
  copy_failed: "Échec de la copie",
  usb_not_mounted: "Aucun stockage USB n'est monté sur le kit.",
  usb_copy_running: "Une copie est déjà en cours.",
  delete: "Supprimer",
  reset: "Réinitialiser",
  delete_confirm: "Supprimer {path} de {library} ?",
  delete_failed: "Échec de la suppression",
  no_files: "Aucun fichier",
  directory: "Répertoire",
  preset: "Préréglage",
  preset_title: "Préréglage de ligne série {label}",
  reset_session: "Réinitialiser la session",
  reset_session_title: "Réinitialiser la session {label}",
  bytes: "{size} octets",
  secure: "sécurisé",
  preferred: "préféré",
  auto_detect: "automatique",
  unavailable: "indisponible",
  yes: "Oui",
  no: "Non",
  root_label: "Racine",
  http_export_label: "Export HTTP",
  usb_gadget_label: "Export USB Gadget",
  configured: "configuré",
  active: "actif",
  enabled: "activé",
  built_in_over_ssh: "intégré via SSH",
  popup_blocked: "Fenêtre contextuelle bloquée pour la console {index}. Autorisez les fenêtres contextuelles pour ce site.",
  serial_preset_saving: "Enregistrement du préréglage série...",
  serial_set: "{label} réglée sur {baud} 8N1.",
  serial_preset_save_failed: "Échec de l'enregistrement du préréglage série : {message}",
  resetting_console: "Réinitialisation de la console {index}...",
  console_reset: "Session de la console {index} réinitialisée.",
  console_no_session: "La console {index} n'avait aucune session active à réinitialiser.",
  console_reset_failed: "Échec de la réinitialisation de la console : {message}",
  reconnect: "Reconnecter",
  opening_session: "Ouverture de la session...",
  connecting: "Connexion...",
  reconnecting: "Reconnexion...",
  connected: "Connecté",
  disconnected: "Déconnecté",
  connecting_to_console: "Connexion à la console {index}...",
  console_disconnected: "Console déconnectée",
  console_window_title: "Console {index}",
  console_move_note: "Cette fenêtre peut être déplacée indépendamment par l'ingénieur terrain.",
  console_capture_note: "La saisie clavier est capturée directement dans cette fenêtre. Cliquez dans la zone du terminal si le focus est perdu.",
  applying_transfer_services: "Application des paramètres des services de transfert...",
  transfer_apply_failed: "Échec de l'application des services de transfert : {message}",
  password_change_accepted: "Mot de passe modifié pour le compte de service local.",
  password_change_rejected: "Changement de mot de passe refusé.",
  local_shell_title: "Shell local du Pi",
  local_shell_note: "Ce terminal s'exécute directement sur l'appareil Fieldkit en tant que compte de service local.",
  serial_profiles_saved: "Profils série enregistrés.",
  serial_profile_save_failed: "Échec de l'enregistrement du profil série.",
  failed_load_profiles: "Échec du chargement des profils série : {message}",
  input_voltage_ok: "Tension d'entrée : OK",
  input_voltage_low_now: "Tension d'entrée : FAIBLE",
  input_voltage_low_seen: "Tension d'entrée : FAIBLE DÉTECTÉE",
  input_voltage_unavailable: "Tension d'entrée indisponible",
};
function flagEmoji(countryCode) {
  return countryCode
    .toUpperCase()
    .split("")
    .map((char) => String.fromCodePoint(127397 + char.charCodeAt(0)))
    .join("");
}

function currentLanguage() {
  const saved = window.localStorage.getItem(STORAGE_KEYS.language) || "en";
  return LANGUAGES[saved] ? saved : "en";
}

function t(key, vars = {}) {
  const language = currentLanguage();
  const table = TRANSLATIONS[language] || TRANSLATIONS.en;
  const template = table[key] || TRANSLATIONS.en[key] || key;
  return template.replace(/\{(\w+)\}/g, (_, name) => String(vars[name] ?? ""));
}

function applyTheme(theme) {
  const resolved = theme === "dark" ? "dark" : "light";
  document.documentElement.dataset.theme = resolved;
  window.localStorage.setItem(STORAGE_KEYS.theme, resolved);
  const target = document.getElementById("theme-toggle-icon");
  const button = document.getElementById("theme-toggle");
  if (target) {
    target.textContent = resolved === "dark" ? "☀" : "☾";
  }
  if (button) {
    button.setAttribute("aria-label", resolved === "dark" ? t("theme_light") : t("theme_dark"));
    button.setAttribute("title", resolved === "dark" ? t("theme_light") : t("theme_dark"));
  }
}

function translateStaticContent(root = document) {
  root.querySelectorAll("[data-i18n]").forEach((node) => {
    node.textContent = t(node.dataset.i18n);
  });
  root.querySelectorAll("[data-i18n-placeholder]").forEach((node) => {
    node.setAttribute("placeholder", t(node.dataset.i18nPlaceholder));
  });
  const lang = currentLanguage();
  document.documentElement.lang = lang;
  const flag = document.getElementById("language-flag");
  const label = document.getElementById("language-label");
  if (flag) {
    flag.textContent = flagEmoji(LANGUAGES[lang].flag);
  }
  if (label) {
    label.textContent = LANGUAGES[lang].label;
  }
  const themeTarget = document.getElementById("theme-toggle-icon");
  if (themeTarget) {
    themeTarget.textContent = document.documentElement.dataset.theme === "dark" ? "☀" : "☾";
  }
}

function yesNo(value) {
  return value ? t("yes") : t("no");
}

function parseIpv4Address(value) {
  const parts = value.trim().split(".");
  if (parts.length !== 4) {
    return null;
  }
  const octets = parts.map((part) => {
    if (!/^\d{1,3}$/.test(part)) {
      return null;
    }
    const octet = Number(part);
    return octet >= 0 && octet <= 255 ? octet : null;
  });
  if (octets.some((octet) => octet === null)) {
    return null;
  }
  return (((octets[0] << 24) >>> 0) + (octets[1] << 16) + (octets[2] << 8) + octets[3]) >>> 0;
}

function formatIpv4Address(value) {
  return [
    (value >>> 24) & 255,
    (value >>> 16) & 255,
    (value >>> 8) & 255,
    value & 255,
  ].join(".");
}

function calculateSubnet(addressValue, prefixValue) {
  const cidrParts = addressValue.trim().split("/");
  if (cidrParts.length > 2) {
    throw new Error(t("subnet_invalid_ip"));
  }
  const [addressText, inlinePrefix] = cidrParts;
  const address = parseIpv4Address(addressText);
  if (address === null) {
    throw new Error(t("subnet_invalid_ip"));
  }
  const prefixText = inlinePrefix === undefined ? String(prefixValue).trim() : inlinePrefix.trim();
  if (!/^\d{1,2}$/.test(prefixText)) {
    throw new Error(t("subnet_invalid_prefix"));
  }
  const prefix = Number(prefixText);
  if (prefix < 0 || prefix > 32) {
    throw new Error(t("subnet_invalid_prefix"));
  }
  const mask = prefix === 0 ? 0 : (0xffffffff << (32 - prefix)) >>> 0;
  const wildcard = (~mask) >>> 0;
  const network = (address & mask) >>> 0;
  const broadcast = (network | wildcard) >>> 0;
  const totalHosts = 2 ** (32 - prefix);
  const usableHosts = prefix === 32 ? 1 : prefix === 31 ? 2 : Math.max(totalHosts - 2, 0);
  const firstHost = prefix >= 31 ? network : (network + 1) >>> 0;
  const lastHost = prefix >= 31 ? broadcast : (broadcast - 1) >>> 0;
  const hostRange = prefix === 32 ? formatIpv4Address(network) : `${formatIpv4Address(firstHost)} - ${formatIpv4Address(lastHost)}`;
  return {
    prefix,
    network: `${formatIpv4Address(network)}/${prefix}`,
    netmask: formatIpv4Address(mask),
    wildcard: formatIpv4Address(wildcard),
    broadcast: formatIpv4Address(broadcast),
    hostRange,
    usableHosts: usableHosts.toLocaleString(),
  };
}

function renderSubnetResult(result) {
  const target = document.getElementById("subnet-results");
  if (!target) {
    return;
  }
  const rows = [
    [t("subnet_network"), result.network],
    [t("subnet_netmask"), result.netmask],
    [t("subnet_wildcard"), result.wildcard],
    [t("subnet_broadcast"), result.broadcast],
    [t("subnet_host_range"), result.hostRange],
    [t("subnet_hosts"), result.usableHosts],
  ];
  target.innerHTML = rows.map(([label, value]) => `<div><dt>${escapeHtml(label)}</dt><dd>${escapeHtml(value)}</dd></div>`).join("");
}

function updateSubnetCalculator(event) {
  event?.preventDefault();
  const addressInput = document.getElementById("subnet-ip");
  const prefixInput = document.getElementById("subnet-prefix");
  const errorTarget = document.getElementById("subnet-error");
  if (!addressInput || !prefixInput || !errorTarget) {
    return;
  }
  try {
    const result = calculateSubnet(addressInput.value, prefixInput.value);
    prefixInput.value = String(result.prefix);
    errorTarget.textContent = "";
    renderSubnetResult(result);
  } catch (error) {
    errorTarget.textContent = error.message;
    renderSubnetResult({
      network: "",
      netmask: "",
      wildcard: "",
      broadcast: "",
      hostRange: "",
      usableHosts: "",
    });
  }
}

function setLanguage(language) {
  if (!LANGUAGES[language]) {
    return;
  }
  window.localStorage.setItem(STORAGE_KEYS.language, language);
  translateStaticContent();
  window.dispatchEvent(new CustomEvent("fieldkit:language-change", { detail: { language } }));
}

function renderTopbar() {
  document.querySelectorAll("[data-topbar]").forEach((target) => {
    const docsHref = target.dataset.docsHref || "/#docs";
    const exportsHref = target.dataset.exportsHref || null;
    const exportsLink = exportsHref
      ? `<a href="${exportsHref}" data-i18n="raw_exports">Exports</a>`
      : "";
    const path = window.location.pathname;
    const active = (href) => {
      if (href.startsWith("/#")) {
        return "";
      }
      const linkPath = href.split("#")[0];
      return linkPath === path || (linkPath !== "/" && path.startsWith(linkPath)) ? " active" : "";
    };
    target.innerHTML = `
      <nav class="topbar">
        <div class="brand-mark">
          <span>Fieldkit</span>
          <span id="app-version" class="brand-version"></span>
        </div>
        <button id="nav-burger" type="button" class="nav-burger" aria-label="Menu" aria-expanded="false">☰</button>
        <div class="topbar-right">
          <div class="topbar-links">
            <a href="/" data-i18n="nav_home" class="${active("/")}">Home</a>
            <a href="/#serial" data-i18n="nav_console">Console</a>
            <a href="/files" data-i18n="nav_files" class="${active("/files")}">Files</a>
            <a href="/server-sync" class="${active("/server-sync")}"><span data-i18n="nav_server_sync">Server Sync</span> <small class="nav-beta">beta</small></a>
            ${exportsLink}
            <a href="${docsHref}" data-i18n="nav_docs" class="${active(docsHref)}">Docs</a>
            <a href="/tools" data-i18n="nav_tools" class="${active("/tools")}">Tools</a>
            <a href="/settings" data-i18n="nav_settings" class="${active("/settings")}">Settings</a>
            <a href="/readme" data-i18n="nav_readme" class="${active("/readme")}">README</a>
          </div>
          <div class="shell-tools">
            <button id="theme-toggle" type="button" class="shell-tool-button theme-icon-button" aria-label="Toggle theme" title="Toggle theme"><span id="theme-toggle-icon" aria-hidden="true">◐</span></button>
            <div class="language-picker">
              <button id="language-toggle" type="button" class="language-button" aria-haspopup="true" aria-expanded="false">
                <span id="language-flag" class="language-flag">🇬🇧</span>
                <span id="language-label">English</span>
              </button>
              <div class="language-options">
                <button type="button" data-language="en"><span class="language-flag">🇬🇧</span><span>English</span></button>
                <button type="button" data-language="es"><span class="language-flag">🇪🇸</span><span>Espanol</span></button>
                <button type="button" data-language="de"><span class="language-flag">🇩🇪</span><span>Deutsch</span></button>
                <button type="button" data-language="nl"><span class="language-flag">🇳🇱</span><span>Nederlands</span></button>
                <button type="button" data-language="fr"><span class="language-flag">🇫🇷</span><span>Francais</span></button>
              </div>
            </div>
          </div>
        </div>
      </nav>`;
  });
}

function bindTopbarBurger() {
  const topbar = document.querySelector(".topbar");
  const burger = document.getElementById("nav-burger");
  if (!topbar || !burger) {
    return;
  }
  burger.addEventListener("click", (event) => {
    event.preventDefault();
    const open = topbar.classList.toggle("nav-open");
    burger.setAttribute("aria-expanded", open ? "true" : "false");
    burger.textContent = open ? "✕" : "☰";
  });
  document.addEventListener("click", (event) => {
    if (!topbar.classList.contains("nav-open") || topbar.contains(event.target)) {
      return;
    }
    topbar.classList.remove("nav-open");
    burger.setAttribute("aria-expanded", "false");
    burger.textContent = "☰";
  });
  document.addEventListener("keydown", (event) => {
    if (event.key !== "Escape" || !topbar.classList.contains("nav-open")) {
      return;
    }
    topbar.classList.remove("nav-open");
    burger.setAttribute("aria-expanded", "false");
    burger.textContent = "☰";
  });
}

async function checkForUpdates() {
  const status = document.getElementById("update-status");
  const applyButton = document.getElementById("update-apply-button");
  if (status) {
    status.textContent = "Checking for updates…";
  }
  try {
    const payload = await getJson("/api/system/update/latest", { timeoutMs: 30000 });
    lastUpdatePayload = payload;
    const local = document.getElementById("update-local-version");
    if (local) {
      local.textContent = payload.local_version || "unknown";
    }
    if (!payload.available) {
      if (status) {
        status.textContent = payload.error || "This appliance is up to date.";
      }
      if (applyButton) {
        applyButton.hidden = true;
      }
      return;
    }
    if (payload.update_available) {
      if (status) {
        status.textContent = `Version ${payload.latest_version} is available (published ${payload.published_at || "recently"}).`;
      }
      if (applyButton) {
        applyButton.hidden = false;
        applyButton.textContent = `Apply update ${payload.latest_version}`;
      }
    } else {
      if (status) {
        status.textContent = `Up to date (latest: ${payload.latest_version}).`;
      }
      if (applyButton) {
        applyButton.hidden = true;
      }
    }
  } catch (error) {
    lastUpdatePayload = null;
    if (status) {
      status.textContent = error.message;
    }
  }
}

async function applyUpdate() {
  if (!lastUpdatePayload?.update_available) {
    return;
  }
  const status = document.getElementById("update-status");
  const applyButton = document.getElementById("update-apply-button");
  if (status) {
    status.textContent = `Applying update ${lastUpdatePayload.latest_version}… the appliance restarts briefly.`;
  }
  if (applyButton) {
    applyButton.disabled = true;
  }
  try {
    await getJson("/api/system/update/apply", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        version: lastUpdatePayload.latest_version,
        url: lastUpdatePayload.url,
        sha256: lastUpdatePayload.sha256,
      }),
    });
    if (status) {
      status.textContent = "Update started. The page will reload when the appliance is back.";
    }
    setTimeout(() => window.location.reload(), 15000);
  } catch (error) {
    if (status) {
      status.textContent = error.message;
    }
    if (applyButton) {
      applyButton.disabled = false;
    }
  }
}

function initializeShellControls() {
  renderTopbar();
  bindTopbarBurger();
  applyTheme(window.localStorage.getItem(STORAGE_KEYS.theme) || "light");
  translateStaticContent();
  document.getElementById("theme-toggle")?.addEventListener("click", () => {
    applyTheme(document.documentElement.dataset.theme === "dark" ? "light" : "dark");
  });
  const picker = document.querySelector(".language-picker");
  const toggle = document.getElementById("language-toggle");
  toggle?.addEventListener("click", (event) => {
    event.preventDefault();
    if (!picker) {
      return;
    }
    const opening = !picker.classList.contains("open");
    picker.classList.toggle("open", opening);
    toggle.setAttribute("aria-expanded", opening ? "true" : "false");
  });
  document.querySelectorAll("[data-language]").forEach((button) => {
    button.addEventListener("click", (event) => {
      event.preventDefault();
      setLanguage(button.dataset.language);
      if (picker) {
        picker.classList.remove("open");
      }
      toggle?.setAttribute("aria-expanded", "false");
    });
  });
  document.addEventListener("click", (event) => {
    if (!picker || picker.contains(event.target)) {
      return;
    }
    picker.classList.remove("open");
    toggle?.setAttribute("aria-expanded", "false");
  });
  document.addEventListener("keydown", (event) => {
    if (event.key !== "Escape" || !picker?.classList.contains("open")) {
      return;
    }
    picker.classList.remove("open");
    toggle?.setAttribute("aria-expanded", "false");
  });
}

async function getJson(url, options = {}) {
  const { timeoutMs = 10000, ...fetchOptions } = options;
  const controller = new AbortController();
  const timeoutId = window.setTimeout(() => controller.abort(), timeoutMs);
  let response;
  try {
    response = await fetch(url, { ...fetchOptions, signal: controller.signal });
  } catch (error) {
    window.clearTimeout(timeoutId);
    if (error.name === "AbortError") {
      throw new Error(`Request timed out: ${url}`);
    }
    throw error;
  }
  window.clearTimeout(timeoutId);
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }
  return response.json();
}

let currentSettings = null;
let lastSerialStatus = null;
let lastUpdatePayload = null;
const consoleWindows = new Map();

function serialPresetValue(profile) {
  if (!profile) {
    return "9600-8n1";
  }
  if (profile.baud_rate === 9600 && profile.data_bits === 8 && profile.parity === "none" && profile.stop_bits === 1) {
    return "9600-8n1";
  }
  if (profile.baud_rate === 115200 && profile.data_bits === 8 && profile.parity === "none" && profile.stop_bits === 1) {
    return "115200-8n1";
  }
  return "custom";
}

function applySerialPreset(profile, preset) {
  if (preset === "custom") {
    return { ...profile };
  }
  return {
    ...profile,
    baud_rate: preset === "115200-8n1" ? 115200 : 9600,
    data_bits: 8,
    parity: "none",
    stop_bits: 1,
  };
}

function defaultSerialPorts() {
  return [
    {
      label: "Console 1",
      device_hint: "",
      baud_rate: 9600,
      data_bits: 8,
      parity: "none",
      stop_bits: 1,
    },
    {
      label: "Console 2",
      device_hint: "",
      baud_rate: 9600,
      data_bits: 8,
      parity: "none",
      stop_bits: 1,
    },
  ];
}

async function loadMeta() {
  const versionTarget = document.getElementById("app-version");
  if (!versionTarget) {
    return;
  }
  const response = await fetch("/openapi.json");
  if (!response.ok) {
    return;
  }
  const schema = await response.json();
  versionTarget.textContent = `v${schema.info.version}`;
}

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, (ch) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
  })[ch]);
}

function renderKeyValue(target, data) {
  if (!target) {
    return;
  }
  target.innerHTML = Object.entries(data)
    .map(([key, value]) => {
      const text = typeof value === "object" ? JSON.stringify(value) : value;
      return `<p><strong>${escapeHtml(key)}</strong>: ${escapeHtml(text)}</p>`;
    })
    .join("");
}

function renderList(target, items, formatter) {
  if (!target) {
    return;
  }
  target.innerHTML = items.map(formatter).join("") || `<li>${t("no_entries")}</li>`;
}

function serialDeviceLabel(session) {
  const tty = session.tty_device || session.active_device;
  if (tty) {
    return session.serial ? `${session.serial} · ${tty}` : tty;
  }
  if (session.device_hint) {
    return `${session.device_hint} (${t("preferred")})`;
  }
  return t("auto_detect");
}

async function savePayload(payload) {
  await getJson("/api/settings", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

async function saveQuickSerialPreset(index, preset) {
  const target = document.getElementById("serial-quick-result");
  if (!currentSettings) {
    return;
  }
  target.textContent = t("serial_preset_saving");
  try {
    const serialPorts = (currentSettings.serial_ports?.length ? currentSettings.serial_ports : defaultSerialPorts()).map((profile) => ({ ...profile }));
    serialPorts[index] = applySerialPreset(serialPorts[index] || defaultSerialPorts()[index], preset);
    await savePayload({
      ...currentSettings,
      serial_ports: serialPorts,
    });
    target.textContent = t("serial_set", { label: serialPorts[index].label, baud: serialPorts[index].baud_rate });
    await loadStatus();
  } catch (error) {
    target.textContent = t("serial_preset_save_failed", { message: error.message });
  }
}

function bindQuickSerialPresetControls() {
  document.querySelectorAll("[data-serial-preset-index]").forEach((select) => {
    select.addEventListener("change", (event) => {
      const presetIndex = Number(event.currentTarget.dataset.serialPresetIndex);
      saveQuickSerialPreset(presetIndex, event.currentTarget.value);
    });
  });
}

function bindResetConsoleControls() {
  document.querySelectorAll("[data-reset-console-index]").forEach((button) => {
    button.addEventListener("click", () => {
      const resetIndex = Number(button.dataset.resetConsoleIndex);
      resetConsoleSession(resetIndex);
    });
  });
}

async function resetConsoleSession(index) {
  const target = document.getElementById("serial-reset-result");
  target.textContent = t("resetting_console", { index: index + 1 });
  try {
    const result = await getJson(`/api/serial/reset/${index}`, { method: "POST" });
    const popupWindow = consoleWindows.get(index);
    if (popupWindow && !popupWindow.closed) {
      popupWindow.focus();
    }
    target.textContent = result.reset ? t("console_reset", { index: index + 1 }) : t("console_no_session", { index: index + 1 });
    await loadStatus();
  } catch (error) {
    target.textContent = t("console_reset_failed", { message: error.message });
  }
}

async function loadWifiNetworks() {
  try {
    const wifi = await getJson("/api/connectivity/wifi/networks", { timeoutMs: 5000 });
    renderList(
      document.getElementById("wifi-networks"),
      wifi.networks,
      (network) => `<li>${escapeHtml(network.ssid)} <span class="muted">(${escapeHtml(network.signal)}%${network.secure ? `, ${t("secure")}` : ""})</span></li>`
    );
  } catch (_) {
    renderList(document.getElementById("wifi-networks"), [], () => "");
  }
}

function renderConnectivity(connectivity) {
  if (!connectivity) {
    return;
  }
  renderKeyValue(document.getElementById("connectivity-status"), connectivity);
  const platformNotes = document.getElementById("platform-notes");
  if (platformNotes) {
    platformNotes.textContent = (connectivity.platform?.notes || []).join(" ");
  }
  renderList(
    document.getElementById("active-connections"),
    connectivity.active_connections || [],
    (connection) =>
      `<li><strong>${escapeHtml(connection.device)}</strong> ${escapeHtml(connection.name)} <span class="muted">${escapeHtml(connection.type)}, ${escapeHtml(connection.state)}</span></li>`
  );
}

function renderPowerStatus(system) {
  const target = document.getElementById("footer-power-status");
  if (!target) {
    return;
  }
  const power = system?.power;
  let text = t("input_voltage_unavailable");
  let statusClass = "footer-status-unknown";
  if (power?.supported) {
    if (power.undervoltage_now) {
      text = t("input_voltage_low_now");
      statusClass = "footer-status-bad";
    } else if (power.undervoltage_seen) {
      text = t("input_voltage_low_seen");
      statusClass = "footer-status-warn";
    } else {
      text = t("input_voltage_ok");
      statusClass = "footer-status-ok";
    }
  }
  target.textContent = text;
  target.classList.remove("footer-status-ok", "footer-status-bad", "footer-status-warn", "footer-status-unknown");
  target.classList.add(statusClass);
  if (power?.raw) {
    target.title = `vcgencmd get_throttled: ${power.raw}`;
  } else {
    target.removeAttribute("title");
  }
}

function renderSerial(serial) {
  if (!serial) {
    return;
  }
  renderList(
    document.getElementById("serial-sessions"),
    serial.sessions,
    (session) => {
      const presetValue = escapeHtml(serialPresetValue(session));
      const label = escapeHtml(session.label);
      const deviceLabel = escapeHtml(serialDeviceLabel(session));
      const parity = session.parity === "none" ? "N" : escapeHtml(session.parity[0].toUpperCase());
      const framing = `${escapeHtml(session.baud_rate)} ${escapeHtml(session.data_bits)}${parity}${escapeHtml(session.stop_bits)}`;
      const index = escapeHtml(session.index);
      const presetOptions = [
        '<option value="9600-8n1">9600 8N1</option>',
        '<option value="115200-8n1">115200 8N1</option>',
      ];
      if (presetValue === "custom") {
        presetOptions.unshift(
          `<option value="custom" selected>${t("custom")} (${framing})</option>`
        );
      }
      return `<li>
        <div class="console-row">
          <div class="console-meta">
            <strong>${label}</strong>
            <span class="console-sub">
              <span class="mono">${deviceLabel}</span>
              <span class="chip">${framing}</span>
              ${session.present ? `<span class="chip">${session.bound ? t("pinned") : t("auto_detect")}</span>` : ""}
              ${session.present ? "" : `<span class="chip warn">${t("unavailable")}</span>`}
            </span>
          </div>
          <div class="console-actions">
            <label class="preset-control">
              <span class="control-caption">${t("preset")}</span>
              <select name="serial-preset-${index}" data-serial-preset-index="${index}" title="${escapeHtml(t("preset_title", { label: session.label }))}">
                ${presetOptions.map((option) => option.replace(`value="${presetValue}"`, `value="${presetValue}" selected`)).join("")}
              </select>
            </label>
            <button type="button" class="btn btn-ghost btn-small serial-reset-button" data-reset-console-index="${index}" title="${escapeHtml(t("reset_session_title", { label: session.label }))}">${t("reset_session")}</button>
          </div>
        </div>
      </li>`;
    }
  );

}

function renderSettings(settings, transfers) {
  if (!settings) {
    return;
  }
  currentSettings = settings;
  bindQuickSerialPresetControls();
  bindResetConsoleControls();
  const networkForm = document.getElementById("settings-form");
  const serialForm = document.getElementById("serial-settings-form");
  if (networkForm) {
    networkForm.hostname.value = settings.hostname;
    networkForm.ethernet_mode.value = settings.ethernet.mode;
    networkForm.ethernet_address.value = settings.ethernet.address;
    networkForm.wifi_mode.value = settings.wifi.mode;
    networkForm.wifi_ssid.value = settings.wifi.ssid;
    networkForm.wifi_password.value = settings.wifi.password || "";
  }
  const wifiAccessNote = document.getElementById("wifi-access-note");
  if (wifiAccessNote) {
    wifiAccessNote.textContent = t("wifi_access_note", { hostname: settings.hostname || "fieldkit" });
  }
  if (serialForm) {
    serialForm.console1_preset.value = serialPresetValue(settings.serial_ports[0]);
    serialForm.console2_preset.value = serialPresetValue(settings.serial_ports[1]);
  }
  const transferForm = document.getElementById("transfer-services-form");
  if (transferForm) {
    transferForm.http_export_enabled.checked = Boolean(settings.transfer_services?.http_export_enabled);
    transferForm.tftp_enabled.checked = Boolean(settings.transfer_services?.tftp_enabled);
    transferForm.ftp_enabled.checked = Boolean(settings.transfer_services?.ftp_enabled);
  }
  renderTransfers(transfers);
}

function renderTransfers(transfers) {
  if (!transfers) {
    return;
  }
  const transferForm = document.getElementById("transfer-services-form");
  if (transferForm) {
    transferForm.http_export_enabled.checked = Boolean(currentSettings?.transfer_services?.http_export_enabled);
    transferForm.tftp_enabled.checked = Boolean(currentSettings?.transfer_services?.tftp_enabled);
    transferForm.ftp_enabled.checked = Boolean(currentSettings?.transfer_services?.ftp_enabled);
  }
  const transferStatus = document.getElementById("transfer-status");
  if (transferStatus) {
    const badge = (active) => (active ? '<span class="chip ok">' + t("active") + "</span>" : '<span class="chip">' + t("configured") + "</span>");
    const httpBase = String(transfers.http_base ?? "");
    const httpBaseHtml = /^https?:\/\//i.test(httpBase)
      ? `<a href="${escapeHtml(httpBase)}">${escapeHtml(httpBase)}</a>`
      : escapeHtml(httpBase);
    transferStatus.innerHTML = `
      <div class="transfer-status">
        <p><strong>${t("http_label")}</strong>: ${httpBaseHtml}</p>
        <p><strong>${t("root_label")}</strong>: <span class="mono">${escapeHtml(transfers.root)}</span></p>
        <p><strong>${t("http_export_label")}</strong>: ${t("configured")} ${yesNo(transfers.http_export.configured_enabled)} · ${t("active")} ${yesNo(transfers.http_export.active)} ${badge(transfers.http_export.active)}</p>
        <p><strong>${t("tftp_label")}</strong>: ${t("configured")} ${yesNo(transfers.tftp.configured_enabled)} · ${t("active")} ${yesNo(transfers.tftp.active)} · ${t("enabled")} ${yesNo(transfers.tftp.enabled)} ${badge(transfers.tftp.active)}</p>
        <p><strong>${t("ftp_label")}</strong>: ${t("configured")} ${yesNo(transfers.ftp.configured_enabled)} · ${t("active")} ${yesNo(transfers.ftp.active)} · ${t("enabled")} ${yesNo(transfers.ftp.enabled)} ${badge(transfers.ftp.active)}</p>
        <p><strong>${t("scp_label")}</strong>: ${t("built_in_over_ssh")} · ${t("active")} ${yesNo(transfers.scp.active)} ${badge(transfers.scp.active)}</p>
        <p><strong>${t("usb_gadget_label")}</strong>: ${transfers.usb_gadget.supported ? t("yes") : t("no")} ${escapeHtml(transfers.usb_gadget.model)}</p>
        <p>${escapeHtml(transfers.usb_gadget.note)}</p>
        ${transfers.http_export.note ? `<p>${escapeHtml(transfers.http_export.note)}</p>` : ""}
        ${transfers.tftp.note ? `<p>${escapeHtml(transfers.tftp.note)}</p>` : ""}
        ${transfers.ftp.note ? `<p>${escapeHtml(transfers.ftp.note)}</p>` : ""}
        ${transfers.scp.note ? `<p>${escapeHtml(transfers.scp.note)}</p>` : ""}
      </div>`;
  }
}

async function loadStatus() {
  const results = await Promise.allSettled([
    getJson("/api/system/status", { timeoutMs: 5000 }),
    getJson("/api/connectivity/status", { timeoutMs: 5000 }),
    getJson("/api/serial/sessions", { timeoutMs: 5000 }),
    getJson("/api/settings", { timeoutMs: 5000 }),
    getJson("/api/transfers/status", { timeoutMs: 5000 }),
  ]);

  const [systemResult, connectivityResult, serialResult, settingsResult, transfersResult] = results;
  if (systemResult.status === "fulfilled") {
    renderKeyValue(document.getElementById("system-status"), systemResult.value);
    renderPowerStatus(systemResult.value);
  }
  if (connectivityResult.status === "fulfilled") {
    renderConnectivity(connectivityResult.value);
  }
  if (serialResult.status === "fulfilled") {
    lastSerialStatus = serialResult.value;
    renderSerial(serialResult.value);
  }
  if (settingsResult.status === "fulfilled") {
    renderSettings(
      settingsResult.value,
      transfersResult.status === "fulfilled" ? transfersResult.value : null
    );
  } else if (transfersResult.status === "fulfilled") {
    renderTransfers(transfersResult.value);
  }
  if (!window.fieldkitWifiLoaded) {
    loadWifiNetworks();
    window.fieldkitWifiLoaded = true;
  }
}

function buildSettingsPayload() {
  const networkForm = document.getElementById("settings-form");
  const serialForm = document.getElementById("serial-settings-form");
  const baseSerialPorts = currentSettings?.serial_ports?.length ? currentSettings.serial_ports : defaultSerialPorts();
  const serialPorts = [
    applySerialPreset(baseSerialPorts[0] || defaultSerialPorts()[0], serialForm.console1_preset.value),
    applySerialPreset(baseSerialPorts[1] || defaultSerialPorts()[1], serialForm.console2_preset.value),
  ];
  const ethernet = currentSettings?.ethernet || {};
  const wifi = currentSettings?.wifi || {};
  return {
    ...currentSettings,
    hostname: networkForm.hostname.value,
    ethernet: {
      mode: networkForm.ethernet_mode.value,
      address: networkForm.ethernet_address.value,
      gateway: ethernet.gateway || "",
      dns: ethernet.dns || [],
      interface: ethernet.interface || "eth0",
    },
    wifi: {
      mode: networkForm.wifi_mode.value,
      ssid: networkForm.wifi_ssid.value,
      password: networkForm.wifi_password.value,
      country_code: wifi.country_code || "US",
    },
    serial_ports: serialPorts,
    transfer_services: {
      http_export_enabled: Boolean(document.getElementById("transfer-services-form")?.http_export_enabled.checked),
      tftp_enabled: Boolean(document.getElementById("transfer-services-form")?.tftp_enabled.checked),
      ftp_enabled: Boolean(document.getElementById("transfer-services-form")?.ftp_enabled.checked),
    },
  };
}

async function saveSettings(event) {
  event.preventDefault();
  const payload = buildSettingsPayload();
  await savePayload(payload);
  await loadStatus();
}

async function applyNetworkPlan() {
  const target = document.getElementById("apply-network-result");
  if (target) {
    target.textContent = t("applying_network_settings");
  }
  try {
    const payload = buildSettingsPayload();
    await savePayload(payload);
    const result = await getJson("/api/connectivity/apply", { method: "POST", timeoutMs: 60000 });
    if (target) {
      target.textContent = [...result.notes, ...result.commands].join(" | ");
    }
    await loadStatus();
  } catch (error) {
    if (target) {
      target.textContent = t("network_apply_failed", { message: error.message });
    }
  }
}

async function uploadFile(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const data = new FormData(form);
  const library = form.upload_library.value || "personal";
  const response = await fetch(`/api/files/upload?library=${encodeURIComponent(library)}`, { method: "POST", body: data });
  const result = await response.json().catch(() => ({}));
  if (!response.ok) {
    document.getElementById("upload-result").textContent = result.detail || t("upload_failed");
    return;
  }
  const target = document.getElementById("upload-result");
  if (target) {
    target.textContent = t("saved_to", { name: result.saved, library: result.library });
  }
  if (typeof loadLibrary === "function") {
    await loadLibrary(result.library);
  }
}

async function changePassword(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const response = await fetch("/api/system/password", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      current_password: form.current_password.value,
      new_password: form.new_password.value,
    }),
  });
  const target = document.getElementById("password-result");
  target.textContent = response.ok ? t("password_change_accepted") : t("password_change_rejected");
}

async function applyTransferServices(event) {
  event.preventDefault();
  const target = document.getElementById("transfer-result");
  target.textContent = t("applying_transfer_services");
  try {
    const payload = buildSettingsPayload();
    await savePayload(payload);
    const result = await getJson("/api/transfers/apply", { method: "POST", timeoutMs: 60000 });
    target.textContent = [...result.commands, ...result.notes].join(" | ");
    await loadStatus();
  } catch (error) {
    target.textContent = t("transfer_apply_failed", { message: error.message });
  }
}

function openConsolePopup(index) {
  const existingWindow = consoleWindows.get(index);
  if (existingWindow && !existingWindow.closed) {
    existingWindow.focus();
    return;
  }
  const popup = window.open(
    `/serial-console/${index}`,
    `fieldkit-console-${index}`,
    "popup=yes,width=860,height=640,resizable=yes,scrollbars=no"
  );
  if (!popup) {
    const target = document.getElementById("serial-reset-result");
    if (target) {
      target.textContent = t("popup_blocked", { index: index + 1 });
    }
    return;
  }
  consoleWindows.set(index, popup);
}

window.fieldkitUi = {
  t,
  translateStaticContent,
  initializeShellControls,
  setLanguage,
  applyTheme,
};

initializeShellControls();
document.getElementById("settings-form")?.addEventListener("submit", saveSettings);
document.getElementById("serial-settings-form")?.addEventListener("submit", saveSettings);
document.getElementById("transfer-services-form")?.addEventListener("submit", applyTransferServices);
document.getElementById("upload-form")?.addEventListener("submit", uploadFile);
document.getElementById("password-form")?.addEventListener("submit", changePassword);
document.getElementById("apply-network-button")?.addEventListener("click", applyNetworkPlan);
document.getElementById("open-console-0")?.addEventListener("click", () => openConsolePopup(0));
document.getElementById("open-console-1")?.addEventListener("click", () => openConsolePopup(1));
document.getElementById("subnet-form")?.addEventListener("submit", updateSubnetCalculator);
document.getElementById("subnet-ip")?.addEventListener("input", updateSubnetCalculator);
document.getElementById("subnet-prefix")?.addEventListener("input", updateSubnetCalculator);
document.getElementById("update-check-button")?.addEventListener("click", checkForUpdates);
document.getElementById("update-apply-button")?.addEventListener("click", applyUpdate);
if (document.getElementById("update-check-button")) {
  checkForUpdates();
}
window.addEventListener("fieldkit:language-change", updateSubnetCalculator);
window.addEventListener("fieldkit:language-change", () => {
  if (lastSerialStatus) {
    renderSerial(lastSerialStatus);
    bindQuickSerialPresetControls();
    bindResetConsoleControls();
  }
});
if (document.getElementById("serial-sessions") || document.getElementById("settings-form") || document.getElementById("serial-settings-form")) {
  loadStatus();
}
if (document.getElementById("subnet-form")) {
  updateSubnetCalculator();
}
loadMeta();
