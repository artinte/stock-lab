from __future__ import annotations

from typing import Any


class StockFinancialService:
    """
    股票财务数据服务。

    负责：
    1. 调用 DataManager 获取三大财务报表
    2. 将模型转换为前端需要的 JSON 数据
    3. 计算基础财务指标
    4. 保持 API 层简单
    """

    def __init__(self, manager):
        self.manager = manager

    def get_financial_data(self, symbol: str) -> dict[str, Any]:
        """
        获取股票完整财务数据。
        """

        income_statements = self.manager.get_income_statement(symbol=symbol)

        balance_sheets = self.manager.get_balance_sheet(symbol=symbol)

        cash_flows = self.manager.get_cash_flow(symbol=symbol)

        income_statements = self._sort_reports(income_statements)
        balance_sheets = self._sort_reports(balance_sheets)
        cash_flows = self._sort_reports(cash_flows)

        trend = self._build_trend(
            income_statements,
            balance_sheets,
            cash_flows,
        )

        summary = self._build_summary(
            income_statements,
            balance_sheets,
            cash_flows,
        )

        profitability = self._build_profitability(
            income_statements,
            balance_sheets,
        )

        return {
            "symbol": symbol,
            "summary": summary,
            "trend": trend,
            "profitability": profitability,
            "income_statement": [
                self._income_to_dict(item) for item in income_statements
            ],
            "balance_sheet": [self._balance_to_dict(item) for item in balance_sheets],
            "cash_flow": [self._cash_flow_to_dict(item) for item in cash_flows],
        }

    # =========================================================
    # Summary
    # =========================================================

    def _build_summary(
        self,
        incomes,
        balances,
        cash_flows,
    ) -> dict[str, Any]:

        income = self._latest(incomes)
        balance = self._latest(balances)
        cash_flow = self._latest(cash_flows)

        revenue = self._number(getattr(income, "revenue", None))

        profit = self._number(getattr(income, "net_profit_attributable", None))

        operating_cash_flow = self._number(
            getattr(cash_flow, "operating_cash_flow", None)
        )

        net_assets = self._number(getattr(balance, "shareholders_equity", None))

        if net_assets is None:
            net_assets = self._number(getattr(balance, "total_equity", None))

        gross_profit = self._number(getattr(income, "gross_profit", None))

        net_margin = None

        if revenue not in (None, 0) and profit is not None:
            net_margin = profit / revenue * 100

        gross_margin = None

        if revenue not in (None, 0) and gross_profit is not None:
            gross_margin = gross_profit / revenue * 100

        return {
            "report_date": self._report_date(income),
            "revenue": revenue,
            "revenue_growth": None,
            "net_profit": profit,
            "net_profit_growth": None,
            "operating_cash_flow": operating_cash_flow,
            "net_assets": net_assets,
            "gross_margin": gross_margin,
            "net_margin": net_margin,
        }

    # =========================================================
    # Trend
    # =========================================================

    def _build_trend(
        self,
        incomes,
        balances,
        cash_flows,
    ) -> list[dict[str, Any]]:

        income_map = {
            self._report_date(item): item for item in incomes if self._report_date(item)
        }

        balance_map = {
            self._report_date(item): item
            for item in balances
            if self._report_date(item)
        }

        cash_map = {
            self._report_date(item): item
            for item in cash_flows
            if self._report_date(item)
        }

        dates = sorted(set(income_map) | set(balance_map) | set(cash_map))

        result = []

        for date in dates:

            income = income_map.get(date)
            balance = balance_map.get(date)
            cash_flow = cash_map.get(date)

            revenue = self._number(getattr(income, "revenue", None))

            profit = self._number(getattr(income, "net_profit_attributable", None))

            gross_profit = self._number(getattr(income, "gross_profit", None))

            operating_profit = self._number(getattr(income, "operating_profit", None))

            operating_cash_flow = self._number(
                getattr(cash_flow, "operating_cash_flow", None)
            )

            net_assets = self._number(getattr(balance, "shareholders_equity", None))

            if net_assets is None:
                net_assets = self._number(getattr(balance, "total_equity", None))

            total_assets = self._number(getattr(balance, "total_assets", None))

            total_liabilities = self._number(
                getattr(balance, "total_liabilities", None)
            )

            gross_margin = None

            if revenue not in (None, 0) and gross_profit is not None:
                gross_margin = gross_profit / revenue * 100

            net_margin = None

            if revenue not in (None, 0) and profit is not None:
                net_margin = profit / revenue * 100

            operating_margin = None

            if revenue not in (None, 0) and operating_profit is not None:
                operating_margin = operating_profit / revenue * 100

            debt_ratio = None

            if total_assets not in (None, 0):
                if total_liabilities is not None:
                    debt_ratio = total_liabilities / total_assets * 100

            result.append(
                {
                    "report_date": date,
                    "period": self._format_period(date),
                    "revenue": revenue,
                    "profit": profit,
                    "operating_cash_flow": operating_cash_flow,
                    "net_assets": net_assets,
                    "gross_margin": gross_margin,
                    "net_margin": net_margin,
                    "operating_margin": operating_margin,
                    "debt_ratio": debt_ratio,
                    "roe": None,
                }
            )

        return result

    # =========================================================
    # Profitability
    # =========================================================

    def _build_profitability(
        self,
        incomes,
        balances,
    ) -> list[dict[str, Any]]:

        income_map = {
            self._report_date(item): item for item in incomes if self._report_date(item)
        }

        balance_map = {
            self._report_date(item): item
            for item in balances
            if self._report_date(item)
        }

        dates = sorted(set(income_map) | set(balance_map))

        result = []

        for date in dates:

            income = income_map.get(date)
            balance = balance_map.get(date)

            revenue = self._number(getattr(income, "revenue", None))

            profit = self._number(getattr(income, "net_profit_attributable", None))

            gross_profit = self._number(getattr(income, "gross_profit", None))

            operating_profit = self._number(getattr(income, "operating_profit", None))

            equity = self._number(getattr(balance, "shareholders_equity", None))

            if equity is None:
                equity = self._number(getattr(balance, "total_equity", None))

            assets = self._number(getattr(balance, "total_assets", None))

            gross_margin = None

            if revenue not in (None, 0) and gross_profit is not None:
                gross_margin = gross_profit / revenue * 100

            net_margin = None

            if revenue not in (None, 0) and profit is not None:
                net_margin = profit / revenue * 100

            operating_margin = None

            if revenue not in (None, 0) and operating_profit is not None:
                operating_margin = operating_profit / revenue * 100

            roe = None

            if equity not in (None, 0) and profit is not None:
                roe = profit / equity * 100

            roa = None

            if assets not in (None, 0) and profit is not None:
                roa = profit / assets * 100

            result.append(
                {
                    "report_date": date,
                    "period": self._format_period(date),
                    "gross_margin": gross_margin,
                    "operating_margin": operating_margin,
                    "net_margin": net_margin,
                    "roe": roe,
                    "roa": roa,
                }
            )

        return result

    # =========================================================
    # Model → JSON
    # =========================================================

    def _income_to_dict(self, item) -> dict[str, Any]:

        return {
            "report_date": self._report_date(item),
            "period": self._format_period(self._report_date(item)),
            "report_type": getattr(
                item,
                "report_type",
                None,
            ),
            "statement_type": getattr(
                item,
                "statement_type",
                None,
            ),
            "revenue": self._number(getattr(item, "revenue", None)),
            "operating_cost": self._number(getattr(item, "operating_cost", None)),
            "gross_profit": self._number(getattr(item, "gross_profit", None)),
            "operating_profit": self._number(getattr(item, "operating_profit", None)),
            "total_profit": self._number(getattr(item, "total_profit", None)),
            "income_tax": self._number(getattr(item, "income_tax", None)),
            "net_profit": self._number(getattr(item, "net_profit", None)),
            "net_profit_attributable": self._number(
                getattr(
                    item,
                    "net_profit_attributable",
                    None,
                )
            ),
            "non_recurring_net_profit": self._number(
                getattr(
                    item,
                    "non_recurring_net_profit",
                    None,
                )
            ),
            "ebit": self._number(getattr(item, "ebit", None)),
            "ebitda": self._number(getattr(item, "ebitda", None)),
            "eps": self._number(getattr(item, "eps", None)),
            "diluted_eps": self._number(getattr(item, "diluted_eps", None)),
        }

    def _balance_to_dict(self, item) -> dict[str, Any]:

        return {
            "report_date": self._report_date(item),
            "period": self._format_period(self._report_date(item)),
            "report_type": getattr(
                item,
                "report_type",
                None,
            ),
            "statement_type": getattr(
                item,
                "statement_type",
                None,
            ),
            "total_assets": self._number(getattr(item, "total_assets", None)),
            "current_assets": self._number(getattr(item, "current_assets", None)),
            "cash": self._number(getattr(item, "cash", None)),
            "accounts_receivable": self._number(
                getattr(item, "accounts_receivable", None)
            ),
            "inventory": self._number(getattr(item, "inventory", None)),
            "fixed_assets": self._number(getattr(item, "fixed_assets", None)),
            "intangible_assets": self._number(getattr(item, "intangible_assets", None)),
            "total_liabilities": self._number(getattr(item, "total_liabilities", None)),
            "current_liabilities": self._number(
                getattr(item, "current_liabilities", None)
            ),
            "short_term_debt": self._number(getattr(item, "short_term_debt", None)),
            "long_term_debt": self._number(getattr(item, "long_term_debt", None)),
            "accounts_payable": self._number(getattr(item, "accounts_payable", None)),
            "total_equity": self._number(getattr(item, "total_equity", None)),
            "shareholders_equity": self._number(
                getattr(item, "shareholders_equity", None)
            ),
            "minority_interest": self._number(getattr(item, "minority_interest", None)),
            "share_capital": self._number(getattr(item, "share_capital", None)),
            "undistributed_profit": self._number(
                getattr(item, "undistributed_profit", None)
            ),
        }

    def _cash_flow_to_dict(self, item) -> dict[str, Any]:

        return {
            "report_date": self._report_date(item),
            "period": self._format_period(self._report_date(item)),
            "report_type": getattr(
                item,
                "report_type",
                None,
            ),
            "statement_type": getattr(
                item,
                "statement_type",
                None,
            ),
            "operating_cash_flow": self._number(
                getattr(item, "operating_cash_flow", None)
            ),
            "operating_cash_inflow": self._number(
                getattr(item, "operating_cash_inflow", None)
            ),
            "operating_cash_outflow": self._number(
                getattr(item, "operating_cash_outflow", None)
            ),
            "investing_cash_flow": self._number(
                getattr(item, "investing_cash_flow", None)
            ),
            "investing_cash_inflow": self._number(
                getattr(item, "investing_cash_inflow", None)
            ),
            "investing_cash_outflow": self._number(
                getattr(item, "investing_cash_outflow", None)
            ),
            "capital_expenditure": self._number(
                getattr(item, "capital_expenditure", None)
            ),
            "financing_cash_flow": self._number(
                getattr(item, "financing_cash_flow", None)
            ),
            "financing_cash_inflow": self._number(
                getattr(item, "financing_cash_inflow", None)
            ),
            "financing_cash_outflow": self._number(
                getattr(item, "financing_cash_outflow", None)
            ),
            "beginning_cash_balance": self._number(
                getattr(item, "beginning_cash_balance", None)
            ),
            "ending_cash_balance": self._number(
                getattr(item, "ending_cash_balance", None)
            ),
            "net_change_in_cash": self._number(
                getattr(item, "net_change_in_cash", None)
            ),
            "free_cash_flow": self._number(getattr(item, "free_cash_flow", None)),
            "fcff": self._number(getattr(item, "fcff", None)),
            "fcfe": self._number(getattr(item, "fcfe", None)),
        }

    # =========================================================
    # Helpers
    # =========================================================

    @staticmethod
    def _latest(items):

        if not items:
            return None

        return max(
            items,
            key=lambda item: (getattr(item, "report_date", "") or ""),
        )

    @staticmethod
    def _sort_reports(items):

        return sorted(
            items or [],
            key=lambda item: (getattr(item, "report_date", "") or ""),
            reverse=True,
        )

    @staticmethod
    def _report_date(item):

        if item is None:
            return None

        value = getattr(
            item,
            "report_date",
            None,
        )

        if value is None:
            return None

        return str(value)

    @staticmethod
    def _number(value):

        if value is None:
            return None

        try:
            value = float(value)

            if value != value:
                return None

            return value

        except (TypeError, ValueError):
            return None

    @staticmethod
    def _format_period(report_date):

        if not report_date:
            return "-"

        value = str(report_date)

        if len(value) != 8:
            return value

        year = value[:4]
        month = value[4:6]

        quarter_map = {
            "03": "Q1",
            "06": "Q2",
            "09": "Q3",
            "12": "Q4",
        }

        quarter = quarter_map.get(month)

        if quarter:
            return f"{year} {quarter}"

        return value
