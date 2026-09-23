from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional

from polars import date

from common.constants import Interval
from common.enums.quote_level import QuoteLevel
from core.models.equity_structure import EquityStructure
from core.models.financial.balance_sheet import BalanceSheet
from core.models.financial.cash_flow import CashFlow
from core.models.financial.financial import Financial
from core.models.financial.income_statement import IncomeStatement
from core.models.kline import Kline
from core.models.quote import Quote
from core.models.stock import Stock


class StockDataGateway(ABC):
    """
    股票数据源统一抽象接口。

    所有数据源必须实现这一接口。
    """

    name: str = ""

    display_name: str = ""

    def __init__(
        self,
        config: Optional[dict] = None,
    ) -> None:
        self.config = config or {}
        self._started = False

    @abstractmethod
    def login(
        self,
        config: Optional[dict] = None,
    ) -> bool:
        raise NotImplementedError

    @abstractmethod
    def logout(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def health_check(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def fetch_stock(
        self,
        symbol: str,
    ) -> Stock:
        raise NotImplementedError

    @abstractmethod
    def fetch_stocks(
        self,
        symbols: list[str],
    ) -> list[Stock]:
        raise NotImplementedError

    @abstractmethod
    def fetch_kline(
        self,
        symbol: str,
        interval: Interval = Interval.DAY_1,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 1000,
    ) -> Kline:
        raise NotImplementedError

    @abstractmethod
    def fetch_equity_structure(
        symbol: str,
    ) -> EquityStructure | None:
        raise NotImplementedError

    @abstractmethod
    def fetch_equity_structures(
        symbols: list[str],
    ) -> list[EquityStructure]:
        raise NotImplementedError

    @abstractmethod
    def fetch_quote(
        self,
        symbol: str,
        level: Optional[QuoteLevel] = None,
    ) -> Quote:
        raise NotImplementedError

    @abstractmethod
    def fetch_quotes(
        self,
        symbols: list[str],
        level: Optional[QuoteLevel] = None,
    ):
        raise NotImplementedError

    def fetch_etf_composition(
        self,
        symbol: str,
        trade_date: date | None = None,
    ):
        return self.gateway.fetch_etf_composition(symbol, trade_date)

    @abstractmethod
    def fetch_balance_sheet(
        self,
        symbol: str,
        start_year: Optional[int] = None,
        start_quarter: Optional[int] = None,
        end_year: Optional[int] = None,
        end_quarter: Optional[int] = None,
    ) -> list[BalanceSheet]:
        raise NotImplementedError

    @abstractmethod
    def fetch_cash_flow(
        self,
        symbol: str,
    ) -> CashFlow:
        """
        由具体数据源实现利润表数据获取。
        """
        raise NotImplementedError

    @abstractmethod
    def fetch_income_statement(
        self,
        symbol: str,
        start_year: Optional[int],
        start_quarter: Optional[int],
        end_year: Optional[int],
        end_quarter: Optional[int],
    ) -> list[IncomeStatement]:
        """
        由具体数据源实现利润表数据获取。

        该方法由 fetch_income_statement() 调用。
        参数已经经过报告期合法性校验。

        不同数据源只需要负责：

            1. 调用数据源接口。
            2. 获取原始利润表数据。
            3. 根据报告期筛选数据。
            4. 转换为统一的 IncomeStatement 模型。
        """
        raise NotImplementedError

    @staticmethod
    def _validate_report_period(
        start_year: Optional[int],
        start_quarter: Optional[int],
        end_year: Optional[int],
        end_quarter: Optional[int],
    ) -> None:
        """
        校验报告期查询范围。

        要求：
            1. start_year 和 start_quarter 必须同时指定。
            2. end_year 和 end_quarter 必须同时指定。
            3. quarter 必须为 1~4。
            4. year 必须为有效的四位年份。
            5. start_report_period <= end_report_period。

        查询范围为闭区间：
            [start_report_period, end_report_period]

        例如：
            start_year=2024, start_quarter=3
            end_year=2025, end_quarter=2

        表示：
            2024Q3 <= report_period <= 2025Q2
        """

        # ==========================================================
        # 检查年份类型
        # ==========================================================

        if start_year is not None:
            if not isinstance(start_year, int):
                raise TypeError(
                    f"start_year 必须是 int，" f"实际类型为 {type(start_year).__name__}"
                )

        if end_year is not None:
            if not isinstance(end_year, int):
                raise TypeError(
                    f"end_year 必须是 int，" f"实际类型为 {type(end_year).__name__}"
                )

        # ==========================================================
        # 检查季度类型
        # ==========================================================

        if start_quarter is not None:
            if not isinstance(start_quarter, int):
                raise TypeError(
                    f"start_quarter 必须是 int，"
                    f"实际类型为 {type(start_quarter).__name__}"
                )

        if end_quarter is not None:
            if not isinstance(end_quarter, int):
                raise TypeError(
                    f"end_quarter 必须是 int，"
                    f"实际类型为 {type(end_quarter).__name__}"
                )

        # ==========================================================
        # 起始报告期必须成对出现
        # ==========================================================

        if start_year is None and start_quarter is not None:
            raise ValueError("start_quarter 已指定，但 start_year 未指定")

        if start_year is not None and start_quarter is None:
            raise ValueError("start_year 已指定，但 start_quarter 未指定")

        # ==========================================================
        # 结束报告期必须成对出现
        # ==========================================================

        if end_year is None and end_quarter is not None:
            raise ValueError("end_quarter 已指定，但 end_year 未指定")

        if end_year is not None and end_quarter is None:
            raise ValueError("end_year 已指定，但 end_quarter 未指定")

        # ==========================================================
        # 检查季度范围
        # ==========================================================

        if start_quarter is not None:
            if start_quarter < 1 or start_quarter > 4:
                raise ValueError(
                    f"start_quarter 必须是 1~4，" f"实际为 {start_quarter}"
                )

        if end_quarter is not None:
            if end_quarter < 1 or end_quarter > 4:
                raise ValueError(f"end_quarter 必须是 1~4，" f"实际为 {end_quarter}")

        # ==========================================================
        # 检查年份范围
        # ==========================================================

        if start_year is not None:
            if start_year < 1900 or start_year > 9999:
                raise ValueError(f"start_year 必须是有效年份，" f"实际为 {start_year}")

        if end_year is not None:
            if end_year < 1900 or end_year > 9999:
                raise ValueError(f"end_year 必须是有效年份，" f"实际为 {end_year}")

        # ==========================================================
        # 检查起始报告期 <= 结束报告期
        #
        # 将：
        #
        #     2025Q1
        #
        # 转换成连续的季度序号：
        #
        #     2025 * 4 + (1 - 1)
        #
        # 这样可以直接比较跨年度季度。
        # ==========================================================

        if (
            start_year is not None
            and start_quarter is not None
            and end_year is not None
            and end_quarter is not None
        ):
            start_period = start_year * 4 + start_quarter - 1

            end_period = end_year * 4 + end_quarter - 1

            if start_period > end_period:
                raise ValueError(
                    "起始报告期不能晚于结束报告期："
                    f"{start_year}Q{start_quarter} > "
                    f"{end_year}Q{end_quarter}"
                )

    @abstractmethod
    def fetch_financial(
        self,
        symbol: str,
        start_year,
        start_quarter,
        end_year,
        end_quarter,
    ) -> Financial:
        raise NotImplementedError

    @abstractmethod
    def fetch_valuation(
        self,
        symbol: str,
    ):
        raise NotImplementedError

    def is_started(self) -> bool:
        return self._started

    def __enter__(self):
        self.login()
        return self

    def __exit__(
        self,
        exc_type,
        exc_value,
        traceback,
    ):
        self.logout()

    @property
    def version(self) -> str:
        return "unknown"
