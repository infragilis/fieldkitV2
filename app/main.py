import asyncio
import json
import os
from contextlib import asynccontextmanager
from html import escape
from pathlib import Path
from urllib.parse import quote

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, Response
from fastapi.staticfiles import StaticFiles

from app.api.router import api_router
from app.api.routes.server_sync import job as server_sync_job
from app.api.routes.server_sync import service as server_sync_service
from app.core.config import get_settings
from app.services.docs_catalog import list_topics, topic_path
from app.services.report_poller import ReportRequestPoller
from app.services.storage import StorageService, ensure_runtime_layout

_SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
    "Content-Security-Policy": (
        "default-src 'self'; img-src 'self' data:; object-src 'none'; base-uri 'self'; "
        "frame-ancestors 'none'; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "script-src 'self' 'unsafe-inline'"
    ),
}


def _json_for_script(value) -> str:
    """Serialize for embedding in an inline <script> without allowing </script>."""
    return (
        json.dumps(value)
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("&", "\\u0026")
        .replace("\u2028", "\\u2028")
        .replace("\u2029", "\\u2029")
    )


@asynccontextmanager
async def lifespan(_: FastAPI):
    ensure_runtime_layout(get_settings())
    storage_service.sync_export_tree()
    report_poller.start()
    try:
        yield
    finally:
        report_poller.stop()
        await asyncio.to_thread(server_sync_job.stop)


app = FastAPI(title="Fieldkit", version="0.2.1", lifespan=lifespan)
app.include_router(api_router, prefix="/api")
app.mount("/static", StaticFiles(directory="app/static"), name="static")
storage_service = StorageService(get_settings())
report_poller = ReportRequestPoller(
    server_sync_service,
    int(os.environ.get("FIELDKIT_REPORT_POLL_SECONDS", "60") or "60"),
)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    for name, value in _SECURITY_HEADERS.items():
        response.headers.setdefault(name, value)
    return response


def readme_path_for_language(language: str) -> str:
    if language in {"es", "de", "nl", "fr"}:
        localized = f"README.{language}.md"
        if Path(localized).is_file():
            return localized
    return "README.md"


def render_template(name: str) -> str:
    return Path(f"app/static/{name}").read_text(encoding="utf-8")


@app.get("/", include_in_schema=False)
async def index() -> FileResponse:
    return FileResponse("app/static/index.html")


@app.get("/settings", include_in_schema=False)
async def settings_page() -> FileResponse:
    return FileResponse("app/static/settings.html")


@app.get("/tools", include_in_schema=False)
async def tools_page() -> FileResponse:
    return FileResponse("app/static/tools.html")


@app.get("/pi-shell", include_in_schema=False)
async def pi_shell_page() -> FileResponse:
    return FileResponse("app/static/pi-shell.html")


@app.get("/fieldkit", include_in_schema=False)
@app.get("/fieldkit/{requested_path:path}", include_in_schema=False)
async def fieldkit_exports(requested_path: str = ""):
    try:
        resolved = storage_service.resolve_export_path(requested_path)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if resolved.is_file():
        return FileResponse(resolved, media_type="application/octet-stream", filename=resolved.name)
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
    html = render_template("exports.html")
    html = html.replace("__HEADER_PATH_HTML__", escape(header_path))
    html = html.replace("__PARENT_PATH__", parent_path)
    html = html.replace("__LISTING_JSON__", _json_for_script(listing["items"]))
    html = html.replace("__HEADER_PATH_JSON__", _json_for_script(header_path))
    html = html.replace("__ROOT_PATH_JSON__", _json_for_script(str(storage_service.export_root())))
    return HTMLResponse(html)


@app.get("/readme", include_in_schema=False)
async def readme() -> FileResponse:
    return FileResponse("app/static/readme.html")


@app.get("/api/readme-content")
async def readme_content(lang: str = "en"):
    path = readme_path_for_language(lang)
    return {"language": lang, "path": path, "content": Path(path).read_text(encoding="utf-8")}


@app.get("/files", include_in_schema=False)
async def files_page() -> FileResponse:
    return FileResponse("app/static/files.html")


@app.get("/cluster-import", include_in_schema=False)
async def cluster_import_page() -> FileResponse:
    return FileResponse("app/static/cluster-import.html")


@app.get("/server-sync", include_in_schema=False)
async def server_sync_page() -> FileResponse:
    return FileResponse("app/static/server-sync.html")


@app.get("/serial-settings", include_in_schema=False)
async def serial_settings_page() -> FileResponse:
    return FileResponse("app/static/serial-settings.html")


@app.get("/serial-console/{profile_index}", include_in_schema=False)
async def serial_console_window(profile_index: int) -> HTMLResponse:
    if profile_index < 0:
        raise HTTPException(status_code=404, detail="Console not found")
    console_number = profile_index + 1
    html = render_template("serial-console.html")
    html = html.replace("__PROFILE_INDEX__", str(profile_index))
    html = html.replace("__CONSOLE_NUMBER__", str(console_number))
    return HTMLResponse(html)


@app.get("/kit-docs", include_in_schema=False)
async def kit_docs_index() -> HTMLResponse:
    links = "\n".join(
        f'<li><a href="/kit-docs/{topic["slug"]}">{escape(topic["title"])}</a></li>'
        for topic in list_topics()
    )
    html = render_template("kit-docs.html")
    return HTMLResponse(html.replace("__DOC_LINKS__", links))


@app.get("/kit-docs/{slug}", include_in_schema=False)
async def kit_doc(slug: str) -> HTMLResponse:
    path = topic_path(slug)
    if path is None:
        raise HTTPException(status_code=404, detail="Topic not found")
    body = escape(path.read_text())
    title = next(topic["title"] for topic in list_topics() if topic["slug"] == slug)
    html = render_template("kit-doc.html")
    html = html.replace("__DOC_TITLE__", escape(title))
    html = html.replace("__DOC_BODY__", body)
    return HTMLResponse(html)
