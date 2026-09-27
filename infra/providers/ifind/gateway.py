from __future__ import annotations

import os
from datetime import datetime
from typing import Optional

import pandas as pd

from iFinDPy import (
THS_HF,
THS_HQ,
THS_RQ,
THS_iFinDLogin,
THS_iFinDLogout,
THS_Trans2DataFrame,
)

from common.constants import Interval
from core.models.financial.balance_sheet import BalanceSheet
from core.models.financial.cash_flow import CashFlow
from core.models.financial.financial import Financial
from core.models.financial.income_statement import IncomeStatement
from core.models.stock.kline import Kline
from core.models.quote import Quote
from core.models.stock.basic_info import BasicInfo
from infra.base import StockDataGateway

class IFinDGateway(StockDataGateway):
    """
    同花顺 iFinD 数据网关。

    ```
    数据源：
        同花顺 iFinD

    Python SDK：
        iFinDPy

    主要功能：
        - 登录 / 登出
        - 健康检查
        - 股票基础信息
        - 实时行情
        - 批量实时行情
        - 日 / 周 / 月 K 线
        - 分钟 K 线

    注意：
        财务数据和估值数据需要根据 iFinD
        实际开通的指标权限配置指标名称。
    """

    name = "ifind"
    display_name = "同花顺 iFinD"

    def __init__(
        self,
        config: Optional[dict] = None,
    ) -> None:
        super().__init__(config)

        self.username = self.config.get(
            "username",
            os.getenv("IFIND_USERNAME"),
        )

        self.password = self.config.get(
            "password",
            os.getenv("IFIND_PASSWORD"),
        )

    # ============================================================
    # 生命周期
    # ============================================================

    def login(
        self,
        config: Optional[dict] = None,
    ) -> bool:
        """
        登录 iFinD。

        返回：
            True  登录成功
            False 登录失败
        """

        if config:
            self.config.update(config)

            self.username = self.config.get(
                "username",
                os.getenv("IFIND_USERNAME"),
            )

            self.password = self.config.get(
                "password",
                os.getenv("IFIND_PASSWORD"),
            )

        if not self.username or not self.password:
            print("[iFinD] 未配置账号或密码")
            return False

        try:
            result = THS_iFinDLogin(
                self.username,
                self.password,
            )

            # iFinD:
            # 0    登录成功
            # -201 已经登录
            if result in (0, -201):
                self._started = True
                print("[iFinD] 登录成功")
                return True

            print(f"[iFinD] 登录失败，错误码: {result}")
            return False

        except Exception as exc:
            print(f"[iFinD] 登录异常: {exc}")
            self._started = False
            return False

    def logout(self) -> None:
        """
        登出 iFinD。
        """

        if not self._started:
            return

        try:
            THS_iFinDLogout()
            print("[iFinD] 已登出")
        except Exception as exc:
            print(f"[iFinD] 登出异常: {exc}")
        finally:
            self._started = False

    def health_check(self) -> bool:
        """
        检查 iFinD 当前是否可以正常访问。

        这里通过获取一只股票的实时行情进行检查。
        """

        if not self._started:
            return False

        try:
            result = THS_RQ(
                "600519.SH",
                "latest",
                "",
            )

            return self._is_success(result)

        except Exception as exc:
            print(f"[iFinD] 健康检查失败: {exc}")
            return False

    # ============================================================
    # 股票
    # ============================================================

    def fetch_stock(
        self,
        symbol: str,
    ) -> BasicInfo:
        """
        获取股票基础信息。

        iFinD 可以通过 THS_BD 获取大量基础指标。
        这里使用最基本的股票名称、证券代码等信息。

        如果你的 Stock 模型字段更多，可以继续增加指标。
        """

        from iFinDPy import THS_BD

        symbol = self._normalize_symbol(symbol)

        result = THS_BD(
            symbol,
            "ths_stock_short_name",
            "",
        )

        df = self._to_dataframe(result)

        name = symbol

        if not df.empty:
            value = self._first_value(df)

            if value is not None:
                name = str(value)

        return BasicInfo(
            symbol=symbol,
            name=name,
        )

    # ============================================================
    # 实时行情
    # ============================================================

    def fetch_quote(
        self,
        symbol: str,
    ) -> Quote:
        """
        获取单只股票实时行情。
        """

        symbol = self._normalize_symbol(symbol)

        indicators = (
            "latest;"
            "preClose;"
            "open;"
            "high;"
            "low;"
            "change;"
            "changeRatio;"
            "volume;"
            "amount;"
            "turnoverRatio;"
            "amplitude;"
            "averagePrice;"
            "totalShares;"
            "floatShares;"
            "marketValue;"
            "floatMarketValue;"
            "upperLimit;"
            "lowerLimit;"
        )

        result = THS_RQ(
            symbol,
            indicators,
            "",
        )

        data = self._extract_realtime(result)

        now = datetime.now()

        return Quote(
            symbol=symbol,
            name=str(data.get("name", symbol)),
            timestamp=now,

            last_price=self._float(data.get("latest")),
            prev_close=self._float(data.get("preClose")),

            open=self._float(data.get("open")),
            high=self._float(data.get("high")),
            low=self._float(data.get("low")),

            change=self._float(data.get("change")),
            change_percent=self._float(data.get("changeRatio")),

            volume=self._float(data.get("volume")),
            amount=self._float(data.get("amount")),

            turnover=self._float(data.get("turnoverRatio")),

            total_shares=self._float(data.get("totalShares")),
            circulating_shares=self._float(data.get("floatShares")),

            market_cap=self._float(data.get("marketValue")),
            circulating_market_cap=self._float(
                data.get("floatMarketValue")
            ),

            amplitude=self._float(data.get("amplitude")),
            average_price=self._float(data.get("averagePrice")),

            volume_ratio=None,

            limit_up=self._float(data.get("upperLimit")),
            limit_down=self._float(data.get("lowerLimit")),

            status=None,
            source=self.display_name,
        )

    def fetch_quotes(
        self,
        symbols: list[str],
    ) -> list[Quote]:
        """
        批量获取实时行情。

        iFinD 支持一次传入多个证券代码。
        """

        if not symbols:
            return []

        normalized = [
            self._normalize_symbol(symbol)
            for symbol in symbols
        ]

        code_string = ",".join(normalized)

        indicators = (
            "latest;"
            "preClose;"
            "open;"
            "high;"
            "low;"
            "change;"
            "changeRatio;"
            "volume;"
            "amount;"
            "turnoverRatio;"
            "amplitude;"
            "averagePrice;"
            "totalShares;"
            "floatShares;"
            "marketValue;"
            "floatMarketValue;"
            "upperLimit;"
            "lowerLimit;"
        )

        result = THS_RQ(
            code_string,
            indicators,
            "",
        )

        rows = self._extract_realtime_rows(result)

        quotes: list[Quote] = []

        for row in rows:
            symbol = self._normalize_symbol(
                row.get("thscode")
                or row.get("code")
                or ""
            )

            if not symbol:
                continue

            data = row.get("data", row)

            quotes.append(
                Quote(
                    symbol=symbol,
                    name=str(data.get("name", symbol)),
                    timestamp=datetime.now(),

                    last_price=self._float(
                        data.get("latest")
                    ),
                    prev_close=self._float(
                        data.get("preClose")
                    ),

                    open=self._float(data.get("open")),
                    high=self._float(data.get("high")),
                    low=self._float(data.get("low")),

                    change=self._float(
                        data.get("change")
                    ),
                    change_percent=self._float(
                        data.get("changeRatio")
                    ),

                    volume=self._float(
                        data.get("volume")
                    ),
                    amount=self._float(
                        data.get("amount")
                    ),

                    turnover=self._float(
                        data.get("turnoverRatio")
                    ),

                    total_shares=self._float(
                        data.get("totalShares")
                    ),
                    circulating_shares=self._float(
                        data.get("floatShares")
                    ),

                    market_cap=self._float(
                        data.get("marketValue")
                    ),
                    circulating_market_cap=self._float(
                        data.get("floatMarketValue")
                    ),

                    amplitude=self._float(
                        data.get("amplitude")
                    ),
                    average_price=self._float(
                        data.get("averagePrice")
                    ),

                    volume_ratio=None,

                    limit_up=self._float(
                        data.get("upperLimit")
                    ),
                    limit_down=self._float(
                        data.get("lowerLimit")
                    ),

                    status=None,
                    source=self.display_name,
                )
            )

        return quotes

    # ============================================================
    # K线
    # ============================================================

    def fetch_kline(
        self,
        symbol: str,
        interval: Interval = Interval.DAY_1,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 1000,
    ) -> list[Kline]:
        """
        获取历史 K 线。

        日 / 周 / 月：
            THS_HQ

        分钟：
            THS_HF
        """

        symbol = self._normalize_symbol(symbol)

        end = end_time or datetime.now()

        if start_time is None:
            # 根据 limit 粗略向前推。
            # 最终再使用 tail(limit) 控制数量。
            start = datetime(
                end.year - 5,
                end.month,
                end.day,
            )
        else:
            start = start_time

        start_date = start.strftime("%Y-%m-%d")
        end_date = end.strftime("%Y-%m-%d")

        # --------------------------------------------------------
        # 日 / 周 / 月
        # --------------------------------------------------------

        if interval in {
            Interval.DAY_1,
            Interval.WEEK_1,
            Interval.MONTH_1,
        }:
            period = {
                Interval.DAY_1: "D",
                Interval.WEEK_1: "W",
                Interval.MONTH_1: "M",
            }[interval]

            result = THS_HQ(
                symbol,
                "open;high;low;close;volume;amount",
                f"Interval:{period},Fill:Omit",
                start_date,
                end_date,
            )

        # --------------------------------------------------------
        # 分钟
        # --------------------------------------------------------

        else:
            minute = {
                Interval.MINUTE_1: 1,
                Interval.MINUTE_5: 5,
                Interval.MINUTE_15: 15,
                Interval.MINUTE_30: 30,
                Interval.MINUTE_60: 60,
            }.get(interval)

            if minute is None:
                raise ValueError(
                    f"iFinD 不支持的 K 线周期: {interval}"
                )

            result = THS_HF(
                symbol,
                "open;high;low;close;volume;amount",
                f"Interval:{minute},Fill:Omit",
                start.strftime("%Y-%m-%d %H:%M:%S"),
                end.strftime("%Y-%m-%d %H:%M:%S"),
            )

        df = self._to_dataframe(result)

        if df.empty:
            return []

        df = self._normalize_kline_dataframe(df)

        if limit > 0:
            df = df.tail(limit)

        klines: list[Kline] = []

        for _, row in df.iterrows():

            timestamp = self._parse_datetime(
                row.get("time")
            )

            if timestamp is None:
                continue

            klines.append(
                Kline(
                    symbol=symbol,
                    timestamp=timestamp,
                    interval=interval,

                    open=self._float(row.get("open")),
                    high=self._float(row.get("high")),
                    low=self._float(row.get("low")),
                    close=self._float(row.get("close")),

                    volume=self._float(row.get("volume")),
                    amount=self._float(row.get("amount")),
                )
            )

        return klines

    # ============================================================
    # 财务报表
    # ============================================================

    def fetch_balance_sheet(
        self,
        symbol: str,
    ) -> BalanceSheet:
        """
        获取资产负债表。

        注意：
        iFinD 财务指标名称由账号权限和指标体系决定。
        建议单独建立 financial/ifind.py 做指标映射。
        """

        raise NotImplementedError(
            "请根据 iFinD 账号实际开通的财务指标配置 "
            "BalanceSheet 映射。"
        )

    def fetch_income_statement(
        self,
        symbol: str,
    ) -> IncomeStatement:
        """
        获取利润表。
        """

        raise NotImplementedError(
            "请根据 iFinD 账号实际开通的财务指标配置 "
            "IncomeStatement 映射。"
        )

    def fetch_cash_flow(
        self,
        symbol: str,
    ) -> CashFlow:
        """
        获取现金流量表。
        """

        raise NotImplementedError(
            "请根据 iFinD 账号实际开通的财务指标配置 "
            "CashFlowStatement 映射。"
        )

    def fetch_financial(
        self,
        symbol: str,
    ) -> Financial:
        """
        获取综合财务数据。
        """

        raise NotImplementedError(
            "请根据 iFinD 账号实际开通的财务指标配置 "
            "Financial 映射。"
        )

    # ============================================================
    # 估值
    # ============================================================

    def fetch_valuation(
        self,
        symbol: str,
    ):
        """
        获取估值数据。

        估值模型建议保持：
            原始数据
            +
            计算数据

        分离。

        这里暂时不直接硬编码 iFinD 指标，
        避免把数据源字段和你的 Valuation 模型耦合。
        """

        raise NotImplementedError(
            "请根据 iFinD 实际开通的估值指标配置 Valuation 映射。"
        )

    # ============================================================
    # 工具方法
    # ============================================================

    @staticmethod
    def _normalize_symbol(
        symbol: str,
    ) -> str:
        """
        标准化股票代码。

        支持：

            600519
            600519.SH
            000001
            000001.SZ
            300750.SZ
        """

        symbol = symbol.strip().upper()

        if "." in symbol:
            return symbol

        if symbol.startswith(
            (
                "600",
                "601",
                "603",
                "605",
                "688",
                "689",
            )
        ):
            return f"{symbol}.SH"

        if symbol.startswith(
            (
                "000",
                "001",
                "002",
                "003",
                "300",
                "301",
            )
        ):
            return f"{symbol}.SZ"

        if symbol.startswith(
            (
                "430",
                "830",
                "831",
                "832",
                "833",
                "834",
                "835",
                "836",
                "837",
                "838",
                "839",
                "870",
                "871",
                "872",
                "873",
                "920",
            )
        ):
            return f"{symbol}.BJ"

        return symbol

    @staticmethod
    def _float(
        value,
    ) -> Optional[float]:
        """
        安全转换 float。
        """

        if value is None:
            return None

        try:
            if pd.isna(value):
                return None
        except Exception:
            pass

        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _parse_datetime(
        value,
    ) -> Optional[datetime]:
        """
        解析 iFinD 时间。
        """

        if value is None:
            return None

        if isinstance(value, datetime):
            return value

        try:
            timestamp = pd.to_datetime(value)

            if pd.isna(timestamp):
                return None

            return timestamp.to_pydatetime()

        except Exception:
            return None

    @staticmethod
    def _to_dataframe(
        result,
    ) -> pd.DataFrame:
        """
        将 iFinD 返回结果统一转换成 DataFrame。
        """

        if result is None:
            return pd.DataFrame()

        try:
            errorcode = getattr(
                result,
                "errorcode",
                0,
            )

            if errorcode not in (0, None):
                errmsg = getattr(
                    result,
                    "errmsg",
                    "",
                )

                print(
                    f"[iFinD] 数据请求失败 "
                    f"errorcode={errorcode}, "
                    f"errmsg={errmsg}"
                )

                return pd.DataFrame()

        except Exception:
            pass

        try:
            return THS_Trans2DataFrame(result)
        except Exception:
            pass

        # 某些版本直接返回 DataFrame
        if isinstance(result, pd.DataFrame):
            return result

        # 最后尝试 data
        data = getattr(
            result,
            "data",
            None,
        )

        if isinstance(data, pd.DataFrame):
            return data

        if isinstance(data, list):
            return pd.DataFrame(data)

        return pd.DataFrame()

    @staticmethod
    def _first_value(
        df: pd.DataFrame,
    ):
        """
        获取 DataFrame 第一行第一个有效值。
        """

        if df.empty:
            return None

        for column in df.columns:
            value = df.iloc[0][column]

            if value is None:
                continue

            try:
                if pd.isna(value):
                    continue
            except Exception:
                pass

            return value

        return None

    @staticmethod
    def _normalize_kline_dataframe(
        df: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        标准化 K 线字段。
        """

        df = df.copy()

        rename_map = {}

        for column in df.columns:

            name = str(column).lower()

            if name in {"time", "datetime", "date"}:
                rename_map[column] = "time"

            elif name in {"open", "open_price"}:
                rename_map[column] = "open"

            elif name in {"high", "high_price"}:
                rename_map[column] = "high"

            elif name in {"low", "low_price"}:
                rename_map[column] = "low"

            elif name in {
                "close",
                "latest",
                "close_price",
            }:
                rename_map[column] = "close"

            elif name in {
                "volume",
                "vol",
            }:
                rename_map[column] = "volume"

            elif name in {
                "amount",
                "turnover",
            }:
                rename_map[column] = "amount"

        df = df.rename(columns=rename_map)

        required = [
            "time",
            "open",
            "high",
            "low",
            "close",
            "volume",
            "amount",
        ]

        for column in required:
            if column not in df.columns:
                df[column] = None

        return df

    @staticmethod
    def _is_success(
        result,
    ) -> bool:
        """
        判断 iFinD 返回结果是否成功。
        """

        if result is None:
            return False

        try:
            return getattr(
                result,
                "errorcode",
                0,
            ) == 0
        except Exception:
            return True

    @staticmethod
    def _extract_realtime(
        result,
    ) -> dict:
        """
        从 THS_RQ 返回结果中提取单只股票数据。
        """

        rows = IFinDGateway._extract_realtime_rows(result)

        if not rows:
            return {}

        row = rows[0]

        if "data" in row:
            return row["data"]

        return row

    @staticmethod
    def _extract_realtime_rows(
        result,
    ) -> list[dict]:
        """
        尽量兼容 iFinDPy 不同版本的 THS_RQ 返回结构。
        """

        if result is None:
            return []

        # --------------------------------------------------------
        # tables
        # --------------------------------------------------------

        tables = getattr(
            result,
            "tables",
            None,
        )

        if isinstance(tables, list):
            rows = []

            for table in tables:
                if isinstance(table, dict):
                    rows.append(table)

            return rows

        # --------------------------------------------------------
        # data
        # --------------------------------------------------------

        data = getattr(
            result,
            "data",
            None,
        )

        if isinstance(data, pd.DataFrame):
            return data.to_dict(
                orient="records"
            )

        if isinstance(data, list):
            return data

        if isinstance(data, dict):
            return [data]

        # --------------------------------------------------------
        # dict
        # --------------------------------------------------------

        if isinstance(result, dict):

            tables = result.get("tables")

            if isinstance(tables, list):
                return tables

            data = result.get("data")

            if isinstance(data, list):
                return data

            if isinstance(data, dict):
                return [data]

        return []

    @property
    def version(self) -> str:
        return "iFinD"

