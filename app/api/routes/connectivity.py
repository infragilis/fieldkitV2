from fastapi import APIRouter
from starlette.concurrency import run_in_threadpool

from app.services.network import NetworkService

router = APIRouter()
network_service = NetworkService()


@router.get("/status")
async def connectivity_status():
    return await run_in_threadpool(network_service.get_status)


@router.get("/wifi/networks")
async def wifi_networks():
    return {"networks": await run_in_threadpool(network_service.scan_wifi_networks)}


@router.post("/apply")
async def apply_connectivity():
    return (await run_in_threadpool(network_service.apply_settings)).model_dump()
