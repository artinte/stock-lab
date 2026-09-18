from __future__ import annotations

from typing import Any

from core.models.crypto.quote import CryptoQuote
from core.models.crypto.kline import CryptoKline

from infra.gateways.crypto_data import CryptoDataGateway


class CryptoManager:
    """
    加密货币数据管理器。

    负责：

    - 加密货币实时行情
    - 批量行情
    - K 线
    - 订单簿
    - 最近成交记录
    """

    def __init__(
        self,
        gateway: CryptoDataGateway,
    ) -> None:
        self.gateway = gateway

    # --------------------------------------------------
    # 实时行情
    # --------------------------------------------------

    def get_crypto_quote(
        self,
        symbol: str,
    ) -> CryptoQuote:
        """
        获取加密货币实时行情。

        示例：

            manager.get_quote("BTC/USDT")
            manager.get_quote("ETH/USDT")
        """

        return self.gateway.fetch_crypto_quote(symbol)

    def get_quotes(
        self,
        symbols: list[str],
    ) -> list[CryptoQuote]:
        """批量获取加密货币实时行情。"""

        return self.gateway.fetch_quotes(symbols)

    # --------------------------------------------------
    # K 线
    # --------------------------------------------------

    def get_klines(
        self,
        symbol: str,
        interval: str = "1d",
        limit: int = 100,
    ) -> list[CryptoKline]:
        """
        获取加密货币历史 K 线。

        示例：

            manager.get_klines(
                symbol="BTC/USDT",
                interval="1d",
                limit=100,
            )
        """

        return self.gateway.fetch_klines(
            symbol=symbol,
            interval=interval,
            limit=limit,
        )

    # --------------------------------------------------
    # 订单簿
    # --------------------------------------------------

    def get_order_book(
        self,
        symbol: str,
        limit: int = 20,
    ) -> dict[str, Any]:
        """获取加密货币订单簿。"""

        return self.gateway.fetch_order_book(
            symbol=symbol,
            limit=limit,
        )

    # --------------------------------------------------
    # 最近成交
    # --------------------------------------------------

    def get_trades(
        self,
        symbol: str,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """获取加密货币最近成交记录。"""

        return self.gateway.fetch_trades(
            symbol=symbol,
            limit=limit,
        )
