from contextlib import asynccontextmanager
from html import escape

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from app.api.router import api_router
from app.core.config import get_settings
from app.services.docs_catalog import list_topics, topic_path
from app.services.storage import ensure_runtime_layout


@asynccontextmanager
async def lifespan(_: FastAPI):
    ensure_runtime_layout(get_settings())
    yield


app = FastAPI(title="Fieldkit", version="0.1.0", lifespan=lifespan)
app.include_router(api_router, prefix="/api")
app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.get("/", include_in_schema=False)
async def index() -> FileResponse:
    return FileResponse("app/static/index.html")


@app.get("/readme", include_in_schema=False)
async def readme() -> FileResponse:
    return FileResponse("README.md", media_type="text/markdown", filename="README.md")


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
    <style>
      body {{ font-family: 'IBM Plex Sans', sans-serif; background: #f6f0e5; color: #1f2a2d; margin: 0; }}
      main {{ width: min(860px, calc(100vw - 32px)); margin: 0 auto; padding: 32px 0 48px; }}
      a {{ color: #7f311c; }}
      article {{ background: rgba(255, 252, 246, 0.92); border: 1px solid #c2b6a2; border-radius: 18px; padding: 24px; }}
    </style>
  </head>
  <body>
    <main>
      <article>
        <h1>Fieldkit Reference Notes</h1>
        <p>Starter command references for common vendor platforms.</p>
        <ul>{links}</ul>
      </article>
    </main>
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
    <style>
      body {{ font-family: 'IBM Plex Sans', sans-serif; background: #f6f0e5; color: #1f2a2d; margin: 0; }}
      main {{ width: min(960px, calc(100vw - 32px)); margin: 0 auto; padding: 32px 0 48px; }}
      a {{ color: #7f311c; }}
      article {{ background: rgba(255, 252, 246, 0.92); border: 1px solid #c2b6a2; border-radius: 18px; padding: 24px; }}
      pre {{ white-space: pre-wrap; font-family: 'IBM Plex Mono', monospace; line-height: 1.5; }}
    </style>
  </head>
  <body>
    <main>
      <article>
        <p><a href="/kit-docs">Back to docs index</a></p>
        <pre>{body}</pre>
      </article>
    </main>
  </body>
</html>"""
    return HTMLResponse(html)
