from __future__ import annotations

from fastapi import APIRouter

from service.api import data, youtube_service


router = APIRouter(
    prefix="/api",
    tags=["system"],
)


@router.get("/health")
def health_check():

    manager = data

    return {
        "success": True,
        "api": "running",
        "data_manager": manager is not None,
        "youtube_service": youtube_service is not None,
        "stock_provider": (
            manager.stock_provider
            if manager is not None
            else None
        ),
        "crypto_provider": (
            manager.crypto_provider
            if manager is not None
            else None
        ),
    }