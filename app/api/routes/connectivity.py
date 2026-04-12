from fastapi import APIRouter

from app.services.network import NetworkService

router = APIRouter()
network_service = NetworkService()


@router.get("/status")
async def connectivity_status():
    return network_service.get_status()


@router.get("/wifi/networks")
async def wifi_networks():
    return {"networks": network_service.scan_wifi_networks()}


@router.post("/apply")
async def apply_connectivity():
    return network_service.apply_settings().model_dump()
