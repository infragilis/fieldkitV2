from pathlib import Path

from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse

from app.core.config import get_settings
from app.services.storage import StorageService

router = APIRouter()
storage_service = StorageService(get_settings())


@router.get("")
async def list_files(library: str = Query("data"), path: str = Query("")):
    try:
        return storage_service.list_library(library, path)
    except (FileNotFoundError, NotADirectoryError, ValueError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    target_path = storage_service.save_personal_upload(file.filename or "upload.bin", file.file)
    return {"saved": str(target_path.relative_to(storage_service.settings.content_root))}


@router.get("/download")
async def download_file(library: str = Query("data"), path: str = Query(...)):
    try:
        resolved = storage_service.resolve_download(library, path)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not resolved.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(resolved)


@router.get("/libraries")
async def libraries():
    libraries = []
    for name, path in storage_service.library_paths().items():
        libraries.append({"name": name, "path": str(path), "exists": Path(path).exists()})
    return {"libraries": libraries}
