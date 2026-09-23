from __future__ import annotations

import datetime
from typing import Optional

import pandas

from common.constants import Interval, TEN_THOUSAND
from common.enums.quote_level import QuoteLevel
from core.models.quote import Quote

from utils.stock_mapping import normalize_symbol


class YinheQuote:
    """
    银河证券行情模块。

    负责获取并统一转换股票最新行情：

        - 最新价格
        - 昨收
        - 开盘 / 最高 / 最低
        - 涨跌 / 涨跌幅 / 振幅
        - 成交量 / 成交额
        - 成交均价
        - 换手率
        - 量比
        - 总市值 / 流通市值
        - 涨停 / 跌停
        - 交易状态

    最终统一转换为 Quote。
    """

    def __init__(
        self,
        gateway,
    ):
        self.gateway = gateway

    # =========================================================
    # 单只行情
    # =========================================================

    def fetch_quote(
        self,
        symbol: str,
        quote_level: Optional[QuoteLevel] = None,
    ) -> Quote | None:
        """
        获取单只股票最新行情。

        fetch_quote 是 fetch_quotes 的单只特例。
        """

        quotes = self.fetch_quotes(
            symbols=[symbol],
            quote_level=quote_level,
        )

        if not quotes:
            return None

        return quotes[0]

    # =========================================================
    # 批量行情
    # =========================================================

    def fetch_quotes(
        self,
        symbols: list[str],
        quote_level: Optional[QuoteLevel] = None,
    ) -> list[Quote]:
        """
        批量获取股票最新行情。

        参数：
            symbols:
                股票代码列表，例如：

                    [
                        "600519",
                        "000001",
                        "300750",
                        "688981",
                    ]

        返回：
            list[Quote]

        核心原则：

            1. 统一标准化股票代码
            2. 一次批量获取 K 线
            3. 一次批量获取股本
            4. 分别构造 Quote

        不在这里逐只调用 fetch_kline。
        """

        self.gateway._ensure_started()

        if not symbols:
            return []

        # =====================================================
        # 1. 标准化股票代码
        # =====================================================

        normalized_symbols = []

        for symbol in symbols:
            if not symbol:
                continue

            symbol = normalize_symbol(symbol)

            if symbol not in normalized_symbols:
                normalized_symbols.append(symbol)

        if not normalized_symbols:
            return []

        # =====================================================
        # 2. 获取当前时间
        # =====================================================

        now = datetime.datetime.now()

        start_time = now - pandas.Timedelta(days=30)

        # =====================================================
        # 3. 一次性批量获取 K 线
        # =====================================================

        try:
            klines = self.gateway.kline.fetch_kline(
                symbol=normalized_symbols,
                interval=Interval.DAY_1,
                start_time=start_time,
                end_time=now,
                limit=30,
            )

        except Exception as e:
            print(f"[银河行情] 批量获取 K 线失败：{e}")
            return []

        if not klines:
            return []

        # =====================================================
        # 4. 整理 K 线数据
        # =====================================================

        kline_map = self._group_klines(
            klines,
            normalized_symbols,
        )

        if not kline_map:
            return []

        # =====================================================
        # 5. 一次批量获取股本
        # =====================================================

        equity_structures = self.gateway.equity_structure.fetch_equity_structures(
            normalized_symbols
        )

        # list[EquityStructure]
        # 转换成：
        #
        # {
        #     "600519.SH": EquityStructure(...),
        #     "000001.SZ": EquityStructure(...),
        # }

        equity_map = {structure.symbol: structure for structure in equity_structures}

        # =====================================================
        # 6. 构造 Quote
        # =====================================================

        result = []

        for symbol in normalized_symbols:
            symbol_klines = kline_map.get(symbol)

            if not symbol_klines:
                print(f"[银河行情] 无 K 线数据：{symbol}")
                continue

            equity = equity_map.get(symbol)

            try:
                quote = self._build_quote(
                    symbol=symbol,
                    klines=symbol_klines,
                    equity=equity,
                    quote_level=quote_level,
                )

                if quote is not None:
                    result.append(quote)

            except Exception as e:
                print(f"[银河行情] 构造行情失败 " f"{symbol}：{e}")

        return result

    # =========================================================
    # K 线整理
    # =========================================================

    @staticmethod
    def _group_klines(
        klines,
        symbols: list[str],
    ) -> dict[str, list]:
        """
        将批量 K 线数据整理成：

            {
                symbol: [Kline, Kline, ...]
            }

        兼容两种常见返回形式：

            1. dict[str, list[Kline]]
            2. list[Kline]
        """

        if isinstance(klines, dict):

            result = {}

            for symbol, items in klines.items():

                normalized = normalize_symbol(symbol)

                if items:
                    result[normalized] = items

            return result

        # -----------------------------------------------------
        # list[Kline]
        # -----------------------------------------------------

        if isinstance(klines, list):

            result = {symbol: [] for symbol in symbols}

            for kline in klines:

                symbol = getattr(
                    kline,
                    "symbol",
                    None,
                )

                if not symbol:
                    continue

                symbol = normalize_symbol(symbol)

                if symbol in result:
                    result[symbol].append(kline)

            return result

        return {}

    # =========================================================
    # 批量获取股本
    # =========================================================

    def _fetch_equity(
        self,
        symbols: list[str],
    ) -> dict[str, pandas.DataFrame]:
        """
        批量获取股本数据。

        返回：

            {
                "600519.SH": DataFrame,
                "000001.SZ": DataFrame,
            }
        """

        result = {}

        try:
            equity = self.gateway.info_data.get_equity_structure(
                symbols,
                local_path=self.gateway.local_path,
                is_local=True,
            )

            if equity is None or equity.empty:
                return result

            # -------------------------------------------------
            # 如果数据中存在股票代码字段
            # -------------------------------------------------

            symbol_column = None
            for column in (
                "SYMBOL",
                "CODE",
                "SECU_CODE",
                "STOCK_CODE",
                "symbol",
                "code",
            ):

                if column in equity.columns:
                    symbol_column = column
                    break

            # -------------------------------------------------
            # 有股票代码字段
            # -------------------------------------------------

            if symbol_column is not None:
                for symbol in symbols:
                    mask = (
                        equity[symbol_column].astype(str).map(normalize_symbol)
                        == symbol
                    )
                    data = equity.loc[mask]

                    if not data.empty:
                        result[symbol] = data

            # -------------------------------------------------
            # 如果接口只返回当前批次数据，
            # 且没有代码字段，则无法安全拆分。
            #
            # 这里不做错误映射。
            # -------------------------------------------------

            return result

        except Exception as e:

            print(f"[银河行情] 批量获取股本失败：{e}")

            return result

    # =========================================================
    # 构造 Quote
    # =========================================================

    def _build_quote(
        self,
        symbol: str,
        klines,
        equity,
        quote_level: Optional[QuoteLevel] = None,
    ) -> Quote | None:
        """
        根据单只股票的 K 线和股本数据构造 Quote。

        所有计算逻辑集中在这里。
        """

        if not klines:
            return None

        # =====================================================
        # 最新 K 线
        # =====================================================

        latest = klines[-1]

        previous = klines[-2] if len(klines) > 1 else None

        # =====================================================
        # 基础价格
        # =====================================================

        last_price = latest.close

        prev_close = previous.close if previous is not None else None

        open_price = latest.open
        high_price = latest.high
        low_price = latest.low

        # =====================================================
        # 涨跌
        # =====================================================

        change = None
        change_percent = None

        if last_price is not None and prev_close is not None and prev_close != 0:

            change = last_price - prev_close

            change_percent = change / prev_close * 100

        # =====================================================
        # 振幅
        # =====================================================

        amplitude = None

        if (
            high_price is not None
            and low_price is not None
            and prev_close is not None
            and prev_close != 0
        ):

            amplitude = (high_price - low_price) / prev_close * 100

        # =====================================================
        # 股本
        # =====================================================

        total_shares = equity.total_shares
        float_shares = equity.float_shares

        # =====================================================
        # 总市值
        # =====================================================

        market_cap = None

        if total_shares is not None and last_price is not None:
            market_cap = total_shares * last_price

        # =====================================================
        # 流通市值
        # =====================================================

        float_market_cap = None

        if float_shares is not None and last_price is not None:
            float_market_cap = float_shares * last_price

        # =====================================================
        # 成交量 / 成交额
        # =====================================================

        volume = latest.volume
        amount = latest.amount

        # =====================================================
        # 成交均价
        # =====================================================

        average_price = None

        if amount is not None and volume is not None and volume != 0:

            average_price = amount / volume

        # =====================================================
        # 换手率
        # =====================================================

        turnover = None

        if float_shares is not None and float_shares != 0 and volume is not None:

            turnover = volume / float_shares * 100

        # =====================================================
        # 量比
        # =====================================================

        volume_ratio = None

        if len(klines) > 1:

            volumes = [
                k.volume
                for k in klines[:-1][-5:]
                if (k.volume is not None and k.volume > 0)
            ]

            today_volume = latest.volume

            if today_volume is not None and today_volume > 0 and volumes:

                average_volume = sum(volumes) / len(volumes)

                if average_volume > 0:

                    volume_ratio = today_volume / average_volume

        # =====================================================
        # 涨跌停
        # =====================================================

        limit_percent = self._get_limit_percent(symbol)

        limit_up = None
        limit_down = None

        if prev_close is not None and prev_close > 0 and limit_percent is not None:

            limit_up = round(
                prev_close * (1 + limit_percent),
                2,
            )

            limit_down = round(
                prev_close * (1 - limit_percent),
                2,
            )

        # =====================================================
        # 交易状态
        # =====================================================

        status = self._get_status(
            last_price=last_price,
            volume=volume,
            limit_up=limit_up,
            limit_down=limit_down,
        )

        # =====================================================
        # 构造 Quote
        # =====================================================

        return Quote(
            symbol=symbol,
            timestamp=latest.timestamp,
            source="yinhe",
            currency="CNY",
            last_price=last_price,
            previous_close=prev_close,
            open_price=open_price,
            high_price=high_price,
            low_price=low_price,
            change=change,
            change_percent=change_percent,
            amplitude=amplitude,
            volume=volume,
            amount=amount,
            average_price=average_price,
            turnover=turnover,
            volume_ratio=volume_ratio,
            market_cap=market_cap,
            float_market_cap=float_market_cap,
            limit_up=limit_up,
            limit_down=limit_down,
            status=status,
        )

    # =========================================================
    # 涨跌停比例
    # =========================================================

    @staticmethod
    def _get_limit_percent(
        symbol: str,
    ) -> float:
        """
        获取涨跌停比例。
        """

        symbol = symbol.upper()

        # -----------------------------------------------------
        # 科创板 / 创业板
        # -----------------------------------------------------

        if (
            symbol.startswith("688")
            or symbol.startswith("300")
            or symbol.startswith("301")
        ):
            return 0.20

        # -----------------------------------------------------
        # 北交所
        # -----------------------------------------------------

        if symbol.startswith("8") or symbol.startswith("4"):
            return 0.30

        # -----------------------------------------------------
        # 主板
        # -----------------------------------------------------

        return 0.10

    # =========================================================
    # 交易状态
    # =========================================================

    @staticmethod
    def _get_status(
        last_price,
        volume,
        limit_up,
        limit_down,
    ):
        """
        判断股票交易状态。
        """

        if last_price is None:
            return "unknown"

        if volume is not None and volume == 0:
            return "suspended"

        if limit_up is not None and last_price >= limit_up:
            return "limit_up"

        if limit_down is not None and last_price <= limit_down:
            return "limit_down"

        return "trading"
