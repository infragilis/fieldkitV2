from fastapi import APIRouter

from app.api.routes import (
    cluster_import,
    connectivity,
    files,
    serial,
    server_sync,
    settings,
    shell,
    system,
    transfers,
    updates,
)

api_router = APIRouter()
api_router.include_router(connectivity.router, prefix="/connectivity", tags=["connectivity"])
api_router.include_router(files.router, prefix="/files", tags=["files"])
api_router.include_router(serial.router, prefix="/serial", tags=["serial"])
api_router.include_router(settings.router, prefix="/settings", tags=["settings"])
api_router.include_router(shell.router, prefix="/shell", tags=["shell"])
api_router.include_router(system.router, prefix="/system", tags=["system"])
api_router.include_router(transfers.router, prefix="/transfers", tags=["transfers"])
api_router.include_router(cluster_import.router, prefix="/cluster", tags=["cluster-import"])
api_router.include_router(server_sync.router, prefix="/server-sync", tags=["server-sync"])
api_router.include_router(updates.router, prefix="/system", tags=["updates"])
