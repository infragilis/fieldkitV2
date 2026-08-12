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
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except (NotADirectoryError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/upload")
async def upload_file(file: UploadFile = File(...), library: str = Query("personal")):
    try:
        target_path = storage_service.save_upload(library, file.filename or "upload.bin", file.file)
    except FileExistsError as exc:
        raise HTTPException(status_code=409, detail=f"File already exists: {exc}") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    root = storage_service.library_paths()[library]
    return {"saved": str(target_path.relative_to(root)), "library": library}


@router.get("/download")
async def download_file(library: str = Query("data"), path: str = Query(...)):
    try:
        resolved = storage_service.resolve_download(library, path)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not resolved.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(resolved, filename=resolved.name)


@router.delete("")
async def delete_file(library: str = Query(...), path: str = Query(...)):
    try:
        storage_service.delete_file(library, path)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"deleted": True, "library": library, "path": path}


@router.get("/libraries")
async def libraries():
    libraries = []
    for name, path in storage_service.library_paths().items():
        libraries.append({"name": name, "path": str(path), "exists": Path(path).exists()})
    return {"libraries": libraries}
