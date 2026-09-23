from __future__ import annotations

import datetime
from typing import Optional

import pandas

from core.models.financial.balance_sheet import BalanceSheet
from core.models.financial.cash_flow import CashFlow
from core.models.financial.income_statement import IncomeStatement
from core.models.quote import Quote
from infra.analysis.valuation_analyzer import ValuationAnalyzer
from common.constants import Interval, TEN_THOUSAND
from core.models.valuation import Valuation
from utils.stock_mapping import normalize_symbol


class YinheValuation:
    """
    银河证券估值模块。

    负责：

        - 获取估值所需基础数据
        - 将银河原始数据转换为项目统一字段
        - 调用 ValuationAnalyzer
        - 组装 Valuation

    不负责：

        - PE 计算
        - PB 计算
        - PS 计算
        - PEG 计算
        - EV 计算
        - 股息率计算

    所有估值计算统一由 ValuationAnalyzer 完成。
    """

    def __init__(
        self,
        gateway,
    ) -> None:
        self.gateway = gateway
        self.analyzer = ValuationAnalyzer()

    # ==========================================================
    # Public API
    # ==========================================================

    def fetch_valuation(
        self,
        symbol: str,
    ) -> Valuation | None:
        """
        获取股票估值数据。

        数据获取与估值计算分离：

        Gateway:
            负责获取 Quote / IncomeStatement /
            BalanceSheet / CashFlow

        ValuationAnalyzer:
            负责根据原始数据计算 PE / PB / PS /
            PEG / EV / EBITDA 等估值指标。
        """

        self.gateway._ensure_started()

        symbol = normalize_symbol(symbol)

        print(f"[{symbol}] 正在获取估值数据...")

        try:
            # ==================================================
            # 1. 获取当前行情
            # ==================================================

            quote: Quote | None = self.gateway.fetch_quote(
                symbol=symbol,
            )

            if quote is None:
                print(
                    f"[银河估值] 未获取到行情数据: "
                    f"{symbol}"
                )
                return None

            # ==================================================
            # 2. 获取利润表
            #
            # 用于：
            # - PE
            # - PE TTM
            # - PEG
            # - PS
            # - EV / EBITDA
            # ==================================================

            income_statements: list[IncomeStatement] = (
                self.gateway.fetch_income_statement(
                    symbol=symbol,
                )
            )

            # ==================================================
            # 3. 获取资产负债表
            #
            # 用于：
            # - PB
            # - 每股净资产
            # - Enterprise Value
            # ==================================================

            balance_sheets: list[BalanceSheet] = (
                self.gateway.fetch_balance_sheet(
                    symbol=symbol,
                )
            )

            # ==================================================
            # 4. 获取现金流量表
            #
            # 当前估值指标暂时不依赖现金流量表，
            # 但保留传入，为后续：
            # - FCF
            # - FCFF
            # - FCFE
            # - DCF
            # 做准备。
            # ==================================================

            cash_flows: list[CashFlow] = (
                self.gateway.fetch_cash_flow(
                    symbol=symbol,
                )
            )

            # ==================================================
            # 5. 使用 ValuationAnalyzer 计算估值
            #
            # Analyzer 只接收统一模型，
            # 不接触 DataFrame / 数据源 API。
            # ==================================================

            valuation = self.analyzer.analyze(
                quote=quote,
                income_statements=income_statements,
                balance_sheets=balance_sheets,
                cash_flows=cash_flows,
            )

            if valuation is None:
                print(
                    f"[银河估值] 估值计算失败: "
                    f"{symbol}"
                )
                return None

            # ==================================================
            # 6. 补充数据源信息
            # ==================================================

            valuation.timestamp = datetime.datetime.now()
            valuation.source = self.gateway.display_name

            return valuation

        except Exception as exc:
            print(
                f"[银河估值] 获取估值失败 "
                f"{symbol}: {exc}"
            )

            return None

    # ==========================================================
    # Price
    # ==========================================================

    def _get_current_price(
        self,
        symbol: str,
    ) -> Optional[float]:
        """
        使用最近交易日 K 线收盘价作为当前价格。
        """

        klines = self.gateway.fetch_kline(
            symbol=symbol,
            interval=Interval.DAY_1,
            start_time=(
                datetime.datetime.now()
                - datetime.timedelta(days=30)
            ),
            end_time=datetime.datetime.now(),
            limit=30,
        )

        if not klines:
            return None

        return klines[-1].close

    # ==========================================================
    # Equity Structure
    # ==========================================================

    def _get_equity_structure(
        self,
        symbol: str,
    ) -> tuple[
        Optional[float],
        Optional[float],
        Optional[str],
    ]:
        """
        获取总股本和流通股本。

        银河原始单位：

            万股

        标准模型：

            股
        """

        total_shares = None
        float_shares = None
        report_date = None

        try:
            equity_structure = (
                self.gateway.info_data.get_equity_structure(
                    [symbol],
                    local_path=self.gateway.local_path,
                    is_local=True,
                )
            )

            if (
                equity_structure is None
                or equity_structure.empty
            ):
                return None, None, None

            if "CHANGE_DATE" in equity_structure.columns:
                equity_structure = (
                    equity_structure.sort_values(
                        "CHANGE_DATE"
                    )
                )

            row = equity_structure.iloc[-1]

            # --------------------------------------------------
            # 总股本
            # --------------------------------------------------

            value = row.get("TOT_SHARE")

            if pandas.notna(value):
                total_shares = (
                    float(value)
                    * TEN_THOUSAND
                )

            # --------------------------------------------------
            # 流通A股(万股) 
            # --------------------------------------------------

            value = row.get("FLOAT_A_SHARE")
            if pandas.notna(value):
                float_shares = (
                    float(value)
                    * TEN_THOUSAND
                )

            # --------------------------------------------------
            # 股本变更日期
            # --------------------------------------------------

            value = row.get("CHANGE_DATE")

            if pandas.notna(value):
                report_date = str(value)

        except Exception as exc:
            print(
                f"[银河估值] 获取股本失败 "
                f"{symbol}: {exc}"
            )

        return (
            total_shares,
            float_shares,
            report_date,
        )

    # ==========================================================
    # Financial Base
    # ==========================================================

    def _get_financial_base(
        self,
        symbol: str,
    ) -> dict:
        """
        获取估值所需基础数据。

        这里负责：

            银河财务数据
                ↓
            项目统一基础数据

        不负责估值计算。
        """

        result = {
            "net_profit": None,
            "net_profit_ttm": None,
            "net_profit_forecast": None,

            "revenue": None,
            "revenue_ttm": None,

            "total_equity": None,
            "book_value_per_share": None,

            "cash": None,
            "debt": None,
            "ebitda": None,

            "dividend": None,

            "profit_growth": None,

            "report_date": None,
        }

        # ======================================================
        # 获取完整财务数据
        # ======================================================

        financial = self.gateway.fetch_financial(
            symbol
        )

        if financial is None:
            return result

        result["report_date"] = (
            financial.report_date
        )

        # ======================================================
        # 利润表
        # ======================================================

        income = financial.income

        if income is not None:

            # --------------------------------------------------
            # 归母净利润优先
            # --------------------------------------------------

            result["net_profit"] = (
                income.net_profit_attributable
                if income.net_profit_attributable
                is not None
                else income.net_profit
            )

            result["revenue"] = income.revenue

            result["ebitda"] = income.ebitda

        # ======================================================
        # 资产负债表
        # ======================================================

        balance = financial.balance

        if balance is not None:

            result["total_equity"] = (
                balance.shareholders_equity
            )

            result["cash"] = balance.cash

            # --------------------------------------------------
            # 有息债务
            # --------------------------------------------------

            debt = 0.0
            has_debt = False

            for value in (
                balance.short_term_debt,
                balance.long_term_debt,
                balance.bonds_payable,
            ):
                if value is not None:
                    debt += value
                    has_debt = True

            if has_debt:
                result["debt"] = debt

            # --------------------------------------------------
            # 每股净资产
            # 后面再用股本计算
            # --------------------------------------------------

        # ======================================================
        # 财务指标
        # ======================================================

        indicators = financial.indicators

        if indicators is not None:

            if hasattr(
                indicators,
                "net_profit_yoy",
            ):
                result["profit_growth"] = (
                    indicators.net_profit_yoy
                )

        return result