from abc import ABC, abstractmethod
from typing import Any

from core.models.crypto.kline import CryptoKline
from core.models.crypto.quote import CryptoQuote


class CryptoDataGateway(ABC):
    """加密货币市场数据接口。"""

    @abstractmethod
    def fetch_crypto_quote(
        self,
        symbol: str,
    ) -> CryptoQuote:
        """获取最新行情。"""
        raise NotImplementedError

    @abstractmethod
    def fetch_crypto_quotes(
        self,
        symbols: list[str],
    ) -> list[CryptoQuote]:
        """批量获取行情。"""
        raise NotImplementedError

    @abstractmethod
    def fetch_klines(
        self,
        symbol: str,
        interval: str = "1d",
        limit: int = 100,
    ) -> list[CryptoKline]:
        """获取历史 K 线。"""
        raise NotImplementedError

    @abstractmethod
    def fetch_trades(
        self,
        symbol: str,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """获取最近成交。"""
        raise NotImplementedError

    @abstractmethod
    def fetch_order_book(
        self,
        symbol: str,
        limit: int = 20,
    ) -> dict[str, Any]:
        """获取订单簿。"""
        raise NotImplementedError
