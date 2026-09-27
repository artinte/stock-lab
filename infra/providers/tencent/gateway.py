from __future__ import annotations

from datetime import datetime
import re
from typing import Any, Optional
import requests

from infra.gateways.stock_data import StockDataGateway
from common.constants import Interval
from core.models.stock.kline import Kline
from core.models.quote import Quote
from core.models.valuation import Valuation

from infra.registry import GatewayRegistry

"""
腾讯财经数据网关。

本模块实现基于腾讯财经公开接口的数据源适配器，
将腾讯财经返回的原始数据转换为项目内部统一的数据模型。

主要功能：

- 获取股票基础信息
- 获取股票实时行情
- 获取批量实时行情
- 获取历史 K 线
- 获取前复权 K 线
- 获取最近收盘价
- 根据行情计算部分行情指标
- 获取基础估值信息

数据流：

    DataManager
        ↓
    StockDataGateway
        ↓
    TencentGateway
        ↓
    腾讯财经公开接口

腾讯 K 线接口：

    https://web.ifzq.gtimg.cn/appstock/app/fqkline/get

腾讯实时行情接口：

    https://qt.gtimg.cn/q=sh600519

注意：

腾讯 K 线原始数据顺序为：

    [
        日期,
        开盘,
        收盘,
        最高,
        最低,
        成交量
    ]

即：

    row[1] = open
    row[2] = close
    row[3] = high
    row[4] = low
    row[5] = volume

这一点非常重要。
"""


@GatewayRegistry.register("tencent")
class TencentGateway(StockDataGateway):
    """
    腾讯财经数据网关。

    腾讯接口不需要账号登录。

    因此 login() 主要负责：

        - 初始化 HTTP Session
        - 设置请求头
        - 标记 Gateway 已启动
    """

    name = "tencent"

    display_name = "腾讯财经"

    KLINE_URL = "https://web.ifzq.gtimg.cn/" "appstock/app/fqkline/get"

    QUOTE_URL = "https://qt.gtimg.cn/q="

    def __init__(
        self,
        config: Optional[dict] = None,
    ) -> None:

        super().__init__(config)

        self.session: Optional[requests.Session] = None

        self.timeout = 10

    # ==========================================================
    # 生命周期
    # ==========================================================

    def login(
        self,
        config: Optional[dict] = None,
    ) -> bool:
        """
        启动腾讯数据源。

        腾讯不需要登录账号。
        """

        if config:
            self.config.update(config)

        self.timeout = int(
            self.config.get(
                "timeout",
                10,
            )
        )

        try:

            self.session = requests.Session()

            self.session.headers.update(
                {
                    "User-Agent": (
                        "Mozilla/5.0 "
                        "(Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 "
                        "(KHTML, like Gecko) "
                        "Chrome/131.0 Safari/537.36"
                    ),
                    "Referer": ("https://finance.qq.com/"),
                }
            )

            self._started = True

            print("[腾讯网关] 启动成功")

            return True

        except Exception as exc:

            print(f"[腾讯网关] 启动失败: {exc}")

            self._started = False

            return False

    def logout(self) -> None:
        """
        关闭腾讯数据源。
        """

        if self.session is not None:

            try:
                self.session.close()

            except Exception:
                pass

        self.session = None

        self._started = False

    def health_check(self) -> bool:
        """
        检查腾讯数据接口是否可以正常访问。
        """

        try:

            self._ensure_started()

            symbol = "600519.SH"

            quote = self.fetch_quote(symbol)

            return quote is not None

        except Exception as exc:

            print(f"[腾讯网关] 健康检查失败: {exc}")

            return False

    # ==========================================================
    # 股票基础信息
    # ==========================================================

    def fetch_basic_info(
        self,
        symbol: str,
    ):
        """
        获取股票基础信息。

        腾讯实时行情接口可以提供股票名称，
        因此这里使用行情接口获取基础信息。
        """

        self._ensure_started()

        formatted_symbol = self._normalize_symbol(symbol)

        try:

            quote_data = self._fetch_quote_raw(formatted_symbol)

            if quote_data is None:
                return None

            name = quote_data.get("name")

            return {
                "symbol": self._to_standard_symbol(formatted_symbol),
                "name": name,
            }

        except Exception as exc:

            print(f"[腾讯网关] 获取股票基础信息失败 " f"{formatted_symbol}: {exc}")

            return None

    # ==========================================================
    # 实时行情
    # ==========================================================

    def fetch_quote(
        self,
        symbol: str,
    ) -> Optional[Quote]:
        """
        获取股票最新行情。

        腾讯实时行情接口：

            qt.gtimg.cn

        这里优先使用腾讯实时行情。

        如果实时行情接口没有提供某些字段，
        则使用最近 K 线辅助计算。
        """

        self._ensure_started()

        formatted_symbol = self._normalize_symbol(symbol)

        try:

            raw = self._fetch_quote_raw(formatted_symbol)

            if raw is None:
                return None

            price = raw.get("price")

            prev_close = raw.get("prev_close")

            open_price = raw.get("open")

            high = raw.get("high")

            low = raw.get("low")

            change = raw.get("change")

            change_percent = raw.get("change_percent")

            volume = raw.get("volume")

            amount = raw.get("amount")

            turnover = raw.get("turnover")

            market_cap = raw.get("market_cap")

            # --------------------------------------------------
            # 如果实时接口没有价格，则使用最近 K 线
            # --------------------------------------------------

            if price is None:

                klines = self.fetch_kline(
                    symbol=formatted_symbol,
                    interval=Interval.DAY_1,
                    limit=2,
                )

                if not klines:
                    return None

                latest = klines[-1]

                previous = klines[-2] if len(klines) >= 2 else None

                price = latest.close
                open_price = latest.open
                high = latest.high
                low = latest.low
                volume = latest.volume
                amount = latest.amount

                if previous is not None:

                    prev_close = previous.close

                    if prev_close:

                        change = price - prev_close

                        change_percent = change / prev_close * 100

            # --------------------------------------------------
            # 如果没有昨收，尝试从实时行情计算
            # --------------------------------------------------

            if change is not None and price is not None and change_percent is None:

                previous_price = price - change

                if previous_price != 0:

                    change_percent = change / previous_price * 100

            # --------------------------------------------------
            # 均价
            # --------------------------------------------------

            average_price = raw.get("average_price")

            if (
                average_price is None
                and amount is not None
                and volume is not None
                and volume != 0
            ):

                average_price = amount / volume

            # --------------------------------------------------
            # 振幅
            # --------------------------------------------------

            amplitude = None

            if (
                prev_close is not None
                and prev_close != 0
                and high is not None
                and low is not None
            ):

                amplitude = (high - low) / prev_close * 100

            # --------------------------------------------------
            # 涨跌停
            # --------------------------------------------------

            high_limit = None
            low_limit = None

            if prev_close is not None:

                high_limit, low_limit = self._calculate_limit_price(
                    formatted_symbol,
                    prev_close,
                    raw.get("name"),
                )

            # --------------------------------------------------
            # 股本
            #
            # 腾讯实时接口没有稳定提供总股本 /
            # 流通股本，因此这里保留 None。
            # --------------------------------------------------

            total_shares = raw.get("total_shares")

            float_shares = raw.get("float_shares")

            # --------------------------------------------------
            # 如果有股本，可以进一步计算市值
            # --------------------------------------------------

            if market_cap is None and total_shares is not None and price is not None:

                market_cap = total_shares * price / 10000

            circulating_market_cap = None

            if float_shares is not None and price is not None:

                circulating_market_cap = float_shares * price / 10000

            # --------------------------------------------------
            # PE
            #
            # 腾讯实时接口不作为本项目 PE 数据源。
            # 暂时保持 None。
            # --------------------------------------------------

            pe_dynamic = raw.get("pe_dynamic")

            pe_ttm = raw.get("pe_ttm")

            pb = raw.get("pb")

            return Quote(
                symbol=self._to_standard_symbol(formatted_symbol),
                name=raw.get("name"),
                timestamp=raw.get("timestamp"),
                last_price=price,
                previous_close=prev_close,
                open_price=open_price,
                high_price=high,
                low_price=low,
                change=change,
                change_percent=change_percent,
                volume=volume,
                amount=amount,
                turnover=turnover,
                volume_ratio=raw.get("volume_ratio"),
                market_cap=market_cap,
                float_market_cap=(circulating_market_cap),
                average_price=average_price,
                amplitude=amplitude,
            )

        except Exception as exc:

            print(f"[腾讯网关] 获取行情失败 " f"{formatted_symbol}: {exc}")

            return None

    # ==========================================================
    # 批量行情
    # ==========================================================

    def fetch_quotes(
        self,
        symbols: list[str],
    ) -> list[Quote]:
        """
        批量获取股票行情。

        腾讯接口支持：

            sh600519,sz000001,...

        一次请求多个股票。
        """

        self._ensure_started()

        if not symbols:
            return []

        result: list[Quote] = []

        formatted_symbols = [self._normalize_symbol(symbol) for symbol in symbols]

        try:

            raw_data = self._fetch_quotes_raw(formatted_symbols)

            for formatted_symbol in formatted_symbols:

                raw = raw_data.get(formatted_symbol)

                if raw is None:
                    continue

                quote = self._build_quote(
                    formatted_symbol,
                    raw,
                )

                if quote is not None:
                    result.append(quote)

        except Exception as exc:

            print(f"[腾讯网关] 批量获取行情失败: {exc}")

        return result

    # ==========================================================
    # K 线
    # ==========================================================

    def fetch_income_statement_abandon(
        self,
        symbol: str,
    ):
        """
        Mock：获取利润表。
        """

        return {
            "symbol": symbol,
            "report_date": "2025-12-31",
            "report_type": "annual",
            "operating_income": 100_000_000.0,
            "operating_cost": 70_000_000.0,
            "total_profit": 35_000_000.0,
            "net_profit": 30_000_000.0,
            "net_profit_attributable": 28_000_000.0,
            "eps": 1.20,
            "source": "akshare_mock",
            "timestamp": datetime.now(),
        }

    def fetch_balance_sheet(
        self,
        symbol: str,
    ):
        """
        Mock：获取资产负债表。
        """

        return {
            "symbol": symbol,
            "report_date": "2025-12-31",
            "report_type": "annual",
            "total_assets": 500_000_000.0,
            "total_liabilities": 200_000_000.0,
            "total_equity": 300_000_000.0,
            "cash": 80_000_000.0,
            "accounts_receivable": 50_000_000.0,
            "inventory": 60_000_000.0,
            "fixed_assets": 150_000_000.0,
            "source": "akshare_mock",
            "timestamp": datetime.now(),
        }

    def fetch_cash_flow(
        self,
        symbol: str,
    ):
        """
        Mock：获取现金流量表。
        """
        return {
            "symbol": symbol,
            "report_date": "2025-12-31",
            "report_type": "annual",
            "operating_cash_flow": 45_000_000.0,
            "investing_cash_flow": -20_000_000.0,
            "financing_cash_flow": 5_000_000.0,
            "free_cash_flow": 25_000_000.0,
            "source": "akshare_mock",
            "timestamp": datetime.now(),
        }

    def fetch_kline(
        self,
        symbol: str,
        interval: Interval = Interval.DAY_1,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 1000,
    ) -> list[Kline]:
        """
        获取腾讯历史 K 线。

        支持：

            1d
            1w
            1M

        腾讯接口返回：

            [
                日期,
                开盘,
                收盘,
                最高,
                最低,
                成交量
            ]

        注意：

            row[2] 是 close
            row[3] 是 high
            row[4] 是 low

        这是腾讯接口最容易解析错误的地方。
        """

        self._ensure_started()

        formatted_symbol = self._normalize_symbol(symbol)

        period = self._convert_interval(interval)

        count = max(
            int(limit),
            1,
        )

        params = {
            "param": (
                f"{formatted_symbol},"
                f"{period},"
                f"{self._format_date(start_time)},"
                f"{self._format_date(end_time)},"
                f"{count},"
                f"qfq"
            )
        }

        try:

            response = self.session.get(
                self.KLINE_URL,
                params=params,
                timeout=self.timeout,
            )

            response.raise_for_status()

            data = response.json()

        except Exception as exc:

            print(f"[腾讯网关] K 线请求失败 " f"{formatted_symbol}: {exc}")

            return []

        try:

            stock_data = data["data"][formatted_symbol]

        except (
            KeyError,
            TypeError,
        ):

            print(f"[腾讯网关] 未找到 K 线数据: " f"{formatted_symbol}")

            return []

        # ------------------------------------------------------
        # 腾讯不同标的可能使用：
        #
        # qfqday
        # day
        #
        # qfqweek
        # week
        #
        # qfqmonth
        # month
        # ------------------------------------------------------

        possible_keys = [
            f"qfq{period}",
            period,
        ]

        rows = None

        for key in possible_keys:

            value = stock_data.get(key)

            if value:

                rows = value

                break

        if not rows:

            print(f"[腾讯网关] {formatted_symbol} " f"没有返回 {period} K 线")

            return []

        # ------------------------------------------------------
        # 转换
        # ------------------------------------------------------

        klines: list[Kline] = []

        for row in rows:

            try:

                if len(row) < 6:
                    continue

                timestamp = self._parse_datetime(row[0])

                # ==================================================
                # 非常重要：
                #
                # 腾讯：
                #
                # 0 日期
                # 1 Open
                # 2 Close
                # 3 High
                # 4 Low
                # 5 Volume
                #
                # 不是：
                #
                # Open High Low Close
                # ==================================================

                open_price = self._to_float(row[1])

                close_price = self._to_float(row[2])

                high_price = self._to_float(row[3])

                low_price = self._to_float(row[4])

                volume = self._to_float(row[5])

                if (
                    open_price is None
                    or close_price is None
                    or high_price is None
                    or low_price is None
                ):
                    continue

                klines.append(
                    Kline(
                        symbol=(self._to_standard_symbol(formatted_symbol)),
                        timestamp=timestamp,
                        interval=interval,
                        open=open_price,
                        high=high_price,
                        low=low_price,
                        close=close_price,
                        volume=(int(volume) if volume is not None else 0),
                        amount=None,
                    )
                )

            except Exception as exc:

                print(f"[腾讯网关] 转换 Kline 失败: " f"{exc}")

                print(f"    原始数据: {row}")

                continue

        klines.sort(key=lambda item: item.timestamp)

        if limit > 0:

            klines = klines[-limit:]

        return klines

    # ==========================================================
    # 财务数据
    # ==========================================================

    def fetch_financial(
        self,
        symbol: str,
    ):
        """
        获取财务数据。

        腾讯公开行情接口不提供本项目需要的完整财务报表。

        因此这里明确返回 None。
        """

        self._ensure_started()

        print(f"[腾讯网关] 暂未提供完整财务数据: " f"{symbol}")

        return None

    # ==========================================================
    # 估值
    # ==========================================================

    def fetch_valuation(
        self,
        symbol: str,
    ) -> Valuation:
        """
        获取基础估值。

        当前主要使用腾讯实时行情。

        腾讯接口没有稳定提供本项目要求的：

            PE(TTM)
            PE(静态)
            PE(动态)
            PB

        因此这些字段可能为 None。
        """

        self._ensure_started()

        formatted_symbol = self._normalize_symbol(symbol)

        quote = self.fetch_quote(formatted_symbol)

        if quote is None:

            return Valuation(
                symbol=self._to_standard_symbol(formatted_symbol),
                timestamp=datetime.now(),
            )

        return Valuation(
            symbol=quote.symbol,
            timestamp=(quote.timestamp or datetime.now()),
            price=quote.price,
            market_cap=quote.market_cap,
            pe_static=None,
            pe_dynamic=quote.pe_dynamic,
            pe_ttm=quote.pe_ttm,
            pb=quote.pb,
        )

    # ==========================================================
    # 原始实时行情
    # ==========================================================

    def _fetch_quote_raw(
        self,
        symbol: str,
    ) -> Optional[dict]:
        """
        获取腾讯原始实时行情。

        腾讯接口：

            https://qt.gtimg.cn/q=sh600519

        返回内容类似：

            v_sh600519="1~贵州茅台~600519~..."

        腾讯行情字段很多，这里只解析本项目当前
        需要的主要字段。
        """

        raw_data = self._fetch_quotes_raw([symbol])

        return raw_data.get(symbol)

    def _fetch_quotes_raw(
        self,
        symbols: list[str],
    ) -> dict[str, dict]:
        """
        批量获取腾讯实时行情。
        """

        if not symbols:
            return {}

        query = ",".join(symbols)

        url = self.QUOTE_URL + query

        response = self.session.get(
            url,
            timeout=self.timeout,
        )

        response.raise_for_status()

        text = response.text

        result: dict[str, dict] = {}

        # ------------------------------------------------------
        # 腾讯返回：
        #
        # v_sh600519="1~贵州茅台~600519~..."
        # ------------------------------------------------------

        pattern = re.compile(r'v_([a-zA-Z0-9]+)="([^"]*)"')

        matches = pattern.findall(text)

        for code, value in matches:

            fields = value.split("~")

            if len(fields) < 5:
                continue

            result[code.lower()] = self._parse_quote_fields(
                code.lower(),
                fields,
            )

        return result

    # ==========================================================
    # 腾讯行情字段解析
    # ==========================================================

    @classmethod
    def _parse_quote_fields(
        cls,
        symbol: str,
        fields: list[str],
    ) -> dict:
        """
        解析腾讯实时行情字段。

        腾讯常见字段：

            0  市场状态
            1  股票名称
            2  股票代码
            3  当前价格
            4  昨收
            5  今开
            6  成交量
            31 换手率
            32 市盈率
            33 总市值
            34 流通市值

        不同版本接口字段可能存在差异，
        因此这里全部采用安全读取。
        """

        def field(
            index: int,
        ) -> Optional[str]:

            if index >= len(fields):
                return None

            value = fields[index]

            if value in (
                "",
                "-",
                "--",
            ):
                return None

            return value

        def number(
            index: int,
        ) -> Optional[float]:

            value = field(index)

            if value is None:
                return None

            try:
                return float(value)

            except (
                TypeError,
                ValueError,
            ):
                return None

        name = field(1)

        price = number(3)

        prev_close = number(4)

        open_price = number(5)

        volume = number(6)

        # 腾讯这里成交量通常为“手”
        # 本项目 Kline / Quote 统一按原始成交量保留。
        #
        # 因此不在这里强行 *100。
        #

        amount = number(37)

        high = number(33)

        low = number(34)

        # ------------------------------------------------------
        # 一些腾讯接口版本中字段位置可能变化。
        #
        # 如果 high / low 明显不合理，
        # 则后面 fetch_quote 会通过 K 线补齐。
        # ------------------------------------------------------

        change = None
        change_percent = None

        if price is not None and prev_close is not None:

            change = price - prev_close

            if prev_close != 0:

                change_percent = change / prev_close * 100

        return {
            "symbol": symbol,
            "name": name,
            "timestamp": datetime.now(),
            "last_price": price,
            "previous_close": prev_close,
            "open": open_price,
            "high": high,
            "low": low,
            "change": change,
            "change_percent": change_percent,
            "volume": volume,
            "amount": amount,
            "turnover": None,
            "volume_ratio": None,
            "total_shares": None,
            "float_shares": None,
            "market_cap": None,
            "average_price": None,
            "pe_dynamic": None,
            "pe_ttm": None,
            "pb": None,
        }

    # ==========================================================
    # 构造 Quote
    # ==========================================================

    def _build_quote(
        self,
        symbol: str,
        raw: dict,
    ) -> Optional[Quote]:
        """
        将原始行情转换成 Quote。
        """

        price = raw.get("price")

        prev_close = raw.get("prev_close")

        open_price = raw.get("open")

        high = raw.get("high")

        low = raw.get("low")

        volume = raw.get("volume")

        amount = raw.get("amount")

        change = raw.get("change")

        change_percent = raw.get("change_percent")

        average_price = None

        if amount is not None and volume is not None and volume != 0:

            average_price = amount / volume

        amplitude = None

        if prev_close and high is not None and low is not None:

            amplitude = (high - low) / prev_close * 100

        high_limit = None
        low_limit = None

        if prev_close is not None:

            high_limit, low_limit = self._calculate_limit_price(
                symbol,
                prev_close,
                raw.get("name"),
            )

        return Quote(
            symbol=self._to_standard_symbol(symbol),
            name=raw.get("name"),
            timestamp=raw.get("timestamp"),
            price=price,
            previous_close=prev_close,
            open_price=open_price,
            high_price=high,
            low_price=low,
            change=change,
            change_percent=change_percent,
            volume=volume,
            amount=amount,
            turnover=raw.get("turnover"),
            volume_ratio=raw.get("volume_ratio"),
            market_cap=raw.get("market_cap"),
            float_market_cap=None,
            average_price=average_price,
            amplitude=amplitude,
        )

    # ==========================================================
    # 涨跌停
    # ==========================================================

    @staticmethod
    def _calculate_limit_price(
        symbol: str,
        prev_close: float,
        name: Optional[str],
    ) -> tuple[
        Optional[float],
        Optional[float],
    ]:
        """
        根据股票类型估算涨跌停价格。

        普通 A 股：
            ±10%

        科创板 / 创业板：
            ±20%

        北交所：
            ±30%

        ST：
            ±5%

        注意：

        这里属于计算值，不是腾讯接口直接返回值。
        """

        if prev_close is None:
            return None, None

        code = symbol.split(
            ".",
            1,
        )[0]

        stock_name = (name or "").upper()

        # ------------------------------------------------------
        # ST
        # ------------------------------------------------------

        if "ST" in stock_name or "*ST" in stock_name:

            ratio = 0.05

        # ------------------------------------------------------
        # 北交所
        # ------------------------------------------------------

        elif code.startswith(
            (
                "4",
                "8",
            )
        ):

            ratio = 0.30

        # ------------------------------------------------------
        # 科创板 / 创业板
        # ------------------------------------------------------

        elif code.startswith(
            (
                "300",
                "301",
                "688",
                "689",
            )
        ):

            ratio = 0.20

        else:

            ratio = 0.10

        return (
            round(
                prev_close * (1 + ratio),
                2,
            ),
            round(
                prev_close * (1 - ratio),
                2,
            ),
        )

    # ==========================================================
    # 周期转换
    # ==========================================================

    @staticmethod
    def _convert_interval(
        interval: Interval,
    ) -> str:
        """
        将统一 Interval 转换成腾讯周期。
        """

        if interval == Interval.DAY_1:
            return "day"

        if interval == Interval.WEEK_1:
            return "week"

        if interval == Interval.MONTH_1:
            return "month"

        raise ValueError("腾讯 K 线暂不支持该周期：" f"{interval}")

    # ==========================================================
    # 股票代码
    # ==========================================================

    @staticmethod
    def _normalize_symbol(
        symbol: str,
    ) -> str:
        """
        将统一股票代码转换为腾讯格式。

        支持：

            600519
            600519.SH

            000001
            000001.SZ

            300750
            688981

        转换：

            sh600519
            sz000001
            sz300750
            sh688981
        """

        value = symbol.strip().upper()

        # ----------------------------------------------
        # 已经是腾讯格式
        # ----------------------------------------------

        if value.startswith(
            (
                "SH",
                "SZ",
                "BJ",
            )
        ):

            return value.lower()

        # ----------------------------------------------
        # 带交易所后缀
        # ----------------------------------------------

        if "." in value:

            code, exchange = value.split(
                ".",
                1,
            )

            exchange = exchange.upper()

            if exchange == "SH":
                return f"sh{code}"

            if exchange == "SZ":
                return f"sz{code}"

            if exchange == "BJ":
                return f"bj{code}"

            raise ValueError(f"不支持的交易所：{exchange}")

        # ----------------------------------------------
        # 上海
        # ----------------------------------------------

        if value.startswith(
            (
                "600",
                "601",
                "603",
                "605",
                "688",
                "689",
            )
        ):

            return f"sh{value}"

        # ----------------------------------------------
        # 深圳
        # ----------------------------------------------

        if value.startswith(
            (
                "000",
                "001",
                "002",
                "003",
                "300",
                "301",
            )
        ):

            return f"sz{value}"

        # ----------------------------------------------
        # 北京
        # ----------------------------------------------

        if value.startswith(
            (
                "4",
                "8",
            )
        ):

            return f"bj{value}"

        raise ValueError(f"无法判断股票交易所：{symbol}")

    @staticmethod
    def _to_standard_symbol(
        symbol: str,
    ) -> str:
        """
        腾讯代码：

            sh600519

        转：

            600519.SH
        """

        value = symbol.strip().upper()

        if value.startswith("SH"):

            return value[2:] + ".SH"

        if value.startswith("SZ"):

            return value[2:] + ".SZ"

        if value.startswith("BJ"):

            return value[2:] + ".BJ"

        return value

    # ==========================================================
    # 日期
    # ==========================================================

    @staticmethod
    def _format_date(
        value: Optional[datetime],
    ) -> str:
        """
        转换日期。

        None 返回空字符串。
        """

        if value is None:
            return ""

        return value.strftime("%Y-%m-%d")

    @staticmethod
    def _parse_datetime(
        value: Any,
    ) -> datetime:
        """
        解析腾讯日期。
        """

        if isinstance(
            value,
            datetime,
        ):
            return value

        if hasattr(
            value,
            "to_pydatetime",
        ):

            return value.to_pydatetime()

        text = str(value)

        return datetime.strptime(
            text[:10],
            "%Y-%m-%d",
        )

    @staticmethod
    def _to_float(
        value: Any,
        default: Optional[float] = None,
    ) -> Optional[float]:
        """
        安全转换 float。
        """

        if value is None:
            return default

        try:

            return float(value)

        except (
            TypeError,
            ValueError,
        ):

            return default

    # ==========================================================
    # 状态
    # ==========================================================

    def _ensure_started(self) -> None:
        """
        确保腾讯数据源已经启动。
        """

        if not self._started:

            raise RuntimeError("腾讯数据源尚未启动，" "请先调用 DataManager.start()")


# ==============================================================
# 测试
# ==============================================================


def main() -> None:
    """
    腾讯数据网关测试。
    """

    print()
    print("腾讯财经数据网关测试")
    print()

    gateway = TencentGateway(
        {
            "timeout": 10,
        }
    )

    try:

        # ------------------------------------------------------
        # 1. 启动
        # ------------------------------------------------------

        print("[1/6] 启动腾讯数据源")

        if not gateway.login():

            print("❌ 启动失败")

            return

        print("✅ 启动成功")

        # ------------------------------------------------------
        # 2. 健康检查
        # ------------------------------------------------------

        print()
        print("[2/6] 健康检查")

        if gateway.health_check():

            print("✅ 腾讯接口正常")

        else:

            print("❌ 腾讯接口异常")

            return

        # ------------------------------------------------------
        # 3. 股票基础信息
        # ------------------------------------------------------

        symbol = "600519.SH"

        print()
        print(f"[3/6] 股票基础信息：{symbol}")

        stock = gateway.fetch_basic_info(symbol)

        print(stock)

        # ------------------------------------------------------
        # 4. K 线
        # ------------------------------------------------------

        print()
        print(f"[4/6] 获取 K 线：{symbol}")

        klines = gateway.fetch_kline(
            symbol=symbol,
            interval=Interval.DAY_1,
            limit=10,
        )

        print(f"获取到 {len(klines)} 条 K 线")

        for kline in klines:

            print(
                f"{kline.timestamp:%Y-%m-%d} "
                f"O={kline.open:.2f} "
                f"H={kline.high:.2f} "
                f"L={kline.low:.2f} "
                f"C={kline.close:.2f} "
                f"V={kline.volume}"
            )

        # ------------------------------------------------------
        # 5. 行情
        # ------------------------------------------------------

        print()
        print(f"[5/6] 获取最新行情：{symbol}")

        quote = gateway.fetch_quote(symbol)

        if quote is None:

            print("❌ 获取行情失败")

        else:

            print(f"股票: {quote.name}")

            print(f"代码: {quote.symbol}")

            print(f"价格: {quote.price}")

            print(f"昨收: {quote.previous_close}")

            print(f"开盘: {quote.open}")

            print(f"最高: {quote.high}")

            print(f"最低: {quote.low}")

            print(f"涨跌: {quote.change}")

            print(f"涨跌幅: {quote.change_percent}%")

            print(f"成交量: {quote.volume}")

            print(f"成交额: {quote.amount}")

            print(f"换手率: {quote.turnover}")

            print(f"总市值: {quote.market_cap}")

            print(f"均价: {quote.average_price}")

            print(f"振幅: {quote.amplitude}")

            print(f"涨停: {quote.high_limit}")

            print(f"跌停: {quote.low_limit}")

        # ------------------------------------------------------
        # 6. 估值
        # ------------------------------------------------------

        print()
        print(f"[6/6] 获取估值：{symbol}")

        valuation = gateway.fetch_valuation(symbol)

        print(f"价格: {valuation.price}")

        print(f"总市值: {valuation.market_cap}")

        print(f"PE(TTM): {valuation.pe_ttm}")

        print(f"PE(静态): {valuation.pe_static}")

        print(f"PE(动态): {valuation.pe_dynamic}")

        print(f"PB: {valuation.pb}")

        print()
        print("✅ 腾讯数据网关测试完成")

    except KeyboardInterrupt:

        print()
        print("⚠️ 用户中断")

    except Exception as exc:

        print()
        print(f"❌ 测试异常: {exc}")

        import traceback

        traceback.print_exc()

    finally:

        print()

        print("正在关闭腾讯数据源...")

        gateway.logout()

        print("腾讯数据源已关闭")


if __name__ == "__main__":
    main()
