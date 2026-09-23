from __future__ import annotations

from datetime import date
from typing import Optional

from common.enums.quote_level import QuoteLevel

from core.models.equity_structure import EquityStructure
from core.models.financial.income_statement import IncomeStatement
from core.models.financial.financial import Financial
from core.models.valuation import Valuation
from core.models.stock import Stock
from core.models.quote import Quote
from core.models.financial.balance_sheet import BalanceSheet
from core.models.financial.cash_flow import CashFlow

from infra.gateways.stock_data import StockDataGateway


class StockManager:
    """
    股票数据管理器。

    负责股票相关的数据访问，包括：

    - 股票基础信息
    - 实时行情
    - K 线
    - 利润表
    - 资产负债表
    - 现金流量表
    - 综合财务
    - 估值
    - ETF 成分及申赎信息
    """

    def __init__(
        self,
        gateway: StockDataGateway,
    ) -> None:
        self.gateway = gateway

    # --------------------------------------------------
    # 股票基础信息
    # --------------------------------------------------

    def get_stock(
        self,
        symbol: str,
    ) -> Stock:
        """获取股票基础信息。"""

        return self.gateway.fetch_stock(symbol)

    def get_stocks(
        self,
        symbols: list[str],
    ) -> list[Stock]:
        """批量获取股票基础信息。"""

        return self.gateway.fetch_stocks(symbols)

    def get_equity_structure(
        self,
        symbol: str,
    ) -> EquityStructure | None:
        """获取单只股票的股本结构。"""

        return self.gateway.fetch_equity_structure(symbol)

    def get_equity_structures(
        self,
        symbols: list[str],
    ) -> list[EquityStructure]:
        """批量获取股票股本结构。"""

        return self.gateway.fetch_equity_structures(symbols)

    # --------------------------------------------------
    # 股票行情
    # --------------------------------------------------

    def get_quote(
        self,
        symbol: str,
        level: QuoteLevel = QuoteLevel.LEVEL_1,
    ) -> Quote:
        """获取股票实时行情。"""

        return self.gateway.fetch_quote(
            symbol,
            level,
        )

    def get_quotes(
        self,
        symbols: list[str],
        level: QuoteLevel = QuoteLevel.LEVEL_1,
    ):
        """批量获取股票实时行情。"""

        return self.gateway.fetch_quotes(
            symbols,
            level,
        )

    # --------------------------------------------------
    # 股票 K 线
    # --------------------------------------------------

    def get_kline(
        self,
        symbol: str,
        interval,
        start_time=None,
        end_time=None,
        limit: int = 1000,
    ):
        """获取股票 K 线。"""

        return self.gateway.fetch_kline(
            symbol=symbol,
            interval=interval,
            start_time=start_time,
            end_time=end_time,
            limit=limit,
        )

    def get_klines(
        self,
        symbols: list[str],
        interval,
        start_time=None,
        end_time=None,
        limit: int = 1000,
    ):
        """批量获取股票 K 线。"""

        return self.gateway.fetch_klines(
            symbols=symbols,
            interval=interval,
            start_time=start_time,
            end_time=end_time,
            limit=limit,
        )

    # --------------------------------------------------
    # 财务数据
    # --------------------------------------------------

    def get_income_statement(
        self,
        symbol: str,
        start_year: Optional[int] = None,
        start_quarter: Optional[int] = None,
        end_year: Optional[int] = None,
        end_quarter: Optional[int] = None,
    ) -> list[IncomeStatement]:
        """获取利润表。"""

        return self.gateway.fetch_income_statement(
            symbol,
            start_year,
            start_quarter,
            end_year,
            end_quarter,
        )

    def get_balance_sheet(
        self,
        symbol: str,
        start_year: Optional[int] = None,
        start_quarter: Optional[int] = None,
        end_year: Optional[int] = None,
        end_quarter: Optional[int] = None,
    ) -> list[BalanceSheet]:
        """获取资产负债表。"""

        return self.gateway.fetch_balance_sheet(
            symbol,
            start_year,
            start_quarter,
            end_year,
            end_quarter,
        )

    def get_cash_flow(
        self,
        symbol: str,
        start_year: Optional[int] = None,
        start_quarter: Optional[int] = None,
        end_year: Optional[int] = None,
        end_quarter: Optional[int] = None,
    ) -> list[CashFlow]:
        """获取现金流量表。"""

        return self.gateway.fetch_cash_flow(
            symbol,
            start_year,
            start_quarter,
            end_year,
            end_quarter,
        )

    def get_financial(
        self,
        symbol: str,
        start_year: Optional[int] = None,
        start_quarter: Optional[int] = None,
        end_year: Optional[int] = None,
        end_quarter: Optional[int] = None,
    ) -> list[Financial]:
        """获取综合财务数据。"""

        return self.gateway.fetch_financial(
            symbol,
            start_year,
            start_quarter,
            end_year,
            end_quarter,
        )

    # --------------------------------------------------
    # 估值
    # --------------------------------------------------

    def get_valuation(
        self,
        symbol: str,
    ) -> Valuation:
        """获取股票估值数据。"""

        return self.gateway.fetch_valuation(symbol)

    # --------------------------------------------------
    # ETF
    # --------------------------------------------------

    def get_etf_composition(
        self,
        symbol: str,
        trade_date: date | None = None,
    ):
        """获取 ETF 成分及申赎信息。"""

        return self.gateway.fetch_etf_composition(
            symbol,
            trade_date,
        )
