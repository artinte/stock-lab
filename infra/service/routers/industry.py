from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from infra.service import app_state
from utils.stock_industry_classification import get_all_industries

router = APIRouter(
    prefix="/api/industry",
    tags=["Industry"],
)


# ============================================================
# Daily Performance
# ============================================================

@router.get("/categories")
def get_industry_categories(
    level: int = Query(
        default=1,
        ge=1,
        le=4,
        description="行业层级：1 / 2 / 3 / 4",
    ),
):
    industries = get_all_industries(level)

    return [
        {
            "code": industry.symbol,
            "name": industry.name,
            "level": level,
        }
        for industry in industries
    ]


@router.get("/performance")
def get_industry_performance(
    date: str | None = Query(
        default=None,
        description="交易日期，例如 2026-09-22",
    ),
    level: int = Query(
        default=2,
        ge=1,
        le=4,
        description="行业层级：1 / 2 / 3 / 4",
    ),
    method: str = Query(
        default="weighted",
        description="计算方式：weighted / equal",
    ),
):
    """
    获取指定日期的行业行情表现。
    """

    service = app_state.require_industry_performance_service()

    try:
        result = service.get_daily_performance(
            date=date,
            level=level,
            method=method,
        )

        return result.to_dict()

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc


# ============================================================
# Period Performance
# ============================================================


@router.get("/performance/range")
def get_industry_performance_range(
    start_date: str = Query(
        ...,
        description="开始日期，例如 2026-09-01",
    ),
    end_date: str = Query(
        ...,
        description="结束日期，例如 2026-09-22",
    ),
    level: int = Query(
        default=2,
        ge=1,
        le=4,
        description="行业层级：1 / 2 / 3 / 4",
    ),
    method: str = Query(
        default="weighted",
        description="计算方式：weighted / equal",
    ),
):
    """
    获取指定时间区间的行业行情表现。
    """

    service = app_state.require_industry_performance_service()

    try:
        result = service.get_period_performance(
            start_date=start_date,
            end_date=end_date,
            level=level,
            method=method,
        )

        return result.to_dict()

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc
