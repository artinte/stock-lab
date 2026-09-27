from __future__ import annotations

from fastapi import APIRouter

from infra.service.app_state import (
    data_manager,
    youtube_service,
)


router = APIRouter(
    prefix="/api",
    tags=["system"],
)


@router.get("/health")
def health():
    """
    API 健康检查。
    """

    return {
        "success": True,
        "status": "ok",
        "services": {
            "data": data_manager is not None,
            "youtube": youtube_service is not None,
        },
    }