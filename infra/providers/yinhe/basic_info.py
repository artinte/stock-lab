from __future__ import annotations

from datetime import date
from typing import Optional

from core.cache.file import FileCache
from core.cache.paths import get_cache_path

from core.models.stock.basic_info import BasicInfo
from utils.stock_mapping import normalize_symbol, get_exchange


class YinheStock:
    """
    银河股票基础信息适配器。
    """

    def __init__(self, gateway):
        self.gateway = gateway

        # 本地文件缓存
        self._stock_cache = FileCache[BasicInfo](
            path=get_cache_path(
                provider="yinhe",
                name="stock_basic",
            ),
            ttl_days=180,
            serializer=BasicInfo.to_dict,
            deserializer=BasicInfo.from_dict,
        )

    def fetch_stock(
        self,
        symbol: str,
    ) -> Optional[BasicInfo]:
        """
        获取单只股票基础信息。
        """
        stocks = self.fetch_stocks([symbol])
        return stocks[0] if stocks else None

    def fetch_stocks(
        self,
        symbols: list[str],
    ) -> list[BasicInfo]:
        """
        批量获取股票基础信息。

        优先读取本地缓存。
        只有缓存未命中的股票才请求数据源。

        返回：
            按输入股票代码顺序排列的基础信息列表。
            未获取到数据的股票自动跳过。
        """
        self.gateway._ensure_started()

        if not symbols:
            return []

        # 1. 标准化股票代码，并去重，保持原有顺序
        normalized_symbols = list(
            dict.fromkeys(normalize_symbol(symbol) for symbol in symbols)
        )

        # 股票信息映射：股票代码 -> 基础信息
        stock_map: dict[str, BasicInfo] = {}

        missing_symbols: list[str] = []

        # 2. 读取本地缓存
        for symbol in normalized_symbols:
            cached_stock = self._stock_cache.get(symbol)

            if cached_stock is not None:
                stock_map[symbol] = cached_stock
            else:
                missing_symbols.append(symbol)

        # 3. 如果全部命中缓存，按照输入顺序返回
        if not missing_symbols:
            return self._order_stocks(
                normalized_symbols,
                stock_map,
            )

        try:
            # 4. 只请求缓存中没有的股票
            # 获取指定股票列表的上市公司的证券基础数据，包含沪深北三个交易所
            stock_basic = self.gateway.info_data.get_stock_basic(
                missing_symbols,
            )

            if stock_basic is None or stock_basic.empty:
                return self._order_stocks(
                    normalized_symbols,
                    stock_map,
                )

            # 5. 解析数据源返回结果
            for _, row in stock_basic.iterrows():
                symbol = self._clean_value(row.get("MARKET_CODE"))

                if symbol is None:
                    continue

                stock = BasicInfo(
                    symbol=symbol,
                    name=self._clean_value(row.get("SECURITY_NAME")),
                    company_name=self._clean_value(row.get("COMP_NAME")),
                    exchange=get_exchange(symbol),
                    market=self._clean_value(row.get("LISTPLATE_NAME")),
                    listing_date=self._parse_date(row.get("LISTDATE")),
                    delisting_date=self._parse_date(row.get("DELISTDATE")),
                    listed_status=(
                        bool(row.get("IS_LISTED"))
                        if self._clean_value(row.get("IS_LISTED")) is not None
                        else None
                    ),
                    source=self.gateway.display_name,
                )

                # 6. 写入本地缓存
                self._stock_cache.set(
                    key=stock.symbol,
                    value=stock,
                )

                # 7. 暂存股票信息
                stock_map[stock.symbol] = stock

            # 8. 按输入顺序返回
            return self._order_stocks(
                normalized_symbols,
                stock_map,
            )

        except Exception as e:
            print(f"[银河网关] 获取股票信息失败 " f"{missing_symbols}: {e}")

            # 异常时返回已经成功获取的缓存数据
            return self._order_stocks(
                normalized_symbols,
                stock_map,
            )

    @staticmethod
    def _order_stocks(
        symbols: list[str],
        stock_map: dict[str, BasicInfo],
    ) -> list[BasicInfo]:
        """
        按照指定股票代码顺序组装基础信息列表。
        """
        return [stock_map[symbol] for symbol in symbols if symbol in stock_map]

    @staticmethod
    def _parse_date(value) -> date | None:
        """
        将数据源日期转换为 date。
        """
        if value is None:
            return None

        if isinstance(value, date):
            return value

        value = str(value).strip()

        if not value or value == "-":
            return None

        # 兼容 20210827
        if len(value) == 8 and value.isdigit():
            return date(
                int(value[:4]),
                int(value[4:6]),
                int(value[6:8]),
            )

        # 兼容 2021-08-27
        return date.fromisoformat(value)

    @staticmethod
    def _clean_value(value):
        """
        清理数据源中的空值。
        """
        if value is None:
            return None

        # 兼容 pandas NaN
        try:
            if value != value:
                return None
        except Exception:
            pass

        value = str(value).strip()

        if not value or value == "-":
            return None

        return value
