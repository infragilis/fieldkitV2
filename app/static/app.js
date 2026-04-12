async function getJson(url, options) {
  const response = await fetch(url, options);
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }
  return response.json();
}

let activeConsoleSocket = null;

async function loadMeta() {
  const response = await fetch("/openapi.json");
  if (!response.ok) {
    return;
  }
  const schema = await response.json();
  document.getElementById("app-version").textContent = `Fieldkit v${schema.info.version}`;
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
  target.innerHTML = items.map(formatter).join("") || "<li>No entries</li>";
}

async function loadStatus() {
  const [system, connectivity, wifi, serial, settings] = await Promise.all([
    getJson("/api/system/status"),
    getJson("/api/connectivity/status"),
    getJson("/api/connectivity/wifi/networks"),
    getJson("/api/serial/sessions"),
    getJson("/api/settings"),
  ]);

  renderKeyValue(document.getElementById("system-status"), system);
  renderKeyValue(document.getElementById("connectivity-status"), connectivity);
  document.getElementById("platform-notes").textContent = (connectivity.platform?.notes || []).join(" ");
  renderList(
    document.getElementById("active-connections"),
    connectivity.active_connections || [],
    (connection) =>
      `<li><strong>${connection.device}</strong> ${connection.name} <span class="muted">${connection.type}, ${connection.state}</span></li>`
  );
  renderList(
    document.getElementById("wifi-networks"),
    wifi.networks,
    (network) => `<li>${network.ssid} <span class="muted">(${network.signal}%${network.secure ? ", secure" : ""})</span></li>`
  );
  renderList(
    document.getElementById("serial-sessions"),
    serial.sessions,
    (session) =>
      `<li><strong>${session.label}</strong> ${session.device_hint} <span class="muted">${session.baud_rate} baud${session.present ? "" : ", unavailable"}</span></li>`
  );

  const networkForm = document.getElementById("settings-form");
  const serialForm = document.getElementById("serial-settings-form");
  networkForm.hostname.value = settings.hostname;
  networkForm.ethernet_mode.value = settings.ethernet.mode;
  networkForm.ethernet_address.value = settings.ethernet.address;
  networkForm.wifi_mode.value = settings.wifi.mode;
  networkForm.wifi_ssid.value = settings.wifi.ssid;
  serialForm.console1_baud.value = settings.serial_ports[0]?.baud_rate || 9600;
  serialForm.console2_baud.value = settings.serial_ports[1]?.baud_rate || 9600;
}

async function loadLibrary(name) {
  const payload = await getJson(`/api/files?library=${encodeURIComponent(name)}`);
  document.getElementById("library-path").textContent = `/${payload.library}/${payload.path || ""}`;
  renderList(
    document.getElementById("library-items"),
    payload.items,
    (item) =>
      `<li>${item.name} <span class="muted">${item.is_dir ? `directory: ${item.path}` : `${item.size} bytes`}</span></li>`
  );
}

function buildSettingsPayload() {
  const networkForm = document.getElementById("settings-form");
  const serialForm = document.getElementById("serial-settings-form");
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
      password: "",
      country_code: "US",
    },
    serial_ports: [
      {
        label: "Console 1",
        device_hint: "/dev/ttyUSB0",
        baud_rate: Number(serialForm.console1_baud.value || 9600),
        data_bits: 8,
        parity: "none",
        stop_bits: 1,
      },
      {
        label: "Console 2",
        device_hint: "/dev/ttyUSB1",
        baud_rate: Number(serialForm.console2_baud.value || 9600),
        data_bits: 8,
        parity: "none",
        stop_bits: 1,
      },
    ],
  };
}

async function saveSettings(event) {
  event.preventDefault();
  const payload = buildSettingsPayload();
  await getJson("/api/settings", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  await loadStatus();
}

async function applyNetworkPlan() {
  const result = await getJson("/api/connectivity/apply", { method: "POST" });
  document.getElementById("apply-network-result").textContent = [...result.commands, ...result.notes].join(" | ");
}

async function uploadFile(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const data = new FormData(form);
  const response = await fetch("/api/files/upload", { method: "POST", body: data });
  const result = await response.json();
  document.getElementById("upload-result").textContent = `Saved ${result.saved}`;
  await loadLibrary("personal");
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
  target.textContent = response.ok ? "Password change accepted by backend placeholder." : "Password change rejected.";
}

function connectConsole(index) {
  if (activeConsoleSocket) {
    activeConsoleSocket.close();
  }
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  const socketUrl = `${protocol}//${window.location.host}/api/serial/ws/${index}`;
  const output = document.getElementById("console-output");
  output.textContent = `Connecting to console ${index + 1}...\n`;
  activeConsoleSocket = new WebSocket(socketUrl);
  activeConsoleSocket.onmessage = (event) => {
    output.textContent += event.data;
    output.scrollTop = output.scrollHeight;
  };
  activeConsoleSocket.onclose = () => {
    output.textContent += "\n[console disconnected]\n";
  };
}

function sendConsoleInput(event) {
  event.preventDefault();
  const input = event.currentTarget.console_input;
  if (!activeConsoleSocket || activeConsoleSocket.readyState !== WebSocket.OPEN) {
    document.getElementById("console-output").textContent += "\n[no active console]\n";
    return;
  }
  activeConsoleSocket.send(`${input.value}\n`);
  input.value = "";
}

document.getElementById("settings-form").addEventListener("submit", saveSettings);
document.getElementById("serial-settings-form").addEventListener("submit", saveSettings);
document.getElementById("upload-form").addEventListener("submit", uploadFile);
document.getElementById("password-form").addEventListener("submit", changePassword);
document.getElementById("console-input-form").addEventListener("submit", sendConsoleInput);
document.getElementById("apply-network-button").addEventListener("click", applyNetworkPlan);
document.getElementById("open-console-0").addEventListener("click", () => connectConsole(0));
document.getElementById("open-console-1").addEventListener("click", () => connectConsole(1));
document.querySelectorAll("[data-library]").forEach((button) => {
  button.addEventListener("click", () => loadLibrary(button.dataset.library));
});

loadStatus();
loadLibrary("data");
loadMeta();
