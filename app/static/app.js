async function getJson(url, options) {
  const response = await fetch(url, options);
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
  target.innerHTML = items.map(formatter).join("") || "<li>No entries</li>";
}

function serialDeviceLabel(session) {
  if (session.active_device) {
    return session.active_device;
  }
  if (session.device_hint) {
    return `${session.device_hint} (preferred)`;
  }
  return "auto-detect";
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
  target.textContent = "Saving serial preset...";
  try {
    const serialPorts = (currentSettings.serial_ports?.length ? currentSettings.serial_ports : defaultSerialPorts()).map((profile) => ({ ...profile }));
    serialPorts[index] = applySerialPreset(serialPorts[index] || defaultSerialPorts()[index], preset);
    await savePayload({
      ...currentSettings,
      serial_ports: serialPorts,
    });
    target.textContent = `${serialPorts[index].label} set to ${serialPorts[index].baud_rate} 8N1.`;
    await loadStatus();
  } catch (error) {
    target.textContent = `Serial preset save failed: ${error.message}`;
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
  target.textContent = `Resetting Console ${index + 1}...`;
  try {
    const result = await getJson(`/api/serial/reset/${index}`, { method: "POST" });
    const popupWindow = consoleWindows.get(index);
    if (popupWindow && !popupWindow.closed) {
      popupWindow.focus();
    }
    target.textContent = result.reset
      ? `Console ${index + 1} session reset.`
      : `Console ${index + 1} had no active session to reset.`;
    await loadStatus();
  } catch (error) {
    target.textContent = `Console reset failed: ${error.message}`;
  }
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
  renderList(
    document.getElementById("wifi-networks"),
    wifi.networks,
    (network) => `<li>${network.ssid} <span class="muted">(${network.signal}%${network.secure ? ", secure" : ""})</span></li>`
  );
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
          `<option value="custom" selected>Custom (${session.baud_rate} ${session.data_bits}${session.parity === "none" ? "N" : session.parity[0].toUpperCase()}${session.stop_bits})</option>`
        );
      }
      return `<li>
        <div class="serial-session-row">
          <div class="serial-session-meta">
            <strong>${session.label}</strong>
            <span>${serialDeviceLabel(session)} <span class="muted">${session.baud_rate} ${session.data_bits}${session.parity === "none" ? "N" : session.parity[0].toUpperCase()}${session.stop_bits}${session.present ? "" : ", unavailable"}</span></span>
          </div>
          <div class="serial-session-actions">
            <div class="serial-session-action-row">
              <select data-serial-preset-index="${session.index}">
                ${presetOptions.map((option) => option.replace(`value="${presetValue}"`, `value="${presetValue}" selected`)).join("")}
              </select>
              <button type="button" class="serial-reset-button" data-reset-console-index="${session.index}">Reset</button>
            </div>
          </div>
        </div>
      </li>`;
    }
  );

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
  }
  if (serialForm) {
    serialForm.console1_preset.value = serialPresetValue(settings.serial_ports[0]);
    serialForm.console2_preset.value = serialPresetValue(settings.serial_ports[1]);
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
    serial_ports: serialPorts,
  };
}

async function saveSettings(event) {
  event.preventDefault();
  const payload = buildSettingsPayload();
  await savePayload(payload);
  await loadStatus();
}

async function applyNetworkPlan() {
  const result = await getJson("/api/connectivity/apply", { method: "POST" });
  const target = document.getElementById("apply-network-result");
  if (target) {
    target.textContent = [...result.commands, ...result.notes].join(" | ");
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
    document.getElementById("upload-result").textContent = result.detail || "Upload failed";
    return;
  }
  const target = document.getElementById("upload-result");
  if (target) {
    target.textContent = `Saved ${result.saved} to ${result.library}`;
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
  target.textContent = response.ok ? "Password change accepted by backend placeholder." : "Password change rejected.";
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
      target.textContent = `Popup blocked for Console ${index + 1}. Allow popups for this site.`;
    }
    return;
  }
  consoleWindows.set(index, popup);
}

document.getElementById("settings-form")?.addEventListener("submit", saveSettings);
document.getElementById("serial-settings-form")?.addEventListener("submit", saveSettings);
document.getElementById("upload-form")?.addEventListener("submit", uploadFile);
document.getElementById("password-form")?.addEventListener("submit", changePassword);
document.getElementById("apply-network-button")?.addEventListener("click", applyNetworkPlan);
document.getElementById("open-console-0")?.addEventListener("click", () => openConsolePopup(0));
document.getElementById("open-console-1")?.addEventListener("click", () => openConsolePopup(1));
loadStatus();
loadMeta();
