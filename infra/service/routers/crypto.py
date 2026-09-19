from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Query

from service.app_state import require_data

router = APIRouter(
    prefix="/api/crypto",
    tags=["crypto"],
)


def success(symbol: str, data_value: Any = None) -> dict[str, Any]:
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
    将模型对象转换为可 JSON 序列化的数据。
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
        return {key: serialize(item) for key, item in value.items()}

    return value


@router.get("/quote/{symbol:path}")
def get_crypto_quote(symbol: str):
    """
    获取 Crypto 实时行情。

    例如：

    /api/crypto/quote/BTCUSDT
    /api/crypto/quote/ETHUSDT
    """

    data = require_data()

    try:
        result = data.crypto.get_crypto_quote(symbol)

        if result is None:
            return failure(symbol)

        return success(
            symbol,
            serialize(result),
        )

    except Exception as exc:
        return failure(symbol, str(exc))


@router.get("/quotes")
def get_crypto_quotes(
    symbols: str | None = Query(
        default=None,
        description="多个交易对，使用逗号分隔，例如 BTCUSDT,ETHUSDT",
    ),
):
    """
    获取多个 Crypto 实时行情。

    例如：

    /api/crypto/quotes?symbols=BTCUSDT,ETHUSDT
    """

    data = require_data()

    try:
        if symbols:
            symbol_list = [item.strip() for item in symbols.split(",") if item.strip()]
        else:
            symbol_list = None

        result = data.crypto.get_crypto_quotes(symbols=symbol_list)

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


@router.get("/kline/{symbol:path}")
def get_crypto_kline(
    symbol: str,
    interval: str = Query(
        default="1d",
        description="K线周期，例如 1m/5m/15m/30m/1h/4h/1d/1w",
    ),
    start_time: str | None = Query(
        default=None,
        description="开始时间",
    ),
    end_time: str | None = Query(
        default=None,
        description="结束时间",
    ),
    limit: int = Query(
        default=200,
        ge=1,
        le=1000,
        description="返回数量",
    ),
):
    """
    获取 Crypto K 线。

    symbol 使用 path 参数，支持类似 BTCUSDT。
    """

    data = require_data()

    try:
        result = data.crypto.get_crypto_klines(
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


@router.get("/order-book/{symbol:path}")
def get_crypto_order_book(
    symbol: str,
    limit: int = Query(
        default=20,
        ge=1,
        le=1000,
        description="买卖盘档位数量",
    ),
):
    """
    获取 Crypto 深度 / Order Book。
    """

    data = require_data()

    try:
        result = data.crypto.get_order_book(
            symbol=symbol,
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
