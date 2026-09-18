from __future__ import annotations

from datetime import datetime
from typing import Any

from core.models.crypto.kline import CryptoKline
from core.models.crypto.quote import CryptoQuote
from infra.gateways.crypto_data import CryptoDataGateway
from infra.providers.binance.client import BinanceClient
from infra.registry import GatewayRegistry

@GatewayRegistry.register("binance")
class BinanceGateway(CryptoDataGateway):
    """Binance 加密货币数据 Gateway。"""

    name = "binance"

    def __init__(
        self,
        config: dict | None = None,
        client: BinanceClient | None = None,
    ) -> None:
        self.config = config or {}
        self.client = client or BinanceClient()

    @staticmethod
    def normalize_symbol(symbol: str) -> str:
        """将项目内部 symbol 转换为 Binance 交易对。"""
        return symbol.replace("/", "").replace("-", "").upper()

    def fetch_crypto_quote(self, symbol: str) -> CryptoQuote:
        """获取单个交易对行情。"""
        symbol = self.normalize_symbol(symbol)

        data = self.client.fetch_ticker(symbol)

        last_price = float(data["lastPrice"])
        prev_close = float(data["prevClosePrice"])

        return CryptoQuote(
            symbol=symbol,
            exchange="Binance",
            last_price=last_price,
            prev_close=prev_close,
            open_price=float(data["openPrice"]),
            high_price=float(data["highPrice"]),
            low_price=float(data["lowPrice"]),
            change=last_price - prev_close,
            change_percent=float(data["priceChangePercent"]),
            volume=float(data["volume"]),
            amount=float(data["quoteVolume"]),
            trade_count=int(data["count"]),
            source="binance",
            timestamp=int(data["closeTime"]),
        )

    def fetch_crypto_quotes(
        self,
        symbols: list[str],
    ) -> list[CryptoQuote]:
        """批量获取行情。"""
        return [self.fetch_quote(symbol) for symbol in symbols]

    def fetch_klines(
        self,
        symbol: str,
        interval: str = "1d",
        limit: int = 100,
    ) -> list[CryptoKline]:
        """获取 K 线。"""
        symbol = self.normalize_symbol(symbol)

        data = self.client.fetch_klines(
            symbol,
            interval=interval,
            limit=limit,
        )

        return [
            CryptoKline(
                symbol=symbol,
                timestamp=datetime.fromtimestamp(item[0] / 1000),
                open=float(item[1]),
                high=float(item[2]),
                low=float(item[3]),
                close=float(item[4]),
                volume=float(item[5]),
                interval=interval,
                amount=float(item[7]),
                close_time=datetime.fromtimestamp(item[6] / 1000),
                trade_count=int(item[8]),
                source="binance",
            )
            for item in data
        ]

    def fetch_order_book(
        self,
        symbol: str,
        limit: int = 20,
    ) -> dict[str, Any]:
        """获取订单簿。"""
        symbol = self.normalize_symbol(symbol)

        data = self.client.fetch_depth(
            symbol=symbol,
            limit=limit,
        )

        return {
            "symbol": symbol,
            "exchange": self.name,
            "last_update_id": data["lastUpdateId"],
            "bids": [
                {
                    "price": float(price),
                    "quantity": float(quantity),
                }
                for price, quantity in data["bids"]
            ],
            "asks": [
                {
                    "price": float(price),
                    "quantity": float(quantity),
                }
                for price, quantity in data["asks"]
            ],
            "source": self.name,
        }

    def fetch_trades(
        self,
        symbol: str,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """获取最近成交记录。"""
        symbol = self.normalize_symbol(symbol)

        data = self.client.fetch_trades(
            symbol,
            limit=limit,
        )

        return [
            {
                "symbol": symbol,
                "exchange": self.name,
                "trade_id": int(item["id"]),
                "price": float(item["price"]),
                "quantity": float(item["qty"]),
                "time": int(item["time"]),
                "is_buyer_maker": bool(item["isBuyerMaker"]),
                "source": self.name,
            }
            for item in data
        ]
