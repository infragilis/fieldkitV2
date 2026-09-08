from fastapi import APIRouter, File, HTTPException, UploadFile

from app.core.config import get_settings
from app.core.models import AnsibleGeneration, ClusterConfig, ParseResult
from app.services.cluster_import import ClusterImportService
from app.services.cluster_parser import WorkbookParseError

router = APIRouter()
service = ClusterImportService()
_settings = get_settings()

_ALLOWED_SUFFIXES = {".xlsx", ".xlsm"}


@router.post("/parse", response_model=ParseResult)
async def parse_workbook(file: UploadFile = File(...)):
    filename = file.filename or "workbook"
    if not any(filename.lower().endswith(suffix) for suffix in _ALLOWED_SUFFIXES):
        raise HTTPException(status_code=400, detail="Unsupported file type. Upload a .xlsx or .xlsm workbook.")

    data = await _read_limited(file, _settings.cluster_max_upload_bytes)
    if not data:
        raise HTTPException(status_code=400, detail="The uploaded file is empty.")

    try:
        return service.parse(filename, data)
    except WorkbookParseError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/generate", response_model=AnsibleGeneration)
async def generate_ansible(config: ClusterConfig):
    return service.generate(config)


async def _read_limited(file: UploadFile, limit: int) -> bytes:
    chunks: list[bytes] = []
    size = 0
    while True:
        chunk = await file.read(1024 * 1024)
        if not chunk:
            break
        size += len(chunk)
        if size > limit:
            raise HTTPException(
                status_code=413,
                detail=f"File exceeds the {limit // (1024 * 1024)} MB limit.",
            )
        chunks.append(chunk)
    return b"".join(chunks)
