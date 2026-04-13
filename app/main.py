import json
from contextlib import asynccontextmanager
from html import escape
from urllib.parse import quote

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from app.api.router import api_router
from app.core.config import get_settings
from app.services.docs_catalog import list_topics, topic_path
from app.services.storage import StorageService, ensure_runtime_layout


@asynccontextmanager
async def lifespan(_: FastAPI):
    ensure_runtime_layout(get_settings())
    yield


app = FastAPI(title="Fieldkit", version="0.1.3", lifespan=lifespan)
app.include_router(api_router, prefix="/api")
app.mount("/static", StaticFiles(directory="app/static"), name="static")
storage_service = StorageService(get_settings())


def readme_path_for_language(language: str) -> str:
    if language in {"es", "de", "nl", "fr"}:
        localized = f"README.{language}.md"
        try:
            with open(localized, encoding="utf-8"):
                return localized
        except FileNotFoundError:
            pass
    return "README.md"


def shell_tools_html() -> str:
    return """
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
    """


def topbar_html(*, docs_href: str = "/#docs", exports_href: str | None = None) -> str:
    exports_link = f'<a href="{exports_href}" data-i18n="raw_exports">Exports</a>' if exports_href else ""
    return f"""
      <nav class="topbar">
        <div class="brand-mark">
          <span>Fieldkit</span>
          <span class="brand-version">v0.1.3</span>
        </div>
        <div class="topbar-right">
          <div class="topbar-links">
            <a href="/" data-i18n="nav_home">Home</a>
            <a href="/files" data-i18n="nav_files">Files</a>
            {exports_link}
            <a href="{docs_href}" data-i18n="nav_docs">Docs</a>
            <a href="/settings" data-i18n="nav_settings">Settings</a>
            <a href="/readme" data-i18n="nav_readme">README</a>
          </div>
          {shell_tools_html()}
        </div>
      </nav>
    """


@app.get("/", include_in_schema=False)
async def index() -> FileResponse:
    return FileResponse("app/static/index.html")


@app.get("/settings", include_in_schema=False)
async def settings_page() -> FileResponse:
    return FileResponse("app/static/settings.html")


@app.get("/pi-shell", include_in_schema=False)
async def pi_shell_page() -> HTMLResponse:
    html = f"""<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Fieldkit Local Shell</title>
    <link rel="stylesheet" href="/static/styles.css" />
    <link rel="stylesheet" href="/static/vendor/xterm.css" />
    <style>
      main {{ width: min(1100px, calc(100vw - 32px)); margin: 0 auto; padding: 0 0 48px; }}
      article {{ padding: 24px; }}
      .shell-note {{ margin-bottom: 12px; }}
      .shell-output {{
        min-height: 520px;
        margin: 0 0 12px;
        overflow: auto;
        border-radius: 12px;
        border: 1px solid var(--line);
        background: #1e2326;
        outline: none;
      }}
      .shell-output .xterm {{ padding: 14px; }}
      .shell-toolbar {{ display: flex; gap: 8px; align-items: center; margin-bottom: 12px; flex-wrap: wrap; }}
    </style>
  </head>
  <body>
    <main class="app-shell">
      {topbar_html()}
      <article class="panel">
        <h1 data-i18n="local_shell_title">Local Pi Shell</h1>
        <p class="muted shell-note" data-i18n="local_shell_note">This terminal runs directly on the Fieldkit appliance as the local service account.</p>
        <div class="shell-toolbar">
          <button id="shell-reconnect-button" type="button" data-i18n="reconnect">Reconnect</button>
          <span id="shell-status" class="muted" data-i18n="opening_session">Opening session...</span>
        </div>
        <div id="shell-output" class="shell-output"></div>
      </article>
    </main>
    <script src="/static/vendor/xterm.js"></script>
    <script src="/static/vendor/xterm-addon-fit.js"></script>
    <script src="/static/app.js"></script>
    <script>
      let shellSocket = null;
      const output = document.getElementById("shell-output");
      const terminal = new Terminal({{
        cursorBlink: true,
        fontFamily: "'IBM Plex Mono', monospace",
        fontSize: 15,
        theme: {{
          background: "#1e2326",
          foreground: "#d6ead9",
          cursor: "#d6ead9",
        }},
      }});
      const fitAddon = new FitAddon.FitAddon();
      terminal.loadAddon(fitAddon);
      terminal.open(output);

      function sendShellMessage(payload) {{
        if (!shellSocket || shellSocket.readyState !== WebSocket.OPEN) {{
          return;
        }}
        shellSocket.send(JSON.stringify(payload));
      }}

      function resizeShell() {{
        fitAddon.fit();
        sendShellMessage({{ type: "resize", cols: terminal.cols, rows: terminal.rows }});
      }}

      function connectShell() {{
        if (shellSocket) {{
          shellSocket.close();
        }}
        const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
        shellSocket = new WebSocket(`${{protocol}}//${{window.location.host}}/api/shell/ws`);
        const status = document.getElementById("shell-status");
        status.textContent = window.fieldkitUi ? window.fieldkitUi.t("connecting") : "Connecting...";
        if (terminal.buffer.active.length) {{
          terminal.writeln(`[${{window.fieldkitUi ? window.fieldkitUi.t("reconnecting").toLowerCase() : "reconnecting"}}]`);
        }}
        shellSocket.onopen = () => {{
          status.textContent = window.fieldkitUi ? window.fieldkitUi.t("connected") : "Connected";
          resizeShell();
          terminal.focus();
        }};
        shellSocket.onmessage = (event) => {{
          terminal.write(event.data);
        }};
        shellSocket.onclose = () => {{
          status.textContent = window.fieldkitUi ? window.fieldkitUi.t("disconnected") : "Disconnected";
          terminal.writeln("");
          terminal.writeln(`[${{window.fieldkitUi ? window.fieldkitUi.t("console_disconnected").toLowerCase() : "disconnected"}}]`);
        }};
      }}

      window.addEventListener("beforeunload", () => {{
        if (shellSocket) {{
          shellSocket.close();
        }}
      }});
      terminal.onData((data) => sendShellMessage({{ type: "input", data }}));
      window.addEventListener("resize", resizeShell);
      document.getElementById("shell-reconnect-button").addEventListener("click", connectShell);
      output.addEventListener("click", () => terminal.focus());
      connectShell();
    </script>
  </body>
</html>"""
    return HTMLResponse(html)


@app.get("/fieldkit", include_in_schema=False)
@app.get("/fieldkit/{requested_path:path}", include_in_schema=False)
async def fieldkit_exports(requested_path: str = ""):
    try:
        resolved = storage_service.resolve_export_path(requested_path)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if resolved.is_file():
        return FileResponse(resolved)
    if not resolved.exists():
        raise HTTPException(status_code=404, detail="File or directory not found")
    if not resolved.is_dir():
        raise HTTPException(status_code=404, detail="Path is not accessible")

    listing = storage_service.list_export_path(requested_path)
    current_path = listing["path"]
    parent_path = "/fieldkit"
    if current_path:
        parent_parts = current_path.split("/")[:-1]
        parent_path = "/fieldkit" if not parent_parts else f"/fieldkit/{quote('/'.join(parent_parts))}"
    header_path = f"/{current_path}" if current_path else "/"
    listing_json = json.dumps(listing["items"])
    html = f"""<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Fieldkit Export {escape(header_path)}</title>
    <link rel="stylesheet" href="/static/styles.css" />
    <style>
      main {{ width: min(980px, calc(100vw - 32px)); margin: 0 auto; padding: 0 0 48px; }}
      article {{ padding: 24px; }}
      ul {{ list-style: none; padding: 0; margin: 18px 0 0; }}
      li {{ display: flex; justify-content: space-between; gap: 16px; align-items: center; border-bottom: 1px solid var(--line); padding: 10px 0; }}
      li:last-child {{ border-bottom: 0; }}
      .item-meta strong, .item-meta span {{ display: block; }}
      .path-note {{ font-family: 'IBM Plex Mono', monospace; }}
    </style>
  </head>
  <body>
    <main class="app-shell">
      {topbar_html(docs_href="/kit-docs", exports_href="/fieldkit")}
      <article class="panel">
        <h1 data-i18n="exports_title">Fieldkit Exports</h1>
        <p id="export-path-note" class="path-note"></p>
        <p id="export-root-note" class="muted"></p>
        <p><a href="{parent_path}" data-i18n="up_one_level">Up one level</a></p>
        <ul id="export-items"></ul>
      </article>
    </main>
    <script src="/static/app.js" defer></script>
    <script>
      const exportListing = {listing_json};
      const exportHeaderPath = {json.dumps(header_path)};
      const exportRootPath = {json.dumps(str(storage_service.export_root()))};

      function escapeHtml(value) {{
        return String(value).replace(/[&<>\"']/g, (char) => ({{
          '&': '&amp;',
          '<': '&lt;',
          '>': '&gt;',
          '"': '&quot;',
          "'": '&#39;'
        }}[char]));
      }}

      function renderExportItems() {{
        const i18n = window.fieldkitUi;
        document.getElementById("export-path-note").textContent = i18n
          ? i18n.t("export_path", {{ path: exportHeaderPath }})
          : `HTTP: /fieldkit${{exportHeaderPath}}`;
        document.getElementById("export-root-note").textContent = i18n
          ? i18n.t("export_root_note", {{ root: exportRootPath }})
          : `TFTP, FTP, and SCP use the same library structure rooted at ${{exportRootPath}}.`;
        document.getElementById("export-items").innerHTML = exportListing.map((item) => `
          <li>
            <div class="item-meta">
              <strong><a href="/fieldkit/${{encodeURIComponent(item.path)}}${{item.is_dir ? "/" : ""}}">${{escapeHtml(item.name)}}</a></strong>
              <span class="muted">${{item.is_dir ? (i18n ? i18n.t("directory") : "Directory") : (i18n ? i18n.t("bytes", {{ size: item.size }}) : `${{item.size}} bytes`)}}</span>
            </div>
            ${{item.is_dir ? "" : `<a href="/fieldkit/${{encodeURIComponent(item.path)}}" download>${{i18n ? i18n.t("download") : "Download"}}</a>`}}
          </li>
        `).join("") || `<li><span class="muted">${{i18n ? i18n.t("no_files") : "No files"}}</span></li>`;
      }}

      window.addEventListener("fieldkit:language-change", renderExportItems);
      window.addEventListener("DOMContentLoaded", renderExportItems);
    </script>
  </body>
</html>"""
    return HTMLResponse(html)


@app.get("/readme", include_in_schema=False)
async def readme() -> HTMLResponse:
    body = escape(open("README.md", encoding="utf-8").read())
    html = f"""<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Fieldkit README</title>
    <link rel="stylesheet" href="/static/styles.css" />
    <style>
      main {{ width: min(960px, calc(100vw - 32px)); margin: 0 auto; padding: 0 0 48px; }}
      article {{ padding: 24px; }}
      pre {{ white-space: pre-wrap; font-family: 'IBM Plex Mono', monospace; line-height: 1.5; }}
    </style>
  </head>
  <body>
    <main class="app-shell">
      {topbar_html()}
      <article class="panel">
        <pre id="readme-body">{body}</pre>
      </article>
    </main>
    <script src="/static/app.js" defer></script>
    <script>
      async function loadReadmeContent(language) {{
        const response = await fetch(`/api/readme-content?lang=${{encodeURIComponent(language)}}`);
        if (!response.ok) {{
          return;
        }}
        const payload = await response.json();
        document.getElementById("readme-body").textContent = payload.content;
      }}

      window.addEventListener("fieldkit:language-change", (event) => loadReadmeContent(event.detail.language));
      window.addEventListener("DOMContentLoaded", () => {{
        const language = window.fieldkitUi ? window.localStorage.getItem("fieldkit-language") || "en" : "en";
        loadReadmeContent(language);
      }});
    </script>
  </body>
</html>"""
    return HTMLResponse(html)


@app.get("/api/readme-content")
async def readme_content(lang: str = "en"):
    path = readme_path_for_language(lang)
    return {"language": lang, "path": path, "content": open(path, encoding="utf-8").read()}


@app.get("/files", include_in_schema=False)
async def files_page() -> HTMLResponse:
    html = """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Fieldkit Files</title>
    <link rel="stylesheet" href="/static/styles.css" />
    <style>
      main { width: min(960px, calc(100vw - 32px)); margin: 0 auto; padding: 0 0 48px; }
      article { padding: 24px; }
      .tabs { display: flex; gap: 8px; margin-bottom: 12px; flex-wrap: wrap; }
      .upload-row { display: flex; gap: 10px; align-items: flex-end; margin-bottom: 12px; flex-wrap: wrap; }
      .upload-row label { display: flex; flex-direction: column; gap: 6px; min-width: 240px; margin-bottom: 0; }
      .upload-row input { max-width: 100%; margin-top: 0; }
      .upload-row button { align-self: flex-end; margin-bottom: 1px; }
      ul { list-style: none; padding: 0; margin: 0; }
      li { padding: 10px 0; border-bottom: 1px solid var(--line); display: flex; justify-content: space-between; gap: 16px; align-items: center; }
      li:last-child { border-bottom: 0; }
      .item-meta { display: flex; flex-direction: column; gap: 4px; }
      .item-actions { display: flex; gap: 8px; align-items: center; }
      .delete-button { background: #8d2f1f; }
      .delete-button:hover { background: #732515; }
    </style>
  </head>
  <body>
    <main class="app-shell">
      __TOPBAR__
      <article class="panel">
        <h1 data-i18n="files_title">Files</h1>
        <p class="muted" data-i18n="files_note">Browse the local file libraries available on the kit.</p>
        <div class="tabs">
          <button data-library="data">data</button>
          <button data-library="personal">personal</button>
          <button data-library="usb">usb</button>
          <button data-library="serial-logs">serial-logs</button>
        </div>
        <form id="library-upload-form" class="upload-row">
          <label>
            <span data-i18n="upload_from_desktop">Upload From Local Desktop</span>
            <input type="file" name="file" required />
          </label>
          <button type="submit" data-i18n="upload_current_library">Upload To Current Library</button>
        </form>
        <p id="upload-result" class="muted"></p>
        <p class="muted" id="library-path"></p>
        <ul id="library-items"></ul>
      </article>
    </main>
    <script src="/static/app.js"></script>
    <script>
      let currentLibrary = "data";

      function escapeHtml(value) {
        return String(value).replace(/[&<>\"']/g, (char) => ({
          '&': '&amp;',
          '<': '&lt;',
          '>': '&gt;',
          '"': '&quot;',
          "'": '&#39;'
        }[char]));
      }

      async function deleteEntry(library, path) {
        const confirmed = window.confirm(window.fieldkitUi ? window.fieldkitUi.t("delete_confirm", { path, library }) : `Delete ${path} from ${library}?`);
        if (!confirmed) return;
        const response = await fetch(`/api/files?library=${encodeURIComponent(library)}&path=${encodeURIComponent(path)}`, {
          method: "DELETE"
        });
        if (!response.ok) {
          const payload = await response.json().catch(() => ({}));
          window.alert(payload.detail || (window.fieldkitUi ? window.fieldkitUi.t("delete_failed") : "Delete failed"));
          return;
        }
        await loadLibrary(library);
      }

      function updateUploadState(library) {
        const form = document.getElementById("library-upload-form");
        const button = form.querySelector("button");
        const allowed = library === "personal" || library === "usb";
        form.style.display = allowed ? "flex" : "none";
        button.textContent = window.fieldkitUi ? window.fieldkitUi.t("upload_current_library") : `Upload To ${library}`;
        document.getElementById("upload-result").textContent = allowed
          ? ""
          : (window.fieldkitUi ? window.fieldkitUi.t("uploads_not_allowed", { library }) : `Uploads are not allowed to ${library}.`);
      }

      async function uploadToCurrentLibrary(event) {
        event.preventDefault();
        const form = event.currentTarget;
        const data = new FormData(form);
        const response = await fetch(`/api/files/upload?library=${encodeURIComponent(currentLibrary)}`, {
          method: "POST",
          body: data
        });
        const payload = await response.json().catch(() => ({}));
        if (!response.ok) {
          document.getElementById("upload-result").textContent = payload.detail || (window.fieldkitUi ? window.fieldkitUi.t("upload_failed") : "Upload failed");
          return;
        }
        document.getElementById("upload-result").textContent = window.fieldkitUi ? window.fieldkitUi.t("saved_to", { name: payload.saved, library: payload.library }) : `Saved ${payload.saved} to ${payload.library}`;
        form.reset();
        await loadLibrary(currentLibrary);
      }

      async function loadLibrary(name) {
        currentLibrary = name;
        updateUploadState(name);
        const response = await fetch(`/api/files?library=${encodeURIComponent(name)}`);
        const payload = await response.json();
        document.getElementById("library-path").textContent = `/${payload.library}/${payload.path || ""}`;
        const i18n = window.fieldkitUi;
        document.getElementById("library-items").innerHTML =
          payload.items.map((item) =>
            `<li>
              <div class="item-meta">
                ${item.is_dir
                  ? `<span>${escapeHtml(item.name)}</span>`
                  : `<a href="/api/files/download?library=${encodeURIComponent(payload.library)}&path=${encodeURIComponent(item.path)}" download>${escapeHtml(item.name)}</a>`
                }
                <span class="muted">${item.is_dir ? (i18n ? i18n.t("directory_path", { path: escapeHtml(item.path) }) : `directory: ${escapeHtml(item.path)}`) : (i18n ? i18n.t("bytes", { size: item.size }) : `${item.size} bytes`)}</span>
              </div>
              <div class="item-actions">
                ${item.is_dir ? "" : `<a href="/api/files/download?library=${encodeURIComponent(payload.library)}&path=${encodeURIComponent(item.path)}" download>${i18n ? i18n.t("download") : "Download"}</a>`}
                ${item.deletable ? `<button class="delete-button" type="button" data-delete-path="${escapeHtml(item.path)}">${i18n ? i18n.t("delete") : "Delete"}</button>` : ""}
              </div>
            </li>`
          ).join("") || `<li>${i18n ? i18n.t("no_entries") : "No entries"}</li>`;
        document.querySelectorAll("[data-delete-path]").forEach((button) => {
          button.addEventListener("click", () => deleteEntry(currentLibrary, button.dataset.deletePath));
        });
      }
      document.querySelectorAll("[data-library]").forEach((button) => {
        button.addEventListener("click", () => loadLibrary(button.dataset.library));
      });
      document.getElementById("library-upload-form").addEventListener("submit", uploadToCurrentLibrary);
      loadLibrary("data");
    </script>
  </body>
</html>"""
    html = html.replace("__TOPBAR__", topbar_html(exports_href="/fieldkit"))
    return HTMLResponse(html)


@app.get("/serial-settings", include_in_schema=False)
async def serial_settings_page() -> HTMLResponse:
    html = """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Fieldkit Serial Profiles</title>
    <link rel="stylesheet" href="/static/styles.css" />
    <style>
      * { box-sizing: border-box; }
      main { width: min(1040px, calc(100vw - 32px)); margin: 0 auto; padding: 0 0 48px; }
      article { padding: 24px; }
      .profiles { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 20px; align-items: start; }
      .profile { min-width: 0; border: 1px solid var(--line); border-radius: 16px; padding: 18px; background: rgba(255, 255, 255, 0.55); }
      input, select, button { font: inherit; }
      @media (max-width: 820px) {
        .profiles { grid-template-columns: 1fr; }
      }
    </style>
  </head>
  <body>
    <main class="app-shell">
      __TOPBAR__
      <article class="panel">
        <h1 data-i18n="serial_profiles_title">Serial Profiles</h1>
        <p class="muted" data-i18n="serial_profiles_note">Serial adapters are auto-detected by default. Only set a device preference when you need to pin a console to a specific adapter.</p>
        <form id="serial-profiles-form">
          <div class="profiles">
            <section class="profile">
              <h2 data-i18n="console_1">Console 1</h2>
              <label>
                <span data-i18n="label">Label</span>
                <input type="text" name="console1_label" />
              </label>
              <label>
                <span data-i18n="device_preference">Device Preference</span>
                <input type="text" name="console1_device_hint" placeholder="Optional: /dev/ttyUSB0" data-i18n-placeholder="device_optional_0" />
              </label>
              <label>
                <span data-i18n="baud_rate">Baud Rate</span>
                <input type="number" name="console1_baud_rate" min="50" step="1" />
              </label>
              <label>
                <span data-i18n="data_bits">Data Bits</span>
                <select name="console1_data_bits">
                  <option value="5">5</option>
                  <option value="6">6</option>
                  <option value="7">7</option>
                  <option value="8">8</option>
                </select>
              </label>
              <label>
                <span data-i18n="parity">Parity</span>
                <select name="console1_parity">
                  <option value="none" data-i18n="none">None</option>
                  <option value="even" data-i18n="even">Even</option>
                  <option value="odd" data-i18n="odd">Odd</option>
                </select>
              </label>
              <label>
                <span data-i18n="stop_bits">Stop Bits</span>
                <select name="console1_stop_bits">
                  <option value="1">1</option>
                  <option value="2">2</option>
                </select>
              </label>
            </section>
            <section class="profile">
              <h2 data-i18n="console_2">Console 2</h2>
              <label>
                <span data-i18n="label">Label</span>
                <input type="text" name="console2_label" />
              </label>
              <label>
                <span data-i18n="device_preference">Device Preference</span>
                <input type="text" name="console2_device_hint" placeholder="Optional: /dev/ttyUSB1" data-i18n-placeholder="device_optional_1" />
              </label>
              <label>
                <span data-i18n="baud_rate">Baud Rate</span>
                <input type="number" name="console2_baud_rate" min="50" step="1" />
              </label>
              <label>
                <span data-i18n="data_bits">Data Bits</span>
                <select name="console2_data_bits">
                  <option value="5">5</option>
                  <option value="6">6</option>
                  <option value="7">7</option>
                  <option value="8">8</option>
                </select>
              </label>
              <label>
                <span data-i18n="parity">Parity</span>
                <select name="console2_parity">
                  <option value="none" data-i18n="none">None</option>
                  <option value="even" data-i18n="even">Even</option>
                  <option value="odd" data-i18n="odd">Odd</option>
                </select>
              </label>
              <label>
                <span data-i18n="stop_bits">Stop Bits</span>
                <select name="console2_stop_bits">
                  <option value="1">1</option>
                  <option value="2">2</option>
                </select>
              </label>
            </section>
          </div>
          <p>
            <button type="submit" data-i18n="save_serial_profiles">Save Serial Profiles</button>
          </p>
          <p id="save-result" class="muted"></p>
        </form>
      </article>
    </main>
    <script src="/static/app.js"></script>
    <script>
      function defaultProfiles() {
        return [
          { label: "Console 1", device_hint: "", baud_rate: 9600, data_bits: 8, parity: "none", stop_bits: 1 },
          { label: "Console 2", device_hint: "", baud_rate: 9600, data_bits: 8, parity: "none", stop_bits: 1 }
        ];
      }

      function fieldValue(form, name) {
        const control = form.elements.namedItem(name);
        return control ? control.value : "";
      }

      function setFieldValue(form, name, value) {
        const control = form.elements.namedItem(name);
        if (control) {
          control.value = value;
        }
      }

      function writeProfile(form, prefix, profile) {
        setFieldValue(form, `${prefix}_label`, profile.label);
        setFieldValue(form, `${prefix}_device_hint`, profile.device_hint || "");
        setFieldValue(form, `${prefix}_baud_rate`, profile.baud_rate);
        setFieldValue(form, `${prefix}_data_bits`, String(profile.data_bits));
        setFieldValue(form, `${prefix}_parity`, profile.parity);
        setFieldValue(form, `${prefix}_stop_bits`, String(profile.stop_bits));
      }

      function readProfile(form, prefix, fallback) {
        return {
          label: fieldValue(form, `${prefix}_label`) || fallback.label,
          device_hint: fieldValue(form, `${prefix}_device_hint`).trim(),
          baud_rate: Number(fieldValue(form, `${prefix}_baud_rate`) || fallback.baud_rate),
          data_bits: Number(fieldValue(form, `${prefix}_data_bits`) || fallback.data_bits),
          parity: fieldValue(form, `${prefix}_parity`) || fallback.parity,
          stop_bits: Number(fieldValue(form, `${prefix}_stop_bits`) || fallback.stop_bits),
        };
      }

      async function loadProfiles() {
        const target = document.getElementById("save-result");
        try {
          const response = await fetch("/api/settings");
          const settings = await response.json();
          const form = document.getElementById("serial-profiles-form");
          const defaults = defaultProfiles();
          const profiles = settings.serial_ports?.length ? settings.serial_ports : defaults;
          writeProfile(form, "console1", profiles[0] || defaults[0]);
          writeProfile(form, "console2", profiles[1] || defaults[1]);
          target.textContent = "";
        } catch (error) {
          target.textContent = window.fieldkitUi ? window.fieldkitUi.t("failed_load_profiles", { message: error.message }) : `Failed to load serial profiles: ${error.message}`;
        }
      }

      async function saveProfiles(event) {
        event.preventDefault();
        const target = document.getElementById("save-result");
        try {
          const settingsResponse = await fetch("/api/settings");
          const settings = await settingsResponse.json();
          const form = event.currentTarget;
          const defaults = defaultProfiles();
          const payload = {
            ...settings,
            serial_ports: [
              readProfile(form, "console1", settings.serial_ports?.[0] || defaults[0]),
              readProfile(form, "console2", settings.serial_ports?.[1] || defaults[1]),
            ],
          };
          const response = await fetch("/api/settings", {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
          });
          target.textContent = response.ok ? (window.fieldkitUi ? window.fieldkitUi.t("serial_profiles_saved") : "Serial profiles saved.") : (window.fieldkitUi ? window.fieldkitUi.t("serial_profile_save_failed") : "Serial profile save failed.");
        } catch (error) {
          target.textContent = window.fieldkitUi ? window.fieldkitUi.t("serial_profile_save_failed", { message: error.message }) : `Serial profile save failed: ${error.message}`;
        }
      }

      document.getElementById("serial-profiles-form").addEventListener("submit", saveProfiles);
      loadProfiles();
    </script>
  </body>
</html>"""
    html = html.replace("__TOPBAR__", topbar_html())
    return HTMLResponse(html)


@app.get("/serial-console/{profile_index}", include_in_schema=False)
async def serial_console_window(profile_index: int) -> HTMLResponse:
    if profile_index < 0:
        raise HTTPException(status_code=404, detail="Console not found")
    console_number = profile_index + 1
    html = f"""<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Fieldkit Console {console_number}</title>
    <style>
      :root {{
        --line: #c2b6a2;
        --text: #1f2a2d;
        --muted: #5e6a6f;
        --accent: #b24a2b;
        --accent-dark: #7f311c;
      }}
      * {{ box-sizing: border-box; }}
      body {{
        margin: 0;
        font-family: 'IBM Plex Sans', sans-serif;
        color: var(--text);
        background:
          radial-gradient(circle at top left, rgba(178, 74, 43, 0.18), transparent 24%),
          linear-gradient(180deg, #f6f0e5, #e9dece);
      }}
      main {{ width: min(100vw, 1100px); margin: 0 auto; padding: 18px; }}
      article {{ background: rgba(255, 252, 246, 0.94); border: 1px solid var(--line); border-radius: 18px; padding: 18px; }}
      .header {{ display: flex; justify-content: space-between; gap: 12px; align-items: baseline; margin-bottom: 12px; }}
      .header h1 {{ margin: 0; font-size: 1.4rem; }}
      .muted {{ color: var(--muted); }}
      .console-output {{
        min-height: 420px;
        margin: 0 0 12px;
        padding: 12px;
        overflow: auto;
        border-radius: 12px;
        border: 1px solid var(--line);
        background: #1e2326;
        color: #d6ead9;
        font-family: 'IBM Plex Mono', monospace;
        white-space: pre-wrap;
        outline: none;
      }}
      .toolbar {{ display: flex; gap: 8px; align-items: center; margin-bottom: 12px; flex-wrap: wrap; }}
      button {{ font: inherit; }}
      button {{
        padding: 10px 14px;
        border: 0;
        border-radius: 999px;
        background: var(--accent);
        color: white;
        cursor: pointer;
      }}
      .capture-note {{
        margin: 0;
        font-size: 0.88rem;
      }}
    </style>
  </head>
  <body>
    <main>
      <article>
        <div class="header">
          <h1 id="console-title">Console {console_number}</h1>
          <span id="console-status" class="muted">Opening session...</span>
        </div>
        <div class="toolbar">
          <button id="reconnect-button" type="button">Reconnect</button>
          <span id="console-move-note" class="muted">This popup can be moved independently by the field engineer.</span>
        </div>
        <p id="console-capture-note" class="muted capture-note">Keyboard input is captured directly in this window. Click the terminal area if input focus is lost.</p>
        <pre id="console-output" class="console-output" tabindex="0"></pre>
      </article>
    </main>
    <script src="/static/app.js"></script>
    <script>
      const profileIndex = {profile_index};
      const consoleNumber = {console_number};
      let consoleSocket = null;
      const output = document.getElementById("console-output");

      function uiText(key, fallback, vars = {{}}) {{
        return window.fieldkitUi ? window.fieldkitUi.t(key, vars) : fallback;
      }}

      function translateConsolePage() {{
        document.getElementById("console-title").textContent = uiText("console_window_title", `Console ${{consoleNumber}}`, {{ index: consoleNumber }});
        document.getElementById("reconnect-button").textContent = uiText("reconnect", "Reconnect");
        document.getElementById("console-move-note").textContent = uiText("console_move_note", "This popup can be moved independently by the field engineer.");
        document.getElementById("console-capture-note").textContent = uiText("console_capture_note", "Keyboard input is captured directly in this window. Click the terminal area if input focus is lost.");
      }}

      function sendRawInput(data) {{
        if (!consoleSocket || consoleSocket.readyState !== WebSocket.OPEN) {{
          output.textContent += "\\n[no active console]\\n";
          output.scrollTop = output.scrollHeight;
          return;
        }}
        consoleSocket.send(data);
      }}

      function keyToSequence(event) {{
        if (event.metaKey || event.altKey) {{
          return null;
        }}
        if (event.ctrlKey && event.key.length === 1) {{
          const upper = event.key.toUpperCase();
          if (upper >= "A" && upper <= "Z") {{
            return String.fromCharCode(upper.charCodeAt(0) - 64);
          }}
        }}
        const special = {{
          Enter: "\\r",
          Backspace: "\\u007f",
          Tab: "\\t",
          Escape: "\\u001b",
          ArrowUp: "\\u001b[A",
          ArrowDown: "\\u001b[B",
          ArrowRight: "\\u001b[C",
          ArrowLeft: "\\u001b[D",
          Delete: "\\u001b[3~",
          Home: "\\u001b[H",
          End: "\\u001b[F",
          PageUp: "\\u001b[5~",
          PageDown: "\\u001b[6~",
        }};
        if (special[event.key]) {{
          return special[event.key];
        }}
        if (!event.ctrlKey && event.key.length === 1) {{
          return event.key;
        }}
        return null;
      }}

      function connectConsole() {{
        if (consoleSocket) {{
          consoleSocket.close();
        }}
        const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
        const socketUrl = `${{protocol}}//${{window.location.host}}/api/serial/ws/${{profileIndex}}`;
        const status = document.getElementById("console-status");
        status.textContent = uiText("connecting", "Connecting...");
        output.textContent += output.textContent ? `\\n[${{uiText("reconnecting", "reconnecting").toLowerCase()}}]\\n` : `${{uiText("connecting_to_console", `Connecting to console ${{consoleNumber}}...`, {{ index: consoleNumber }})}}\\n`;
        consoleSocket = new WebSocket(socketUrl);
        consoleSocket.onopen = () => {{
          status.textContent = uiText("connected", "Connected");
          output.focus();
        }};
        consoleSocket.onmessage = (event) => {{
          output.textContent += event.data;
          output.scrollTop = output.scrollHeight;
        }};
        consoleSocket.onclose = () => {{
          status.textContent = uiText("disconnected", "Disconnected");
          output.textContent += `\\n[${{uiText("console_disconnected", "console disconnected").toLowerCase()}}]\\n`;
          output.scrollTop = output.scrollHeight;
        }};
      }}

      function handleConsoleKeydown(event) {{
        const sequence = keyToSequence(event);
        if (sequence === null) {{
          return;
        }}
        event.preventDefault();
        sendRawInput(sequence);
      }}

      window.addEventListener("beforeunload", () => {{
        if (consoleSocket) {{
          consoleSocket.close();
        }}
      }});
      window.addEventListener("fieldkit:language-change", translateConsolePage);

      window.addEventListener("keydown", handleConsoleKeydown);
      document.getElementById("reconnect-button").addEventListener("click", connectConsole);
      output.addEventListener("click", () => output.focus());
      translateConsolePage();
      connectConsole();
    </script>
  </body>
</html>"""
    return HTMLResponse(html)


@app.get("/kit-docs", include_in_schema=False)
async def kit_docs_index() -> HTMLResponse:
    links = "\n".join(
        f'<li><a href="/kit-docs/{topic["slug"]}">{escape(topic["title"])}</a></li>'
        for topic in list_topics()
    )
    html = f"""<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Fieldkit Docs</title>
    <link rel="stylesheet" href="/static/styles.css" />
    <style>
      main {{ width: min(860px, calc(100vw - 32px)); margin: 0 auto; padding: 0 0 48px; }}
      article {{ padding: 24px; }}
    </style>
  </head>
  <body>
    <main class="app-shell">
      {topbar_html(docs_href="/kit-docs")}
      <article class="panel">
        <h1 data-i18n="docs_title">Fieldkit Reference Notes</h1>
        <p data-i18n="docs_intro">Starter command references for common vendor platforms.</p>
        <ul>{links}</ul>
      </article>
    </main>
    <script src="/static/app.js" defer></script>
  </body>
</html>"""
    return HTMLResponse(html)


@app.get("/kit-docs/{slug}", include_in_schema=False)
async def kit_doc(slug: str) -> HTMLResponse:
    path = topic_path(slug)
    if path is None:
        raise HTTPException(status_code=404, detail="Topic not found")
    body = escape(path.read_text())
    title = next(topic["title"] for topic in list_topics() if topic["slug"] == slug)
    html = f"""<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{escape(title)} - Fieldkit Docs</title>
    <link rel="stylesheet" href="/static/styles.css" />
    <style>
      main {{ width: min(960px, calc(100vw - 32px)); margin: 0 auto; padding: 0 0 48px; }}
      article {{ padding: 24px; }}
      pre {{ white-space: pre-wrap; font-family: 'IBM Plex Mono', monospace; line-height: 1.5; }}
    </style>
  </head>
  <body>
    <main class="app-shell">
      {topbar_html(docs_href="/kit-docs")}
      <article class="panel">
        <p><a href="/kit-docs" data-i18n="back_to_docs">Back to docs index</a></p>
        <pre>{body}</pre>
      </article>
    </main>
    <script src="/static/app.js" defer></script>
  </body>
</html>"""
    return HTMLResponse(html)
