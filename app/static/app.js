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
    nav_docs: "Docs",
    nav_settings: "Settings",
    nav_readme: "README",
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
    wifi_access_note: "Apple devices can reach the GUI at https://{hostname}.local/ while connected to the Fieldkit AP. Direct fallback: https://10.42.0.1/",
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
    serial_profiles_note: "Serial adapters are auto-detected by default. Only set a device preference when you need to pin a console to a specific adapter.",
    label: "Label",
    device_preference: "Device Preference",
    device_optional_0: "Optional: /dev/ttyUSB0",
    device_optional_1: "Optional: /dev/ttyUSB1",
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
    no_entries: "No entries",
    directory_path: "directory: {path}",
    download: "Download",
    delete: "Delete",
    reset: "Reset",
    delete_confirm: "Delete {path} from {library}?",
    delete_failed: "Delete failed",
    no_files: "No files",
    directory: "Directory",
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
  },
};
TRANSLATIONS.es = { ...TRANSLATIONS.en, nav_home: "Inicio", nav_console: "Consola", nav_files: "Archivos", nav_docs: "Docs", nav_settings: "Configuracion", theme_dark: "Oscuro", theme_light: "Claro", serial_consoles: "Consolas seriales", open_console_1: "Abrir Consola 1", open_console_2: "Abrir Consola 2", popup_note: "Cada consola se abre en su propia ventana movible para trabajo en campo.", quick_access: "Acceso rapido", jump_console: "Ir a consola", browse_files: "Explorar archivos", raw_exports: "Exportaciones", open_settings: "Abrir ajustes", reference_docs: "Documentacion", docs_note: "Temas de referencia de fabricantes guardados localmente en el kit.", docs_index: "Abrir indice de docs", upload_title: "Subir", destination: "Destino", upload_file: "Subir archivo", settings_title: "Configuracion", settings_subhead: "Estado de conectividad, red, cambio de contrasena y ajustes de consola serial.", networking: "Red", transfer_services: "Servicios de transferencia", serial_presets: "Perfiles seriales", password: "Contrasena", operational_notes: "Notas operativas", export_browser: "Explorador de exportaciones", open_local_shell: "Abrir shell local", full_serial_profiles: "Perfiles seriales completos", open_readme: "Abrir README", back_to_console: "Volver a consola", connectivity: "Conectividad", active_links: "Enlaces activos", nearby_wifi: "Wi-Fi cercano", hostname: "Hostname", ethernet_mode: "Modo Ethernet", ethernet_address: "Direccion Ethernet", wifi_mode: "Modo Wi-Fi", wifi_ssid: "SSID Wi-Fi", ap: "AP", client: "Cliente", save_network_settings: "Guardar red", apply_network_settings: "Aplicar red", network_apply_note: "Aplicar red guarda los valores actuales y ejecuta el cambio de red real en el appliance.", applying_network_settings: "Aplicando ajustes de red...", network_apply_failed: "La aplicacion de red fallo: {message}", transfer_services_title: "Servicios de transferencia", http_export_access: "Acceso HTTP de exportacion", tftp_access: "Acceso TFTP", ftp_access: "Acceso FTP", apply_transfer_services: "Aplicar servicios", transfer_services_note: "La exportacion HTTP expone solo /fieldkit en puerto 80 para descargas. FTP y TFTP quedan apagados hasta activarlos aqui. SCP sigue disponible por SSH.", serial_settings: "Ajustes seriales", console_1_preset: "Perfil Consola 1", console_2_preset: "Perfil Consola 2", custom: "Personalizado", save_serial_settings: "Guardar ajustes seriales", serial_settings_note: "Para valores no estandar use Serial Profiles.", change_password: "Cambiar contrasena", current_password: "Contrasena actual", new_password: "Nueva contrasena", files_title: "Archivos", files_note: "Explora las bibliotecas locales del kit.", upload_from_desktop: "Subir desde escritorio", upload_current_library: "Subir a biblioteca actual", exports_title: "Exportaciones Fieldkit", up_one_level: "Subir un nivel", readme_title: "README", docs_title: "Notas de referencia Fieldkit", docs_intro: "Referencias iniciales para plataformas comunes.", back_to_docs: "Volver al indice", serial_profiles_title: "Perfiles seriales", serial_profiles_note: "Los adaptadores seriales se detectan automaticamente. Solo fije un dispositivo si hace falta.", label: "Etiqueta", device_preference: "Preferencia de dispositivo", device_optional_0: "Opcional: /dev/ttyUSB0", device_optional_1: "Opcional: /dev/ttyUSB1", baud_rate: "Baudios", data_bits: "Bits de datos", parity: "Paridad", stop_bits: "Bits de parada", none: "Ninguna", even: "Par", odd: "Impar", console_1: "Consola 1", console_2: "Consola 2", save_serial_profiles: "Guardar perfiles seriales", upload_failed: "Fallo de carga", saved_to: "Guardado {name} en {library}", uploads_not_allowed: "No se permiten cargas en {library}.", no_entries: "Sin entradas", directory_path: "directorio: {path}", download: "Descargar", delete: "Borrar", reset: "Reiniciar", delete_confirm: "Borrar {path} de {library}?", delete_failed: "Fallo al borrar", no_files: "Sin archivos", directory: "Directorio", bytes: "{size} bytes", secure: "segura", preferred: "preferido", auto_detect: "deteccion automatica", unavailable: "no disponible", yes: "si", no: "no", http_label: "HTTP", root_label: "Raiz", http_export_label: "Exportacion HTTP", tftp_label: "TFTP", ftp_label: "FTP", scp_label: "SCP", usb_gadget_label: "Exportacion USB Gadget", configured: "configurado", active: "activo", enabled: "habilitado", built_in_over_ssh: "integrado por SSH", local_shell_title: "Shell local del Pi", local_shell_note: "Este terminal se ejecuta directamente en el appliance Fieldkit como la cuenta local service.", password_change_accepted: "Contrasena cambiada para la cuenta local service." };
TRANSLATIONS.es.export_path = "HTTP: /fieldkit{path}";
TRANSLATIONS.es.export_root_note = "TFTP, FTP y SCP usan la misma estructura de bibliotecas con raiz en {root}.";
TRANSLATIONS.es.reconnect = "Reconectar";
TRANSLATIONS.es.opening_session = "Abriendo sesion...";
TRANSLATIONS.es.connecting = "Conectando...";
TRANSLATIONS.es.reconnecting = "Reconectando";
TRANSLATIONS.es.connected = "Conectado";
TRANSLATIONS.es.disconnected = "Desconectado";
TRANSLATIONS.es.connecting_to_console = "Conectando a la consola {index}...";
TRANSLATIONS.es.console_disconnected = "Consola desconectada";
TRANSLATIONS.es.console_window_title = "Consola {index}";
TRANSLATIONS.es.console_move_note = "Esta ventana puede moverse de forma independiente por el ingeniero de campo.";
TRANSLATIONS.es.console_capture_note = "La entrada del teclado se captura directamente en esta ventana. Haga clic en el terminal si se pierde el foco.";
TRANSLATIONS.de = { ...TRANSLATIONS.en, nav_home: "Start", nav_console: "Konsole", nav_files: "Dateien", nav_docs: "Docs", nav_settings: "Einstellungen", theme_dark: "Dunkel", theme_light: "Hell", serial_consoles: "Serielle Konsolen", open_console_1: "Konsole 1 offnen", open_console_2: "Konsole 2 offnen", popup_note: "Jede Konsole offnet sich in einem eigenen verschiebbaren Fenster.", quick_access: "Schnellzugriff", jump_console: "Zur Konsole", browse_files: "Dateien offnen", raw_exports: "Exporte", open_settings: "Einstellungen offnen", reference_docs: "Referenzdokumente", docs_note: "Herstellerreferenzen lokal auf dem Kit gespeichert.", docs_index: "Dokumentindex offnen", upload_title: "Upload", destination: "Ziel", upload_file: "Datei hochladen", settings_title: "Einstellungen", appliance_controls: "Geraetesteuerung", settings_subhead: "Konnektivitat, Netzwerk, Passwortanderung und serielle Einstellungen.", networking: "Netzwerk", transfer_services: "Transferdienste", serial_presets: "Serielle Vorgaben", password: "Passwort", operational_notes: "Betriebshinweise", export_browser: "Export-Browser", full_serial_profiles: "Volle serielle Profile", open_readme: "README offnen", back_to_console: "Zuruck zur Konsole", connectivity: "Konnektivitat", active_links: "Aktive Verbindungen", nearby_wifi: "Nahe WLANs", hostname: "Hostname", ethernet_mode: "Ethernet-Modus", ethernet_address: "Ethernet-Adresse", wifi_mode: "WLAN-Modus", wifi_ssid: "WLAN-SSID", disabled: "Deaktiviert", ap: "AP", client: "Client", save_network_settings: "Netzwerk speichern", prepare_network_apply: "Netzwerkanwendung vorbereiten", network_apply_note: "Zeigt nur die geplanten Netzwerkbefehle vor echten Anderungen.", transfer_services_title: "Transferdienste", http_export_access: "HTTP-Exportzugang", tftp_access: "TFTP-Zugang", ftp_access: "FTP-Zugang", apply_transfer_services: "Transferdienste anwenden", transfer_services_note: "HTTP exportiert nur /fieldkit uber Port 80. FTP und TFTP bleiben aus, bis sie hier aktiviert werden. SCP bleibt uber SSH verfugbar.", serial_settings: "Serielle Einstellungen", console_1_preset: "Vorgabe Konsole 1", console_2_preset: "Vorgabe Konsole 2", custom: "Benutzerdefiniert", save_serial_settings: "Serielle Einstellungen speichern", serial_settings_note: "Fur Sonderwerte bitte Serial Profiles verwenden.", change_password: "Passwort andern", current_password: "Aktuelles Passwort", new_password: "Neues Passwort", files_title: "Dateien", files_note: "Lokale Dateibibliotheken des Kits durchsuchen.", upload_from_desktop: "Vom Desktop hochladen", upload_current_library: "In aktuelle Bibliothek hochladen", exports_title: "Fieldkit-Exporte", up_one_level: "Eine Ebene hoch", docs_title: "Fieldkit-Referenznotizen", docs_intro: "Startreferenzen fur gangige Plattformen.", back_to_docs: "Zuruck zum Index", serial_profiles_title: "Serielle Profile", serial_profiles_note: "Serielle Adapter werden standardmassig automatisch erkannt.", label: "Bezeichnung", device_preference: "Geraetevorgabe", device_optional_0: "Optional: /dev/ttyUSB0", device_optional_1: "Optional: /dev/ttyUSB1", baud_rate: "Baudrate", data_bits: "Datenbits", parity: "Paritat", stop_bits: "Stoppbits", none: "Keine", even: "Gerade", odd: "Ungerade", console_1: "Konsole 1", console_2: "Konsole 2", save_serial_profiles: "Serielle Profile speichern", upload_failed: "Upload fehlgeschlagen", saved_to: "{name} nach {library} gespeichert", uploads_not_allowed: "Uploads nach {library} sind nicht erlaubt.", no_entries: "Keine Eintrage", directory_path: "Verzeichnis: {path}", download: "Herunterladen", delete: "Loschen", reset: "Zurucksetzen", delete_confirm: "{path} aus {library} loschen?", delete_failed: "Loschen fehlgeschlagen", no_files: "Keine Dateien", bytes: "{size} Byte", secure: "gesichert", preferred: "bevorzugt", auto_detect: "automatisch", unavailable: "nicht verfugbar", yes: "ja", no: "nein", root_label: "Wurzel", http_export_label: "HTTP-Export", usb_gadget_label: "USB-Gadget-Export", configured: "konfiguriert", active: "aktiv", enabled: "aktiviert", built_in_over_ssh: "integriert uber SSH" };
TRANSLATIONS.de.open_local_shell = "Lokale Shell offnen";
TRANSLATIONS.de.local_shell_title = "Lokale Pi-Shell";
TRANSLATIONS.de.local_shell_note = "Dieses Terminal laeuft direkt auf der Fieldkit-Appliance als lokales service-Konto.";
TRANSLATIONS.de.password_change_accepted = "Passwort fuer das lokale service-Konto geaendert.";
TRANSLATIONS.de.export_path = "HTTP: /fieldkit{path}";
TRANSLATIONS.de.export_root_note = "TFTP, FTP und SCP verwenden dieselbe Bibliotheksstruktur mit Wurzel in {root}.";
TRANSLATIONS.de.reconnect = "Neu verbinden";
TRANSLATIONS.de.opening_session = "Sitzung wird geoffnet...";
TRANSLATIONS.de.connecting = "Verbinden...";
TRANSLATIONS.de.reconnecting = "Erneut verbinden";
TRANSLATIONS.de.connected = "Verbunden";
TRANSLATIONS.de.disconnected = "Getrennt";
TRANSLATIONS.de.connecting_to_console = "Verbinde mit Konsole {index}...";
TRANSLATIONS.de.console_disconnected = "Konsole getrennt";
TRANSLATIONS.de.console_window_title = "Konsole {index}";
TRANSLATIONS.de.console_move_note = "Dieses Popup kann vom Feldeinsatztechniker unabhangig verschoben werden.";
TRANSLATIONS.de.console_capture_note = "Tastatureingaben werden direkt in diesem Fenster erfasst. Klicken Sie auf das Terminal, wenn der Fokus verloren geht.";
TRANSLATIONS.de.apply_network_settings = "Netzwerk anwenden";
TRANSLATIONS.de.network_apply_note = "Netzwerk anwenden speichert die aktuellen Werte und fuhrt die echte Netzwerkanderung auf der Appliance aus.";
TRANSLATIONS.de.applying_network_settings = "Netzwerkeinstellungen werden angewendet...";
TRANSLATIONS.de.network_apply_failed = "Netzwerkanwendung fehlgeschlagen: {message}";
TRANSLATIONS.nl = { ...TRANSLATIONS.en, nav_home: "Home", nav_console: "Console", nav_files: "Bestanden", nav_docs: "Docs", nav_settings: "Instellingen", theme_dark: "Donker", theme_light: "Licht", serial_consoles: "Seriele consoles", open_console_1: "Open Console 1", open_console_2: "Open Console 2", popup_note: "Elke console opent in een eigen verplaatsbaar venster.", quick_access: "Snelle toegang", jump_console: "Ga naar console", browse_files: "Bestanden bekijken", raw_exports: "Exports", open_settings: "Open instellingen", reference_docs: "Referentiedocs", docs_note: "Leveranciersreferenties lokaal op de kit opgeslagen.", docs_index: "Open docs-index", upload_title: "Upload", destination: "Doel", upload_file: "Bestand uploaden", settings_title: "Instellingen", appliance_controls: "Apparaatbediening", settings_subhead: "Connectiviteit, netwerk, wachtwoord en seriele instellingen.", networking: "Netwerk", transfer_services: "Overdrachtsdiensten", serial_presets: "Seriele presets", password: "Wachtwoord", operational_notes: "Operationele notities", export_browser: "Exportbrowser", full_serial_profiles: "Volledige seriele profielen", open_readme: "Open README", back_to_console: "Terug naar console", connectivity: "Connectiviteit", active_links: "Actieve links", nearby_wifi: "Nabije wifi", hostname: "Hostnaam", ethernet_mode: "Ethernet-modus", ethernet_address: "Ethernet-adres", wifi_mode: "Wifi-modus", wifi_ssid: "Wifi-SSID", disabled: "Uitgeschakeld", ap: "AP", client: "Client", save_network_settings: "Netwerkinstellingen opslaan", prepare_network_apply: "Netwerkwijziging voorbereiden", network_apply_note: "Toont alleen de geplande netwerkcommando's voor echte wijzigingen.", transfer_services_title: "Overdrachtsdiensten", http_export_access: "HTTP-exporttoegang", tftp_access: "TFTP-toegang", ftp_access: "FTP-toegang", apply_transfer_services: "Overdrachtsdiensten toepassen", transfer_services_note: "HTTP exporteert alleen /fieldkit via poort 80. FTP en TFTP blijven uit totdat je ze hier aanzet. SCP blijft beschikbaar via SSH.", serial_settings: "Seriele instellingen", console_1_preset: "Preset Console 1", console_2_preset: "Preset Console 2", custom: "Aangepast", save_serial_settings: "Seriele instellingen opslaan", serial_settings_note: "Gebruik Serial Profiles voor afwijkende waarden.", change_password: "Wachtwoord wijzigen", current_password: "Huidig wachtwoord", new_password: "Nieuw wachtwoord", files_title: "Bestanden", files_note: "Blader door de lokale bestandsbibliotheken op de kit.", upload_from_desktop: "Upload vanaf desktop", upload_current_library: "Upload naar huidige bibliotheek", exports_title: "Fieldkit-exports", up_one_level: "Een niveau omhoog", docs_title: "Fieldkit-referentienotities", docs_intro: "Startreferenties voor gangbare platforms.", back_to_docs: "Terug naar docs-index", serial_profiles_title: "Seriele profielen", serial_profiles_note: "Seriele adapters worden standaard automatisch gedetecteerd.", label: "Label", device_preference: "Apparaatvoorkeur", device_optional_0: "Optioneel: /dev/ttyUSB0", device_optional_1: "Optioneel: /dev/ttyUSB1", baud_rate: "Baudrate", data_bits: "Databits", parity: "Pariteit", stop_bits: "Stopbits", none: "Geen", even: "Even", odd: "Oneven", console_1: "Console 1", console_2: "Console 2", save_serial_profiles: "Seriele profielen opslaan", upload_failed: "Upload mislukt", saved_to: "{name} opgeslagen naar {library}", uploads_not_allowed: "Uploads naar {library} zijn niet toegestaan.", no_entries: "Geen items", directory_path: "map: {path}", download: "Downloaden", delete: "Verwijderen", reset: "Reset", delete_confirm: "{path} verwijderen uit {library}?", delete_failed: "Verwijderen mislukt", no_files: "Geen bestanden", bytes: "{size} bytes", secure: "beveiligd", preferred: "voorkeur", auto_detect: "auto-detectie", unavailable: "niet beschikbaar", yes: "ja", no: "nee", root_label: "Root", http_export_label: "HTTP-export", usb_gadget_label: "USB-gadget-export", configured: "geconfigureerd", active: "actief", enabled: "ingeschakeld", built_in_over_ssh: "ingebouwd via SSH" };
TRANSLATIONS.nl.open_local_shell = "Open lokale shell";
TRANSLATIONS.nl.local_shell_title = "Lokale Pi-shell";
TRANSLATIONS.nl.local_shell_note = "Deze terminal draait rechtstreeks op de Fieldkit-appliance als het lokale service-account.";
TRANSLATIONS.nl.password_change_accepted = "Wachtwoord gewijzigd voor het lokale service-account.";
TRANSLATIONS.nl.export_path = "HTTP: /fieldkit{path}";
TRANSLATIONS.nl.export_root_note = "TFTP, FTP en SCP gebruiken dezelfde bibliotheekstructuur met root in {root}.";
TRANSLATIONS.nl.reconnect = "Opnieuw verbinden";
TRANSLATIONS.nl.opening_session = "Sessie openen...";
TRANSLATIONS.nl.connecting = "Verbinden...";
TRANSLATIONS.nl.reconnecting = "Opnieuw verbinden";
TRANSLATIONS.nl.connected = "Verbonden";
TRANSLATIONS.nl.disconnected = "Verbroken";
TRANSLATIONS.nl.connecting_to_console = "Verbinding maken met console {index}...";
TRANSLATIONS.nl.console_disconnected = "Console verbroken";
TRANSLATIONS.nl.console_window_title = "Console {index}";
TRANSLATIONS.nl.console_move_note = "Deze popup kan onafhankelijk door de field engineer worden verplaatst.";
TRANSLATIONS.nl.console_capture_note = "Toetsenbordinvoer wordt direct in dit venster vastgelegd. Klik op het terminalgebied als de focus verloren gaat.";
TRANSLATIONS.nl.apply_network_settings = "Netwerk toepassen";
TRANSLATIONS.nl.network_apply_note = "Netwerk toepassen slaat de huidige waarden op en voert de echte netwerkwijziging op het apparaat uit.";
TRANSLATIONS.nl.applying_network_settings = "Netwerkinstellingen worden toegepast...";
TRANSLATIONS.nl.network_apply_failed = "Netwerktoepassing mislukt: {message}";
TRANSLATIONS.fr = { ...TRANSLATIONS.en, nav_home: "Accueil", nav_console: "Console", nav_files: "Fichiers", nav_docs: "Docs", nav_settings: "Parametres", theme_dark: "Sombre", theme_light: "Clair", serial_consoles: "Consoles serie", open_console_1: "Ouvrir Console 1", open_console_2: "Ouvrir Console 2", popup_note: "Chaque console s'ouvre dans sa propre fenetre deplacable.", quick_access: "Acces rapide", jump_console: "Aller a la console", browse_files: "Parcourir les fichiers", raw_exports: "Exports", open_settings: "Ouvrir les parametres", reference_docs: "Docs de reference", docs_note: "Sujets de reference fournisseurs stockes localement sur le kit.", docs_index: "Ouvrir l'index docs", upload_title: "Envoi", destination: "Destination", upload_file: "Envoyer le fichier", settings_title: "Parametres", appliance_controls: "Controles de l'appliance", settings_subhead: "Etat reseau, configuration, mot de passe et parametres serie.", networking: "Reseau", transfer_services: "Services de transfert", serial_presets: "Presets serie", password: "Mot de passe", operational_notes: "Notes operationnelles", export_browser: "Navigateur d'exports", full_serial_profiles: "Profils serie complets", open_readme: "Ouvrir README", back_to_console: "Retour a la console", connectivity: "Connectivite", active_links: "Liens actifs", nearby_wifi: "Wi-Fi proche", hostname: "Nom d'hote", ethernet_mode: "Mode Ethernet", ethernet_address: "Adresse Ethernet", wifi_mode: "Mode Wi-Fi", wifi_ssid: "SSID Wi-Fi", disabled: "Desactive", ap: "AP", client: "Client", save_network_settings: "Enregistrer le reseau", prepare_network_apply: "Preparer l'application reseau", network_apply_note: "Affiche uniquement les commandes prevues avant tout changement reel.", transfer_services_title: "Services de transfert", http_export_access: "Acces export HTTP", tftp_access: "Acces TFTP", ftp_access: "Acces FTP", apply_transfer_services: "Appliquer les services", transfer_services_note: "HTTP expose seulement /fieldkit sur le port 80. FTP et TFTP restent desactives jusqu'a activation ici. SCP reste disponible via SSH.", serial_settings: "Parametres serie", console_1_preset: "Preset Console 1", console_2_preset: "Preset Console 2", custom: "Personnalise", save_serial_settings: "Enregistrer les parametres serie", serial_settings_note: "Pour les valeurs non standard, utilisez Serial Profiles.", change_password: "Changer le mot de passe", current_password: "Mot de passe actuel", new_password: "Nouveau mot de passe", files_title: "Fichiers", files_note: "Parcourez les bibliotheques locales du kit.", upload_from_desktop: "Envoyer depuis le bureau", upload_current_library: "Envoyer vers la bibliotheque courante", exports_title: "Exports Fieldkit", up_one_level: "Niveau superieur", docs_title: "Notes de reference Fieldkit", docs_intro: "References de depart pour les plateformes courantes.", back_to_docs: "Retour a l'index", serial_profiles_title: "Profils serie", serial_profiles_note: "Les adaptateurs serie sont detectes automatiquement par defaut.", label: "Libelle", device_preference: "Preference de peripherique", device_optional_0: "Optionnel : /dev/ttyUSB0", device_optional_1: "Optionnel : /dev/ttyUSB1", baud_rate: "Debit", data_bits: "Bits de donnees", parity: "Parite", stop_bits: "Bits d'arret", none: "Aucune", even: "Pair", odd: "Impair", console_1: "Console 1", console_2: "Console 2", save_serial_profiles: "Enregistrer les profils serie", upload_failed: "Echec de l'envoi", saved_to: "{name} enregistre dans {library}", uploads_not_allowed: "Les envois vers {library} ne sont pas autorises.", no_entries: "Aucune entree", directory_path: "repertoire : {path}", download: "Telecharger", delete: "Supprimer", reset: "Reinitialiser", delete_confirm: "Supprimer {path} de {library} ?", delete_failed: "Echec de suppression", no_files: "Aucun fichier", bytes: "{size} octets", secure: "securise", preferred: "prefere", auto_detect: "auto-detection", unavailable: "indisponible", yes: "oui", no: "non", root_label: "Racine", http_export_label: "Export HTTP", usb_gadget_label: "Export USB Gadget", configured: "configure", active: "actif", enabled: "active", built_in_over_ssh: "integre via SSH" };
TRANSLATIONS.fr.open_local_shell = "Ouvrir le shell local";
TRANSLATIONS.fr.local_shell_title = "Shell local du Pi";
TRANSLATIONS.fr.local_shell_note = "Ce terminal s'execute directement sur l'appliance Fieldkit avec le compte local service.";
TRANSLATIONS.fr.password_change_accepted = "Mot de passe modifie pour le compte local service.";
TRANSLATIONS.fr.export_path = "HTTP: /fieldkit{path}";
TRANSLATIONS.fr.export_root_note = "TFTP, FTP et SCP utilisent la meme structure de bibliotheques racinee dans {root}.";
TRANSLATIONS.fr.reconnect = "Reconnecter";
TRANSLATIONS.fr.opening_session = "Ouverture de session...";
TRANSLATIONS.fr.connecting = "Connexion...";
TRANSLATIONS.fr.reconnecting = "Reconnexion";
TRANSLATIONS.fr.connected = "Connecte";
TRANSLATIONS.fr.disconnected = "Deconnecte";
TRANSLATIONS.fr.connecting_to_console = "Connexion a la console {index}...";
TRANSLATIONS.fr.console_disconnected = "Console deconnectee";
TRANSLATIONS.fr.console_window_title = "Console {index}";
TRANSLATIONS.fr.console_move_note = "Cette fenetre peut etre deplacee independamment par l'ingenieur terrain.";
TRANSLATIONS.fr.console_capture_note = "La saisie clavier est capturee directement dans cette fenetre. Cliquez dans la zone terminal si le focus est perdu.";
TRANSLATIONS.fr.apply_network_settings = "Appliquer le reseau";
TRANSLATIONS.fr.network_apply_note = "Appliquer le reseau enregistre les valeurs actuelles et execute le vrai changement reseau sur l'appliance.";
TRANSLATIONS.fr.applying_network_settings = "Application des parametres reseau...";
TRANSLATIONS.fr.network_apply_failed = "Echec de l'application reseau : {message}";

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

function setLanguage(language) {
  if (!LANGUAGES[language]) {
    return;
  }
  window.localStorage.setItem(STORAGE_KEYS.language, language);
  translateStaticContent();
  window.dispatchEvent(new CustomEvent("fieldkit:language-change", { detail: { language } }));
}

function initializeShellControls() {
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

function renderKeyValue(target, data) {
  if (!target) {
    return;
  }
  target.innerHTML = Object.entries(data)
    .map(([key, value]) => `<p><strong>${key}</strong>: ${typeof value === "object" ? JSON.stringify(value) : value}</p>`)
    .join("");
}

function renderList(target, items, formatter) {
  if (!target) {
    return;
  }
  target.innerHTML = items.map(formatter).join("") || `<li>${t("no_entries")}</li>`;
}

function serialDeviceLabel(session) {
  if (session.active_device) {
    return session.active_device;
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
      (network) => `<li>${network.ssid} <span class="muted">(${network.signal}%${network.secure ? `, ${t("secure")}` : ""})</span></li>`
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
      `<li><strong>${connection.device}</strong> ${connection.name} <span class="muted">${connection.type}, ${connection.state}</span></li>`
  );
}

function renderSerial(serial) {
  if (!serial) {
    return;
  }
  renderList(
    document.getElementById("serial-sessions"),
    serial.sessions,
    (session) => {
      const presetValue = serialPresetValue(session);
      const presetOptions = [
        '<option value="9600-8n1">9600 8N1</option>',
        '<option value="115200-8n1">115200 8N1</option>',
      ];
      if (presetValue === "custom") {
        presetOptions.unshift(
          `<option value="custom" selected>${t("custom")} (${session.baud_rate} ${session.data_bits}${session.parity === "none" ? "N" : session.parity[0].toUpperCase()}${session.stop_bits})</option>`
        );
      }
      return `<li>
        <div class="serial-session-row">
          <div class="serial-session-meta">
            <strong>${session.label}</strong>
            <span>${serialDeviceLabel(session)} <span class="muted">${session.baud_rate} ${session.data_bits}${session.parity === "none" ? "N" : session.parity[0].toUpperCase()}${session.stop_bits}${session.present ? "" : `, ${t("unavailable")}`}</span></span>
          </div>
          <div class="serial-session-actions">
            <div class="serial-session-action-row">
              <select data-serial-preset-index="${session.index}">
                ${presetOptions.map((option) => option.replace(`value="${presetValue}"`, `value="${presetValue}" selected`)).join("")}
              </select>
              <button type="button" class="serial-reset-button" data-reset-console-index="${session.index}">${t("reset")}</button>
            </div>
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
    transferStatus.innerHTML = [
      `<p><strong>${t("http_label")}</strong>: <a href="${transfers.http_base}">${transfers.http_base}</a></p>`,
      `<p><strong>${t("root_label")}</strong>: ${transfers.root}</p>`,
      `<p><strong>${t("http_export_label")}</strong>: ${t("configured")} ${yesNo(transfers.http_export.configured_enabled)}, ${t("active")} ${yesNo(transfers.http_export.active)}</p>`,
      `<p><strong>${t("tftp_label")}</strong>: ${t("configured")} ${yesNo(transfers.tftp.configured_enabled)}, ${t("active")} ${yesNo(transfers.tftp.active)}, ${t("enabled")} ${yesNo(transfers.tftp.enabled)}</p>`,
      `<p><strong>${t("ftp_label")}</strong>: ${t("configured")} ${yesNo(transfers.ftp.configured_enabled)}, ${t("active")} ${yesNo(transfers.ftp.active)}, ${t("enabled")} ${yesNo(transfers.ftp.enabled)}</p>`,
      `<p><strong>${t("scp_label")}</strong>: ${t("built_in_over_ssh")}, ${t("active")} ${yesNo(transfers.scp.active)}, ${t("enabled")} ${yesNo(transfers.scp.enabled)}</p>`,
      `<p><strong>${t("usb_gadget_label")}</strong>: ${transfers.usb_gadget.supported ? t("yes") : t("no")} ${transfers.usb_gadget.model}</p>`,
      `<p>${transfers.usb_gadget.note}</p>`,
      transfers.http_export.note ? `<p>${transfers.http_export.note}</p>` : "",
      transfers.tftp.note ? `<p>${transfers.tftp.note}</p>` : "",
      transfers.ftp.note ? `<p>${transfers.ftp.note}</p>` : "",
      transfers.scp.note ? `<p>${transfers.scp.note}</p>` : "",
    ].join("");
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
  }
  if (connectivityResult.status === "fulfilled") {
    renderConnectivity(connectivityResult.value);
  }
  if (serialResult.status === "fulfilled") {
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
  loadWifiNetworks();
}

function buildSettingsPayload() {
  const networkForm = document.getElementById("settings-form");
  const serialForm = document.getElementById("serial-settings-form");
  const baseSerialPorts = currentSettings?.serial_ports?.length ? currentSettings.serial_ports : defaultSerialPorts();
  const serialPorts = [
    applySerialPreset(baseSerialPorts[0] || defaultSerialPorts()[0], serialForm.console1_preset.value),
    applySerialPreset(baseSerialPorts[1] || defaultSerialPorts()[1], serialForm.console2_preset.value),
  ];
  return {
    hostname: networkForm.hostname.value,
    ethernet: {
      mode: networkForm.ethernet_mode.value,
      address: networkForm.ethernet_address.value,
      gateway: "",
      dns: [],
      interface: "eth0",
    },
    wifi: {
      mode: networkForm.wifi_mode.value,
      ssid: networkForm.wifi_ssid.value,
      password: networkForm.wifi_password.value,
      country_code: "US",
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
if (document.getElementById("serial-sessions") || document.getElementById("settings-form") || document.getElementById("serial-settings-form")) {
  loadStatus();
}
loadMeta();
