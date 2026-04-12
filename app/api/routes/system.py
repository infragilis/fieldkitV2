from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.system import SystemService

router = APIRouter()
system_service = SystemService()


class PasswordChangeRequest(BaseModel):
    current_password: str = Field(min_length=1)
    new_password: str = Field(min_length=4)


@router.get("/status")
async def system_status():
    return system_service.get_status()


@router.post("/password")
async def change_password(payload: PasswordChangeRequest):
    changed = system_service.change_password(payload.current_password, payload.new_password)
    if not changed:
        raise HTTPException(status_code=400, detail="Password change rejected")
    return {"changed": True}


@router.post("/apply-hostname")
async def apply_hostname():
    return system_service.apply_hostname().model_dump()
