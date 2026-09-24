from __future__ import annotations

import datetime

import traceback
from typing import Optional, Union

import AmazingData

from common.constants import Interval
from core.models.kline import Kline

from utils.stock_mapping import normalize_symbol


class YinheKline:
    """
    银河证券 K 线模块。

    支持：

        - 单股票 K 线
        - 多股票批量 K 线
        - 日 K
        - 周 K
        - 分钟 K

    调用：

        fetch_kline(
            symbol="600519"
        )

        fetch_kline(
            symbol=[
                "600519",
                "000001",
                "300750",
            ]
        )

    返回：

        单股票：
            list[Kline]

        多股票：
            dict[str, list[Kline]]

    数据流程：

        AmazingData DataFrame
                ↓
        Provider 原始数据
                ↓
        统一 Kline
    """

    def __init__(
        self,
        gateway,
    ):
        self.gateway = gateway

    # ==========================================================
    # 主入口
    # ==========================================================

    def fetch_kline(
        self,
        symbol: Union[str, list[str]],
        interval: Interval = Interval.DAY_1,
        start_time: Optional[datetime.datetime] = None,
        end_time: Optional[datetime.datetime] = None,
        limit: int = 1000,
    ) -> Union[list[Kline], dict[str, list[Kline]]]:

        self.gateway._ensure_started()

        # ------------------------------------------------------
        # 1. 判断单个 / 批量
        # ------------------------------------------------------

        is_batch = isinstance(symbol, (list, tuple, set))

        if is_batch:
            symbols = [
                normalized
                for item in symbol
                if item is not None
                for normalized in [normalize_symbol(item)]
                if normalized.endswith((".SH", ".SZ", ".BJ"))
            ]
        else:
            symbols = [normalize_symbol(symbol)]

        # 去重，同时保持原顺序
        symbols = list(dict.fromkeys(symbols))

        if not symbols:
            return {} if is_batch else []

        # ------------------------------------------------------
        # 2. 周期映射
        # ------------------------------------------------------

        period_map = {
            Interval.MINUTE_1: AmazingData.constant.Period.min1.value,
            Interval.MINUTE_5: AmazingData.constant.Period.min5.value,
            Interval.MINUTE_15: AmazingData.constant.Period.min15.value,
            Interval.MINUTE_30: AmazingData.constant.Period.min30.value,
            Interval.MINUTE_60: AmazingData.constant.Period.min60.value,
            Interval.DAY_1: AmazingData.constant.Period.day.value,
            Interval.WEEK_1: AmazingData.constant.Period.week.value,
        }

        period = period_map.get(
            interval,
            AmazingData.constant.Period.day.value,
        )

        # ------------------------------------------------------
        # 3. 日期处理
        # ------------------------------------------------------

        now = datetime.datetime.now()

        today_str = now.strftime("%Y%m%d")

        begin_str = start_time.strftime("%Y%m%d") if start_time else today_str

        end_str = end_time.strftime("%Y%m%d") if end_time else today_str

        # ------------------------------------------------------
        # 4. 一次批量查询
        #
        # 注意：
        #
        # 这里绝对不要：
        #
        # for symbol in symbols:
        #     query_kline(...)
        #
        # 而是一次把 symbols 传进去。
        # ------------------------------------------------------

        try:
            kline_dict = self.gateway.market_data.query_kline(
                symbols,
                period=period,
                begin_date=int(begin_str),
                end_date=int(end_str),
            )

        except Exception as e:
            print(f"[银河网关] 批量 query_kline 查询失败: {e}")
            traceback.print_exc()
            return {} if is_batch else []

        # ------------------------------------------------------
        # 5. 没有返回
        # ------------------------------------------------------

        if kline_dict is None:

            return {} if is_batch else []

        # ------------------------------------------------------
        # 6. 统一处理返回结果
        # ------------------------------------------------------

        result: dict[str, list[Kline]] = {}

        for current_symbol in symbols:

            df = kline_dict.get(current_symbol)

            # --------------------------------------------------
            # 某个股票没有数据
            # --------------------------------------------------

            if df is None:
                result[current_symbol] = []
                continue

            # --------------------------------------------------
            # DataFrame 为空
            # --------------------------------------------------

            if hasattr(df, "empty") and df.empty:
                print(f"[银河网关] {current_symbol} 返回数据为空")
                result[current_symbol] = []

                continue

            # --------------------------------------------------
            # DataFrame → list[dict]
            # --------------------------------------------------

            if hasattr(df, "to_dict"):

                raw_bars = df.to_dict("records")

            else:

                raw_bars = df

            # --------------------------------------------------
            # limit
            # --------------------------------------------------

            if limit and len(raw_bars) > limit:

                raw_bars = raw_bars[-limit:]

            # --------------------------------------------------
            # 转换成统一 Kline
            # --------------------------------------------------

            klines = self._convert_klines(
                symbol=current_symbol,
                interval=interval,
                raw_bars=raw_bars,
            )

            result[current_symbol] = klines

        # ------------------------------------------------------
        # 7. 单股票保持原来的 API
        #
        # fetch_kline("600519")
        #
        # 仍然直接返回 list[Kline]
        # ------------------------------------------------------

        if not is_batch:

            return result.get(
                symbols[0],
                [],
            )

        # ------------------------------------------------------
        # 8. 批量返回
        # ------------------------------------------------------

        return result

    # ==========================================================
    # DataFrame / 原始数据 → Kline
    # ==========================================================

    @staticmethod
    def _convert_klines(
        symbol: str,
        interval: Interval,
        raw_bars,
    ) -> list[Kline]:

        klines: list[Kline] = []

        for item in raw_bars:

            try:

                # --------------------------------------------------
                # 时间
                # --------------------------------------------------

                kline_time = item.get("kline_time")

                if kline_time is None:

                    print(f"[银河网关] {symbol} 缺少 kline_time")

                    print(f"    原始数据: {item}")

                    continue

                # pandas.Timestamp
                if hasattr(
                    kline_time,
                    "to_pydatetime",
                ):

                    kline_time = kline_time.to_pydatetime()

                # --------------------------------------------------
                # Kline
                # --------------------------------------------------

                klines.append(
                    Kline(
                        symbol=symbol,
                        timestamp=kline_time,
                        interval=interval,
                        open=float(item["open"]),
                        high=float(item["high"]),
                        low=float(item["low"]),
                        close=float(item["close"]),
                        volume=int(item["volume"]),
                        amount=float(item["amount"]),
                    )
                )

            except Exception as e:

                print(f"[银河网关] 转换 Kline 失败: " f"{symbol}: {e}")

                print(f"    原始数据: {item}")

                continue

        return klines
