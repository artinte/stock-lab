from __future__ import annotations

"""
模块名称：银河 K 线数据模块

功能描述：
    通过 AmazingData 获取银河证券 K 线数据，
    并转换为 Stock Lab 统一的 Kline 数据模型。

支持：
    - 单股票 K 线
    - 多股票批量 K 线
    - 1 分钟 K
    - 5 分钟 K
    - 15 分钟 K
    - 30 分钟 K
    - 60 分钟 K
    - 日 K
    - 周 K

数据流程：

    KlineCache
        ↓
    缓存命中
        ↓
    返回 Kline

    缓存未覆盖
        ↓
    AmazingData
        ↓
    DataFrame
        ↓
    Kline
        ↓
    KlineCache
"""

from datetime import datetime

import AmazingData

from common.constants import Interval
from core.models.stock.kline import Kline
from infra.cache.kline_cache import KlineCache
from utils.stock_mapping import normalize_symbol


class YinheKline:
    """
    银河证券 K 线数据适配器。
    """

    def __init__(
        self,
        gateway,
        cache: KlineCache,
    ):
        self.gateway = gateway
        self.cache = cache

    def fetch_kline(
        self,
        symbol: str,
        interval: Interval = Interval.DAY_1,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        limit: int = 1000,
    ) -> list[Kline]:
        """
        获取单个股票 K 线。
        """

        normalized_symbol = normalize_symbol(
            symbol
        )

        if not self._is_stock_symbol(
            normalized_symbol
        ):
            return []

        result = self.fetch_klines(
            symbols=[normalized_symbol],
            interval=interval,
            start_time=start_time,
            end_time=end_time,
            limit=limit,
        )

        return result.get(
            normalized_symbol,
            [],
        )

    def fetch_klines(
        self,
        symbols: list[str],
        interval: Interval = Interval.DAY_1,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        limit: int = 1000,
    ) -> dict[str, list[Kline]]:
        """
        批量获取股票 K 线。

        处理流程：

            1. 标准化股票代码
            2. 查询缓存
            3. 缓存完整则直接返回
            4. 缓存不完整则请求 AmazingData
            5. 保存新的 K 线
            6. 返回指定时间范围数据
        """

        self.gateway._ensure_started()

        normalized_symbols = [
            normalized
            for symbol in symbols
            if symbol is not None
            for normalized in [
                normalize_symbol(symbol)
            ]
            if self._is_stock_symbol(normalized)
        ]

        normalized_symbols = list(
            dict.fromkeys(normalized_symbols)
        )

        if not normalized_symbols:
            return {}

        result: dict[str, list[Kline]] = {}

        missing_symbols: list[str] = []

        for symbol in normalized_symbols:
            if self.cache.contains_range(
                symbol=symbol,
                interval=interval,
                start_time=start_time,
                end_time=end_time,
            ):
                result[symbol] = self.cache.get(
                    symbol=symbol,
                    interval=interval,
                    start_time=start_time,
                    end_time=end_time,
                    limit=limit,
                )
            else:
                missing_symbols.append(symbol)

        if missing_symbols:
            fetched = self._fetch_from_source(
                symbols=missing_symbols,
                interval=interval,
                start_time=start_time,
                end_time=end_time,
            )

            if fetched:
                self.cache.save_many(
                    fetched
                )

                for symbol in missing_symbols:
                    result[symbol] = self.cache.get(
                        symbol=symbol,
                        interval=interval,
                        start_time=start_time,
                        end_time=end_time,
                        limit=limit,
                    )

        return {
            symbol: result.get(
                symbol,
                [],
            )
            for symbol in normalized_symbols
        }

    def clear_cache(
        self,
        symbol: str | None = None,
        interval: Interval | None = None,
    ) -> None:
        """
        清理 K 线缓存。
        """

        self.cache.delete(
            symbol=symbol,
            interval=interval,
        )

    def _fetch_from_source(
        self,
        symbols: list[str],
        interval: Interval,
        start_time: datetime | None,
        end_time: datetime | None,
    ) -> dict[str, list[Kline]]:
        """
        从 AmazingData 获取 K 线。
        """

        period = self._get_period(
            interval
        )

        now = datetime.now()

        begin_date = (
            start_time.strftime("%Y%m%d")
            if start_time is not None
            else now.strftime("%Y%m%d")
        )

        end_date = (
            end_time.strftime("%Y%m%d")
            if end_time is not None
            else now.strftime("%Y%m%d")
        )

        try:
            kline_dict = (
                self.gateway.market_data.query_kline(
                    symbols,
                    period=period,
                    begin_date=int(begin_date),
                    end_date=int(end_date),
                )
            )

        except Exception as exc:
            print(
                f"[银河 K 线] "
                f"query_kline 查询失败：{exc}"
            )
            return {}

        if not kline_dict:
            return {}

        result: dict[str, list[Kline]] = {}

        for symbol in symbols:
            df = kline_dict.get(symbol)

            if df is None:
                result[symbol] = []
                continue

            if hasattr(df, "empty") and df.empty:
                result[symbol] = []
                continue

            if hasattr(df, "to_dict"):
                raw_bars = df.to_dict(
                    "records"
                )
            else:
                raw_bars = df

            if not raw_bars:
                result[symbol] = []
                continue

            result[symbol] = self._convert_klines(
                symbol=symbol,
                interval=interval,
                raw_bars=raw_bars,
            )

        return result

    @staticmethod
    def _is_stock_symbol(
        symbol: str,
    ) -> bool:
        """
        判断是否为 A 股股票代码。
        """

        return symbol.endswith(
            (".SH", ".SZ", ".BJ")
        )

    @staticmethod
    def _get_period(
        interval: Interval,
    ):
        """
        将 Stock Lab K 线周期转换为 AmazingData 周期。
        """

        period_map = {
            Interval.MINUTE_1:
                AmazingData.constant.Period.min1.value,
            Interval.MINUTE_5:
                AmazingData.constant.Period.min5.value,
            Interval.MINUTE_15:
                AmazingData.constant.Period.min15.value,
            Interval.MINUTE_30:
                AmazingData.constant.Period.min30.value,
            Interval.MINUTE_60:
                AmazingData.constant.Period.min60.value,
            Interval.DAY_1:
                AmazingData.constant.Period.day.value,
            Interval.WEEK_1:
                AmazingData.constant.Period.week.value,
        }

        period = period_map.get(interval)

        if period is None:
            raise ValueError(
                f"银河数据源暂不支持 K 线周期：{interval}"
            )

        return period

    @staticmethod
    def _convert_klines(
        symbol: str,
        interval: Interval,
        raw_bars,
    ) -> list[Kline]:
        """
        将 AmazingData 原始 K 线转换为统一 Kline。
        """

        klines: list[Kline] = []

        for item in raw_bars:
            try:
                kline_time = item.get(
                    "kline_time"
                )

                if kline_time is None:
                    print(
                        f"[银河 K 线] "
                        f"{symbol} 缺少 kline_time"
                    )
                    continue

                if hasattr(
                    kline_time,
                    "to_pydatetime",
                ):
                    kline_time = (
                        kline_time.to_pydatetime()
                    )

                if not isinstance(
                    kline_time,
                    datetime,
                ):
                    kline_time = datetime.fromisoformat(
                        str(kline_time)
                    )

                klines.append(
                    Kline(
                        symbol=symbol,
                        interval=interval,
                        timestamp=kline_time,
                        open=float(item["open"]),
                        high=float(item["high"]),
                        low=float(item["low"]),
                        close=float(item["close"]),
                        volume=(
                            float(item["volume"])
                            if item.get("volume") is not None
                            else None
                        ),
                        amount=(
                            float(item["amount"])
                            if item.get("amount") is not None
                            else None
                        ),
                    )
                )

            except Exception as exc:
                print(
                    f"[银河 K 线] "
                    f"转换 Kline 失败："
                    f"{symbol}：{exc}"
                )

        klines.sort(
            key=lambda item: item.timestamp
        )

        return klines