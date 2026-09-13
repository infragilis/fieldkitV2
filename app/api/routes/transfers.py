import asyncio

from fastapi import APIRouter

from app.services.transfers import TransferService

router = APIRouter()
transfer_service = TransferService()


@router.get("/status")
async def transfer_status():
    return await asyncio.to_thread(transfer_service.get_status)


@router.post("/apply")
async def apply_transfer_services():
    result = await asyncio.to_thread(transfer_service.apply_settings)
    return result.model_dump()
