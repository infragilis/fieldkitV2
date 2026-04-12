from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.router import api_router
from app.core.config import get_settings
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
