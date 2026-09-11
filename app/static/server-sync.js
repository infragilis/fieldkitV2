(() => {
  const el = (id) => document.getElementById(id);
  const text = (id, value) => { el(id).textContent = value; };
  let urlLoaded = false;
  let timer;
  let busy = false;
  let saving = false;
  let running = false;
  let configured = false;
  let configPlacedAtBottom = null;

  function duration(seconds) {
    if (seconds === null || seconds === undefined) return "—";
    seconds = Math.max(0, Math.round(seconds));
    if (seconds < 60) return `${seconds}s`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ${seconds % 60}s`;
    return `${Math.floor(seconds / 3600)}h ${Math.floor((seconds % 3600) / 60)}m`;
  }

  function bytes(value) {
    if (!value) return "0 B";
    const unit = Math.min(3, Math.floor(Math.log(value) / Math.log(1024)));
    return `${(value / 1024 ** unit).toFixed(unit ? 1 : 0)} ${["B", "KiB", "MiB", "GiB"][unit]}`;
  }

  function date(value) {
    return value ? new Date(value).toLocaleString() : "Never";
  }

  function buttons() {
    el("sync-btn").disabled = busy || saving || running || !configured;
    el("save-btn").disabled = busy || saving || running;
    el("sync-btn").textContent = running ? "Sync in progress…" : "Sync now";
  }

  async function request(path, options = {}) {
    const response = await fetch(path, { ...options, cache: "no-store", signal: AbortSignal.timeout(10000) });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(payload.detail || `Request failed (${response.status}).`);
    return payload;
  }

  function placeConfigSection() {
    const panel = document.querySelector(".panel");
    const section = el("config-section");
    if (!panel || !section) return;
    if (configPlacedAtBottom === configured) return;
    configPlacedAtBottom = configured;
    if (configured) {
      panel.append(section);
    } else {
      panel.insertBefore(section, el("status-section"));
    }
  }

  function render(payload) {
    configured = payload.configured;
    running = payload.running;
    placeConfigSection();
    text("configured", configured ? "configured" : "not configured");
    el("configured").className = `badge ${configured ? "ok" : "missing"}`;
    text("device-id", payload.device_id);
    if (!urlLoaded) {
      el("base-url").value = payload.base_url || "";
      urlLoaded = true;
    }
    const current = payload.current_sync;
    el("current-details").classList.toggle("hidden", !current);
    const phases = { starting: "Starting…", manifest: "Checking the server for updates…", checking: "Checking local files…", downloading: "Downloading updates…", publishing: "Publishing files to transfer exports…", reporting: "Reporting results to the server…" };
    text("current-phase", current ? phases[current.phase] || "Syncing…" : "No sync running.");
    if (current) {
      text("current-file", current.current_file || "—");
      text("current-files", `${current.completed_files} / ${current.total_files ?? "…"}`);
      text("current-bytes", `${bytes(current.downloaded_bytes)}${current.phase === "downloading" ? ` · ${bytes(current.bytes_per_second)}/s` : ""}`);
      text("current-elapsed", duration(current.elapsed_seconds));
      text("current-eta", current.eta_seconds != null ? `About ${duration(current.eta_seconds)}` : current.phase === "downloading" ? "Calculating…" : "Waiting for this stage to finish…");
      const progress = el("sync-progress");
      if (current.phase === "downloading" && current.total_bytes > 0) {
        progress.value = Math.min(100, current.processed_bytes / current.total_bytes * 100);
      } else {
        progress.removeAttribute("value");
      }
    }
    const last = payload.last_sync;
    el("last-empty").classList.toggle("hidden", !!last);
    el("last-details").classList.toggle("hidden", !last);
    if (last) {
      const outcomes = { success: "Successful", partial: "Completed with errors", failed: "Failed", interrupted: "Interrupted" };
      text("last-outcome", outcomes[last.outcome] || last.outcome);
      text("last-started", date(last.started_at));
      text("last-finished", date(last.finished_at));
      text("last-duration", duration(last.elapsed_seconds));
      text("last-trigger", last.trigger === "scheduled" ? "Automatic schedule" : "Sync now");
      const counts = last.counts || {};
      text("last-counts", `${counts.ok || 0} downloaded · ${counts.skipped || 0} unchanged · ${counts.failed || 0} failed`);
      text("last-success", date(payload.last_success_at));
      text("last-error", [last.error, last.report_error ? `Result reporting: ${last.report_error}` : ""].filter(Boolean).join(" "));
      el("result").classList.toggle("hidden", !last.files?.length);
      text("result", (last.files || []).map((file) => `${file.status}\t${file.library}/${file.name}${file.error ? ` — ${file.error}` : ""}`).join("\n"));
    }
    buttons();
  }

  async function refresh() {
    clearTimeout(timer);
    try {
      render(await request("/api/server-sync/status"));
      text("sync-status", configured ? "" : "Save a device token to enable manual and automatic sync.");
    } catch (error) {
      text("sync-status", `Status unavailable: ${error.message} Retrying…`);
    } finally {
      timer = setTimeout(refresh, running ? 1000 : 10000);
    }
  }

  el("save-btn").addEventListener("click", async () => {
    saving = true;
    buttons();
    text("save-status", "Saving…");
    try {
      await request("/api/server-sync/config", {
        method: "PUT", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ base_url: el("base-url").value.trim(), device_token: el("device-token").value.trim() }),
      });
      el("device-token").value = "";
      text("save-status", "Configuration saved.");
      await refresh();
    } catch (error) {
      text("save-status", error.message);
    } finally {
      saving = false;
      buttons();
    }
  });

  el("sync-btn").addEventListener("click", async () => {
    busy = true;
    buttons();
    text("sync-status", "Starting sync…");
    try {
      await request("/api/server-sync/sync", { method: "POST" });
      await refresh();
    } catch (error) {
      text("sync-status", error.message);
    } finally {
      busy = false;
      buttons();
    }
  });

  window.addEventListener("pagehide", () => clearTimeout(timer));
  refresh();
})();
