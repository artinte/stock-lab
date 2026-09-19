from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Query

from infra.service.app_state import (
    require_data,
    require_financial_service,
)


router = APIRouter(
    prefix="/api",
    tags=["stock"],
)


def success(
    symbol: str,
    data_value: Any = None,
) -> dict[str, Any]:
    return {
        "success": True,
        "symbol": symbol,
        "data": data_value,
    }


def failure(
    symbol: str,
    message: str = "暂无数据",
) -> dict[str, Any]:
    return {
        "success": False,
        "symbol": symbol,
        "message": message,
        "data": None,
    }


def serialize(value: Any) -> Any:
    """
    将数据模型转换成 JSON 可序列化的数据。
    """

    if value is None:
        return None

    if hasattr(value, "to_dict"):
        return value.to_dict()

    if isinstance(value, list):
        return [serialize(item) for item in value]

    if isinstance(value, tuple):
        return [serialize(item) for item in value]

    if isinstance(value, dict):
        return {
            key: serialize(item)
            for key, item in value.items()
        }

    return value


@router.get("/indices")
def get_indices():
    """获取主要指数行情。"""

    data = require_data()

    try:
        result = data.stock.get_indices()

        return {
            "success": True,
            "data": serialize(result),
        }

    except Exception as exc:
        return {
            "success": False,
            "message": str(exc),
            "data": None,
        }


@router.get("/stock/{symbol}")
def get_stock(symbol: str):
    """获取股票基本信息。"""

    data = require_data()

    try:
        result = data.stock.get_stock(symbol)

        if result is None:
            return failure(symbol)

        return success(
            symbol,
            serialize(result),
        )

    except Exception as exc:
        return failure(symbol, str(exc))


@router.get("/industry_category/{symbol}")
def get_industry_category(symbol: str):
    """获取股票行业分类。"""

    data = require_data()

    try:
        result = data.stock.get_industry_category(symbol)

        if result is None:
            return failure(symbol)

        return success(
            symbol,
            serialize(result),
        )

    except Exception as exc:
        return failure(symbol, str(exc))


@router.get("/quote/{symbol}")
def get_quote(symbol: str):
    """获取股票实时行情。"""

    data = require_data()

    try:
        result = data.stock.get_quote(symbol)

        if result is None:
            return failure(symbol)

        return success(
            symbol,
            serialize(result),
        )

    except Exception as exc:
        return failure(symbol, str(exc))


@router.get("/kline/{symbol}")
def get_kline(
    symbol: str,
    interval: str = Query(
        default="1d",
        description="K线周期：1m/5m/15m/30m/60m/1d/1w/1M",
    ),
    start_time: datetime | None = Query(
        default=None,
        description="开始时间",
    ),
    end_time: datetime | None = Query(
        default=None,
        description="结束时间",
    ),
    limit: int = Query(
        default=200,
        ge=1,
        le=5000,
        description="返回数量",
    ),
):
    """获取股票 K 线数据。"""

    data = require_data()

    try:
        result = data.stock.get_kline(
            symbol=symbol,
            interval=interval,
            start_time=start_time,
            end_time=end_time,
            limit=limit,
        )

        if result is None:
            return failure(symbol)

        return success(
            symbol,
            serialize(result),
        )

    except Exception as exc:
        return failure(symbol, str(exc))


@router.get("/financial/{symbol}")
def get_financial(symbol: str):
    """获取股票财务数据。"""

    service = require_financial_service()

    try:
        result = service.get_financial(symbol)

        if result is None:
            return failure(symbol)

        return success(
            symbol,
            serialize(result),
        )

    except Exception as exc:
        return failure(symbol, str(exc))


@router.get("/valuation/{symbol}")
def get_valuation(symbol: str):
    """获取股票估值数据。"""

    data = require_data()

    try:
        result = data.stock.get_valuation(symbol)

        if result is None:
            return failure(symbol)

        return success(
            symbol,
            serialize(result),
        )

    except Exception as exc:
        return failure(symbol, str(exc))


@router.get("/industry/{symbol}")
def get_industry(symbol: str):
    """获取股票行业信息。"""

    data = require_data()

    try:
        result = data.stock.get_industry(symbol)

        if result is None:
            return failure(symbol)

        return success(
            symbol,
            serialize(result),
        )

    except Exception as exc:
        return failure(symbol, str(exc))


@router.get("/technical/{symbol}")
def get_technical(symbol: str):
    """获取股票技术分析数据。"""

    data = require_data()

    try:
        result = data.stock.get_technical(symbol)

        if result is None:
            return failure(symbol)

        return success(
            symbol,
            serialize(result),
        )

    except Exception as exc:
        return failure(symbol, str(exc))


@router.get("/news/{symbol}")
def get_news(symbol: str):
    """获取股票相关新闻。"""

    data = require_data()

    try:
        result = data.stock.get_news(symbol)

        if result is None:
            return failure(symbol)

        return success(
            symbol,
            serialize(result),
        )

    except Exception as exc:
        return failure(symbol, str(exc))


@router.get("/announcement/{symbol}")
def get_announcement(symbol: str):
    """获取股票公告。"""

    data = require_data()

    try:
        result = data.stock.get_announcement(symbol)

        if result is None:
            return failure(symbol)

        return success(
            symbol,
            serialize(result),
        )

    except Exception as exc:
        return failure(symbol, str(exc))


@router.get("/ai/{symbol}")
def get_ai(symbol: str):
    """获取股票 AI 研究结果。"""

    data = require_data()

    try:
        result = data.stock.get_ai(symbol)

        if result is None:
            return failure(symbol)

        return success(
            symbol,
            serialize(result),
        )

    except Exception as exc:
        return failure(symbol, str(exc))


@router.get("/stock/{symbol}/financial")
def get_stock_financial(symbol: str):
    """
    获取股票完整财务数据。

    保留原有接口，避免影响现有前端。
    """

    service = require_financial_service()

    try:
        result = service.get_financial(symbol)

        if result is None:
            return failure(symbol)

        return success(
            symbol,
            serialize(result),
        )

    except Exception as exc:
        return failure(symbol, str(exc))