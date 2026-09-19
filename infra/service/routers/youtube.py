from __future__ import annotations

from fastapi import APIRouter, Query
from pydantic import BaseModel

from infra.service.app_state import require_youtube

router = APIRouter(
    prefix="/api/youtube",
    tags=["youtube"],
)


# ============================================================
# Request Models
# ============================================================


class ChannelRequest(BaseModel):

    name: str
    channel_id: str
    category: str = "other"
    enabled: bool = True


class ChannelUpdateRequest(BaseModel):

    name: str | None = None
    category: str | None = None
    enabled: bool | None = None


class ConfigRequest(BaseModel):

    enabled: bool | None = None

    interval: int | None = None

    max_results: int | None = None

    upload_only: bool | None = None

    save_description: bool | None = None

    notification_enabled: bool | None = None

    # YouTube API 网络配置
    proxy: str | None = None

    timeout: int | None = None


# ============================================================
# Status
# ============================================================


@router.get("/status")
def get_status():

    service = require_youtube()

    return {
        "success": True,
        "data": service.get_status(),
    }


# ============================================================
# API Status
# ============================================================


@router.get("/api-status")
def get_api_status():

    service = require_youtube()

    return {
        "success": True,
        "data": service.get_api_status(),
    }


# ============================================================
# Config
# ============================================================


@router.get("/config")
def get_config():

    service = require_youtube()

    return {
        "success": True,
        "data": service.get_config(),
    }


@router.put("/config")
def update_config(
    request: ConfigRequest,
):

    service = require_youtube()

    try:

        result = service.update_config(
            enabled=request.enabled,
            interval=request.interval,
            max_results=request.max_results,
            upload_only=request.upload_only,
            save_description=request.save_description,
            notification_enabled=(request.notification_enabled),
            proxy=request.proxy,
            timeout=request.timeout,
        )

        return {
            "success": True,
            "data": result,
        }

    except ValueError as exc:

        return {
            "success": False,
            "message": str(exc),
        }


# ============================================================
# Channels
# ============================================================


@router.get("/channels")
def get_channels(
    category: str | None = Query(None),
    keyword: str | None = Query(None),
):

    service = require_youtube()

    channels = service.get_channels(
        category=category,
        keyword=keyword,
    )

    return {
        "success": True,
        "data": channels,
        "count": len(channels),
    }


@router.post("/channels")
def add_channel(
    request: ChannelRequest,
):

    service = require_youtube()

    try:

        channel = service.add_channel(
            name=request.name,
            channel_id=request.channel_id,
            category=request.category,
            enabled=request.enabled,
        )

        return {
            "success": True,
            "data": channel,
        }

    except ValueError as exc:

        return {
            "success": False,
            "message": str(exc),
        }


@router.put("/channels/{channel_id}")
def update_channel(
    channel_id: str,
    request: ChannelUpdateRequest,
):

    service = require_youtube()

    try:

        channel = service.update_channel(
            channel_id=channel_id,
            name=request.name,
            category=request.category,
            enabled=request.enabled,
        )

        return {
            "success": True,
            "data": channel,
        }

    except ValueError as exc:

        return {
            "success": False,
            "message": str(exc),
        }


@router.delete("/channels/{channel_id}")
def delete_channel(
    channel_id: str,
):

    service = require_youtube()

    try:

        service.remove_channel(channel_id)

        return {
            "success": True,
            "message": "频道已删除",
        }

    except ValueError as exc:

        return {
            "success": False,
            "message": str(exc),
        }


# ============================================================
# Videos
# ============================================================


@router.get("/videos")
def get_videos(
    category: str | None = Query(None),
    channel_id: str | None = Query(None),
    keyword: str | None = Query(None),
    today: bool = Query(False),
    limit: int = Query(
        50,
        ge=1,
        le=200,
    ),
):

    service = require_youtube()

    videos = service.get_videos(
        category=category,
        channel_id=channel_id,
        keyword=keyword,
        today=today,
        limit=limit,
    )

    return {
        "success": True,
        "data": videos,
        "count": len(videos),
    }


# ============================================================
# Check
# ============================================================


@router.post("/check")
def check():

    service = require_youtube()

    result = service.check_now()

    return {
        "success": True,
        "data": result,
    }


# ============================================================
# AI TOP
# ============================================================


@router.get("/ai/top")
def get_ai_top(
    limit: int = Query(
        10,
        ge=1,
        le=50,
    ),
):

    service = require_youtube()

    result = service.get_ai_top(limit=limit)

    return {
        "success": True,
        "data": result,
        "count": len(result),
    }
