from typing import Any

import pandas

from core.models.financial.financial import Financial
from core.models.financial.income_statement import IncomeStatement
from core.models.financial.balance_sheet import BalanceSheet
from core.models.financial.cash_flow import CashFlow
from infra.analysis.financial_analyzer import FinancialAnalyzer
from utils.stock_mapping import normalize_symbol


class YinheFinancial:
    """
    银河证券财务数据适配。
    """

    def __init__(self, gateway):
        """
        保存主网关引用。

        可以访问：

            gateway.info_data
            gateway.calendar
            gateway.local_path

        """

        self.gateway = gateway

        self.financial_analyzer = FinancialAnalyzer()

    def fetch_balance_sheet(
        self,
        symbol: str,
        start_year: int | None = None,
        start_quarter: int | None = None,
        end_year: int | None = None,
        end_quarter: int | None = None,
    ) -> list[BalanceSheet]:
        return self.fetch_balance_sheets(
            [symbol],
            start_year,
            start_quarter,
            end_year,
            end_quarter,
        ).get(symbol, [])

    def fetch_cash_flow(
        self,
        symbol: str,
        start_year: int | None = None,
        start_quarter: int | None = None,
        end_year: int | None = None,
        end_quarter: int | None = None,
    ) -> list[CashFlow]:
        return self.fetch_cash_flows(
            [symbol],
            start_year,
            start_quarter,
            end_year,
            end_quarter,
        ).get(symbol, [])

    def fetch_income_statement(
        self,
        symbol: str,
        start_year: int | None = None,
        start_quarter: int | None = None,
        end_year: int | None = None,
        end_quarter: int | None = None,
    ) -> list[IncomeStatement]:
        """
        获取银河利润表数据。

        将银河证券返回的利润表 DataFrame
        转换为统一 IncomeStatement 模型。

        数据流：
            AmazingData
                |
                ↓
            DataFrame
                |
                ↓
            IncomeStatement
        参数：
            symbols: 股票代码列表
            start_year: 起始报告年度
            start_quarter: 起始报告季度
            end_year: 结束报告年度
            end_quarter: 结束报告季度
        返回：
            符合查询条件的利润表数据列表。
            如果没有匹配数据，则返回空列表。
        """
        return self.fetch_income_statements(
            [symbol],
            start_year,
            start_quarter,
            end_year,
            end_quarter,
        ).get(symbol, [])

    def fetch_balance_sheets(
        self,
        symbols: list[str],
        start_year: int | None = None,
        start_quarter: int | None = None,
        end_year: int | None = None,
        end_quarter: int | None = None,
    ) -> dict[str, list[BalanceSheet]]:
        balance_sheets: dict[str, list[BalanceSheet]] = {}
        try:
            # ======================================================
            # 获取银河指定股票列表的上市公司的资产负债表数据
            # 本地保存全量历史数据，且每次调用接口默认增量更新本地数据，从而加速接口读取速度
            # ======================================================
            result = self.gateway.info_data.get_balance_sheet(
                symbols,
                local_path=self.gateway.local_path,
                is_local=True,
            )

            if not result:
                print(f"[银河] 未获取到资产负债表数据: {symbols}")
                return {}

            for symbol in symbols:
                # ======================================================
                # 获取当前股票 DataFrame
                # ======================================================
                df = result.get(symbol)

                if df is None:
                    print(f"[银河] 未找到股票资产负债表: {symbol}")
                    continue

                if df.empty:
                    print(f"[银河] 资产负债表为空: {symbol}")
                    continue

                if "REPORTING_PERIOD" not in df.columns:
                    print(f"[银河] 资产负债表缺少 REPORTING_PERIOD: " f"{symbol}")
                    continue

                # ======================================================
                # 根据报告期筛选
                # ======================================================

                selected_rows = []
                for _, row in df.iterrows():
                    statement_type = row.get("STATEMENT_TYPE")
                    # --------------------------------------------------
                    # 只使用合并报表
                    # --------------------------------------------------
                    if statement_type != "1":
                        continue
                    report_date = str(row.get("REPORTING_PERIOD"))

                    if not report_date:
                        continue
                    report_year, report_quarter = self._parse_report_period(report_date)

                    # --------------------------------------------------
                    # 起始报告期
                    # --------------------------------------------------
                    if start_year is not None:
                        if self._quarter_index(
                            report_year,
                            report_quarter,
                        ) < self._quarter_index(
                            start_year,
                            start_quarter,
                        ):
                            continue

                    # --------------------------------------------------
                    # 结束报告期
                    # --------------------------------------------------
                    if end_year is not None:
                        if self._quarter_index(
                            report_year,
                            report_quarter,
                        ) > self._quarter_index(
                            end_year,
                            end_quarter,
                        ):
                            continue

                    selected_rows.append(row)
                if not selected_rows:
                    continue

                # ======================================================
                # 转换为标准 BalanceSheet
                # ======================================================
                symbol_balance_sheets: list[BalanceSheet] = []
                for row in selected_rows:
                    symbol_balance_sheets.append(
                        BalanceSheet(
                            # ==================================================
                            # 基础信息
                            # ==================================================
                            symbol=symbol,
                            report_date=self._to_str(row.get("REPORTING_PERIOD")),
                            report_type=self._to_str(row.get("REPORT_TYPE")),
                            statement_type=self._to_str(row.get("STATEMENT_TYPE")),
                            announcement_date=self._to_str(row.get("ANN_DATE")),
                            currency=self._to_str(row.get("CURRENCY_CODE")),
                            # ==================================================
                            # 资产
                            # ==================================================
                            total_assets=self._to_float(row.get("TOTAL_ASSETS")),
                            current_assets=self._to_float(row.get("TOTAL_CUR_ASSETS")),
                            non_current_assets=self._to_float(
                                row.get("TOT_NONCUR_ASSETS")
                            ),
                            cash=self._to_float(row.get("CURRENCY_CAP")),
                            accounts_receivable=self._to_float(
                                row.get("ACCT_RECEIVABLE")
                            ),
                            inventory=self._to_float(row.get("INV")),
                            fixed_assets=self._to_float(row.get("FIXED_ASSETS")),
                            construction_in_progress=self._to_float(
                                row.get("CONST_IN_PROC")
                            ),
                            intangible_assets=self._to_float(
                                row.get("INTANGIBLE_ASSETS")
                            ),
                            goodwill=self._to_float(row.get("GOODWILL")),
                            long_term_equity_investment=self._to_float(
                                row.get("LT_EQUITY_INV")
                            ),
                            investment_real_estate=self._to_float(
                                row.get("INV_REALESTATE")
                            ),
                            right_of_use_assets=self._to_float(
                                row.get("USE_RIGHT_ASSETS")
                            ),
                            # ==================================================
                            # 负债
                            # ==================================================
                            total_liabilities=self._to_float(row.get("TOTAL_LIAB")),
                            current_liabilities=self._to_float(
                                row.get("TOTAL_CUR_LIAB")
                            ),
                            non_current_liabilities=self._to_float(
                                row.get("TOTAL_NONCUR_LIAB")
                            ),
                            short_term_debt=self._to_float(row.get("ST_BORROWING")),
                            long_term_debt=self._to_float(row.get("LT_LOAN")),
                            accounts_payable=self._to_float(row.get("ACCT_PAYABLE")),
                            notes_payable=self._to_float(row.get("NOTES_PAYABLE")),
                            bonds_payable=self._to_float(row.get("BONDS_PAYABLE")),
                            lease_liability=self._to_float(row.get("LEASE_LIABILITY")),
                            tax_payable=self._to_float(row.get("TAX_PAYABLE")),
                            dividends_payable=self._to_float(row.get("DIV_PAYABLE")),
                            # ==================================================
                            # 所有者权益
                            # ==================================================
                            total_equity=self._to_float(
                                row.get("TOT_SHARE_EQUITY_INCL_MIN_INT")
                            ),
                            shareholders_equity=self._to_float(
                                row.get("TOT_SHARE_EQUITY_EXCL_MIN_INT")
                            ),
                            minority_interest=self._to_float(
                                row.get("MINORITY_EQUITY")
                            ),
                            share_capital=self._to_float(row.get("CAP_STOCK")),
                            capital_reserve=self._to_float(row.get("CAP_RESV")),
                            surplus_reserve=self._to_float(row.get("SURPLUS_RESV")),
                            undistributed_profit=self._to_float(
                                row.get("UNDISTRIBUTED_PRO")
                            ),
                            treasury_stock=self._to_float(row.get("LESS_TREASURY_STK")),
                        )
                    )

                # ======================================================
                # 按报告期升序排列
                # ======================================================
                symbol_balance_sheets.sort(key=lambda item: item.report_date or "")
                balance_sheets[symbol] = symbol_balance_sheets
            return balance_sheets

        except SystemExit as exc:
            print(f"[银河] get_balance_sheet 调用了 exit(): " f"{exc}")
            return {}

        except BaseException as exc:
            print(f"[银河] get_balance_sheet 异常: " f"{type(exc).__name__}: {exc}")
            return {}

    def fetch_cash_flows(
        self,
        symbols: list[str],
        start_year: int | None = None,
        start_quarter: int | None = None,
        end_year: int | None = None,
        end_quarter: int | None = None,
    ) -> dict[str, list[CashFlow]]:
        cash_flows: dict[str, list[CashFlow]] = {}
        try:
            # ======================================================
            # 获取银河指定股票列表的上市公司的现金流量表数据
            # 本地保存全量历史数据，且每次调用接口默认增量更新本地数据，从而加速接口读取速度
            # ======================================================
            result = self.gateway.info_data.get_cash_flow(
                symbols,
                local_path=self.gateway.local_path,
                is_local=True,
            )

            if not result:
                print(f"[银河] 未获取到现金流量表数据: {symbols}")
                return {}

            for symbol in symbols:
                # ======================================================
                # 获取当前股票 DataFrame
                # ======================================================
                df = result.get(symbol)
                if df is None:
                    print(f"[银河] 未找到股票现金流量表: {symbol}")
                    continue

                if df.empty:
                    print(f"[银河] 现金流量表为空: {symbol}")
                    continue

                if "REPORTING_PERIOD" not in df.columns:
                    print(f"[银河] 现金流量表缺少 REPORTING_PERIOD: " f"{symbol}")
                    continue

                # ======================================================
                # 根据报告期筛选
                # ======================================================

                selected_rows = []
                for _, row in df.iterrows():
                    statement_type = row.get("STATEMENT_TYPE")
                    # --------------------------------------------------
                    # 只使用合并报表
                    # --------------------------------------------------
                    if statement_type != "1":
                        continue
                    report_date = str(row.get("REPORTING_PERIOD"))
                    if not report_date:
                        continue
                    report_year, report_quarter = self._parse_report_period(report_date)

                    # --------------------------------------------------
                    # 起始报告期
                    # --------------------------------------------------
                    if start_year is not None:
                        if self._quarter_index(
                            report_year,
                            report_quarter,
                        ) < self._quarter_index(
                            start_year,
                            start_quarter,
                        ):
                            continue

                    # --------------------------------------------------
                    # 结束报告期
                    # --------------------------------------------------
                    if end_year is not None:
                        if self._quarter_index(
                            report_year,
                            report_quarter,
                        ) > self._quarter_index(
                            end_year,
                            end_quarter,
                        ):
                            continue

                    selected_rows.append(row)

                if not selected_rows:
                    continue

                # ======================================================
                # 转换为标准 CashFlow
                # ======================================================

                symbol_cash_flows: list[CashFlow] = []

                for row in selected_rows:

                    symbol_cash_flows.append(
                        CashFlow(
                            # ==================================================
                            # 基础信息
                            # ==================================================
                            symbol=symbol,
                            report_date=self._to_str(row.get("REPORTING_PERIOD")),
                            report_type=self._to_str(row.get("REPORT_TYPE")),
                            statement_type=self._to_str(row.get("STATEMENT_TYPE")),
                            announcement_date=self._to_str(row.get("ANN_DATE")),
                            currency=self._to_str(row.get("CURRENCY_CODE")),
                            # ==================================================
                            # 经营活动
                            # ==================================================
                            operating_cash_flow=self._to_float(
                                row.get("NET_CASH_FLOWS_OPERA_ACT")
                            ),
                            cash_flow_from_operations=self._to_float(
                                row.get("IND_NET_CASH_FLOWS_OPERA_ACT")
                            ),
                            operating_cash_inflow=self._to_float(
                                row.get("TOT_CASH_INFLOW_OPER_ACT")
                            ),
                            operating_cash_outflow=self._to_float(
                                row.get("TOT_CASH_OUTFLOW_OPERA_ACT")
                            ),
                            cash_received_from_sales=self._to_float(
                                row.get("CASH_RECP_SG_AND_RS")
                            ),
                            cash_paid_for_goods=self._to_float(
                                row.get("CASH_PAY_GOODS_SERVICES")
                            ),
                            cash_paid_to_employees=self._to_float(
                                row.get("CASH_PAY_EMPLOYEE")
                            ),
                            taxes_paid=self._to_float(row.get("PAY_ALL_TAX")),
                            tax_refund_received=self._to_float(
                                row.get("RECP_TAX_REFUND")
                            ),
                            # ==================================================
                            # 投资活动
                            # ==================================================
                            investing_cash_flow=self._to_float(
                                row.get("NET_CASH_FLOWS_INV_ACT")
                            ),
                            investing_cash_inflow=self._to_float(
                                row.get("TOT_CASH_INFLOW_INV_ACT")
                            ),
                            investing_cash_outflow=self._to_float(
                                row.get("TOT_CASH_OUTFLOW_INV_ACT")
                            ),
                            capital_expenditure=self._to_float(
                                row.get("CASH_PAID_PUR_CONST_FIOLTA")
                            ),
                            cash_received_from_investments=self._to_float(
                                row.get("CASH_RECP_RECOV_INV")
                            ),
                            investment_income_received=self._to_float(
                                row.get("CASH_RECP_INV_INCOME")
                            ),
                            # ==================================================
                            # 筹资活动
                            # ==================================================
                            financing_cash_flow=self._to_float(
                                row.get("NET_CASH_FLOWS_FIN_ACT")
                            ),
                            financing_cash_inflow=self._to_float(
                                row.get("TOT_CASH_INFLOW_FIN_ACT")
                            ),
                            financing_cash_outflow=self._to_float(
                                row.get("TOT_CASH_OUTFLOW_FIN_ACT")
                            ),
                            cash_received_from_borrowings=self._to_float(
                                row.get("CASH_RECE_BORROW")
                            ),
                            cash_paid_for_debt=self._to_float(
                                row.get("CASH_PAY_FOR_DEBT")
                            ),
                            dividends_interest_paid=self._to_float(
                                row.get("CASH_PAY_DIST_DIV_PRO_INT")
                            ),
                            cash_from_equity_investment=self._to_float(
                                row.get("ABSORB_CASH_RECP_INV")
                            ),
                            # ==================================================
                            # 现金及现金等价物
                            # ==================================================
                            beginning_cash_balance=self._to_float(
                                row.get("BEG_BAL_CASH_CASH_EQU")
                            ),
                            ending_cash_balance=self._to_float(
                                row.get("END_BAL_CASH_CASH_EQU")
                            ),
                            net_change_in_cash=self._to_float(
                                row.get("NET_INCR_CASH_AND_CASH_EQU")
                            ),
                            exchange_rate_effect=self._to_float(
                                row.get("EFF_FX_FLUC_CASH")
                            ),
                            # ==================================================
                            # 自由现金流
                            # ==================================================
                            free_cash_flow=self._to_float(row.get("FREE_CASH_FLOW")),
                        )
                    )

                # ======================================================
                # 按报告期升序排列
                # ======================================================

                symbol_cash_flows.sort(key=lambda item: item.report_date or "")

                cash_flows[symbol] = symbol_cash_flows

            return cash_flows

        except Exception as exc:
            print(f"[银河] 获取现金流量表失败 " f"{symbols}: {exc}")
            return {}

    def fetch_income_statements(
        self,
        symbols: list[str],
        start_year: int | None = None,
        start_quarter: int | None = None,
        end_year: int | None = None,
        end_quarter: int | None = None,
    ) -> dict[str, list[IncomeStatement]]:

        statements: dict[str, list[IncomeStatement]] = {}

        try:
            # ======================================================
            # 获取银河指定股票列表的上市公司的利润表数据
            # 本地保存全量历史数据，且每次调用接口默认增量更新本地数据，从而加速接口读取速度
            # ======================================================

            result = self.gateway.info_data.get_income(
                symbols,
                local_path=self.gateway.local_path,
                is_local=True,
            )

            if not result:
                print(f"[银河] 未获取到利润表数据: {symbols}")
                return {}

            for symbol in symbols:

                # ======================================================
                # 获取当前股票 DataFrame
                # ======================================================

                df = result.get(symbol)

                if df is None:
                    print(f"[银河] 未找到股票利润表: {symbol}")
                    continue

                if df.empty:
                    print(f"[银河] 利润表为空: {symbol}")
                    continue

                if "REPORTING_PERIOD" not in df.columns:
                    print(f"[银河] 利润表缺少 REPORTING_PERIOD: " f"{symbol}")
                    continue

                # ======================================================
                # 根据报告期筛选
                # ======================================================

                selected_rows = []

                for _, row in df.iterrows():
                    statement_type = row.get("STATEMENT_TYPE")
                    if statement_type != "1":
                        continue

                    report_date = str(row.get("REPORTING_PERIOD"))
                    if not report_date:
                        continue

                    report_year, report_quarter = self._parse_report_period(report_date)

                    # --------------------------------------------------
                    # 起始报告期
                    # --------------------------------------------------

                    if start_year is not None:
                        if self._quarter_index(
                            report_year,
                            report_quarter,
                        ) < self._quarter_index(
                            start_year,
                            start_quarter,
                        ):
                            continue

                    # --------------------------------------------------
                    # 结束报告期
                    # --------------------------------------------------

                    if end_year is not None:
                        if self._quarter_index(
                            report_year,
                            report_quarter,
                        ) > self._quarter_index(
                            end_year,
                            end_quarter,
                        ):
                            continue

                    selected_rows.append(row)

                if not selected_rows:
                    continue

                # ======================================================
                # 转换为标准 IncomeStatement
                # ======================================================

                symbol_statements: list[IncomeStatement] = []

                for row in selected_rows:
                    symbol_statements.append(
                        IncomeStatement(
                            # ==================================================
                            # 基础信息
                            # ==================================================
                            symbol=symbol,
                            report_date=self._to_str(row.get("REPORTING_PERIOD")),
                            report_type=self._to_str(row.get("REPORT_TYPE")),
                            statement_type=self._to_str(row.get("STATEMENT_TYPE")),
                            announcement_date=self._to_str(row.get("ANN_DATE")),
                            currency=self._to_str(row.get("CURRENCY_CODE")),
                            # ==================================================
                            # 收入
                            # ==================================================
                            revenue=self._to_float(row.get("OPERA_REV")),
                            total_operating_income=self._to_float(
                                row.get("TOT_OPERA_REV")
                            ),
                            # ==================================================
                            # 成本费用
                            # ==================================================
                            operating_cost=self._to_float(row.get("LESS_OPERA_COST")),
                            total_operating_cost=self._to_float(
                                row.get("TOT_OPERA_COST")
                            ),
                            selling_expense=self._to_float(row.get("LESS_SELLING_EXP")),
                            administrative_expense=self._to_float(
                                row.get("LESS_ADMIN_EXP")
                            ),
                            financial_expense=self._to_float(row.get("LESS_FIN_EXP")),
                            rd_expense=self._to_float(row.get("RD_EXP")),
                            business_tax_and_surcharge=self._to_float(
                                row.get("LESS_BUS_TAX_SURCHARGE")
                            ),
                            asset_impairment_loss=self._to_float(
                                row.get("LESS_ASSETS_IMPAIR_LOSS")
                            ),
                            credit_impairment_loss=self._to_float(
                                row.get("CREDIT_IMPAIR_LOSS")
                            ),
                            # ==================================================
                            # 收益项目
                            # ==================================================
                            investment_income=self._to_float(
                                row.get("PLUS_NET_INV_INC")
                            ),
                            fair_value_change_income=self._to_float(
                                row.get("PLUS_NET_GAIN_CHG_FV")
                            ),
                            exchange_income=self._to_float(row.get("PLUS_NET_FX_INC")),
                            other_income=self._to_float(row.get("OTH_INCOME")),
                            # ==================================================
                            # 利润
                            # ==================================================
                            gross_profit=self._calculate_gross_profit(row),
                            operating_profit=self._to_float(row.get("OPERA_PROFIT")),
                            total_profit=self._to_float(row.get("TOTAL_PROFIT")),
                            income_tax=self._to_float(row.get("INCOME_TAX")),
                            net_profit=self._to_float(
                                row.get("NET_PRO_INCL_MIN_INT_INC")
                            ),
                            net_profit_attributable=self._to_float(
                                row.get("NET_PRO_EXCL_MIN_INT_INC")
                            ),
                            non_recurring_net_profit=self._first_float(
                                row.get("NET_PRO_AFTER_DED_NR_GL"),
                                row.get("NET_PRO_AFTER_DED_NR_GL_COR"),
                            ),
                            # ==================================================
                            # 营业外收支
                            # ==================================================
                            non_operating_income=self._to_float(
                                row.get("PLUS_NON_OPERA_REV")
                            ),
                            non_operating_expense=self._to_float(
                                row.get("LESS_NON_OPERA_EXP")
                            ),
                            # ==================================================
                            # 其他综合收益
                            # ==================================================
                            other_comprehensive_income=self._to_float(
                                row.get("OTH_COMPRE_INC")
                            ),
                            # ==================================================
                            # EBIT / EBITDA
                            # ==================================================
                            ebit=self._to_float(row.get("EBIT")),
                            ebitda=self._to_float(row.get("EBITDA")),
                            # ==================================================
                            # 每股收益
                            # ==================================================
                            eps=self._to_float(row.get("BASIC_EPS")),
                            diluted_eps=self._to_float(row.get("DILUTED_EPS")),
                        )
                    )

                # ======================================================
                # 按报告期升序排列
                # ======================================================

                symbol_statements.sort(key=lambda item: item.report_date or "")

                statements[symbol] = symbol_statements

            return statements

        except Exception as exc:
            print(f"[银河] 获取利润表失败 " f"{symbols}: {exc}")
            return {}

    @staticmethod
    def _safe_float(value):
        """
        安全转换 float。
        """

        if value is None:
            return None

        try:
            return float(value)

        except (
            TypeError,
            ValueError,
        ):
            return None

    @staticmethod
    def _to_float(
        value: Any,
    ) -> float | None:
        """
        将数据源字段安全转换为 float。
        """

        if value is None:
            return None

        try:
            if pandas.isna(value):
                return None
        except (TypeError, ValueError):
            pass

        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _to_str(
        value: object,
    ) -> str | None:
        """
        安全转换为字符串。
        """

        if value is None:
            return None

        try:
            if pandas.isna(value):
                return None
        except (TypeError, ValueError):
            pass

        value = str(value).strip()

        return value or None

    @classmethod
    def _calculate_gross_profit(
        cls,
        row: pandas.Series,
    ) -> float | None:
        """
        计算毛利润。

        Gross Profit =
            营业收入 - 营业成本
        """

        revenue = cls._to_float(row.get("OPERA_REV"))

        cost = cls._to_float(row.get("LESS_OPERA_COST"))

        if revenue is None or cost is None:
            return None

        return revenue - cost

    @staticmethod
    def _first_float(*values: object) -> float | None:
        for value in values:
            result = YinheFinancial._to_float(value)

            if result is not None:
                return result

        return None

    @staticmethod
    def _parse_report_period(
        report_date: str,
    ) -> tuple[int, int]:
        """
        将报告期转换为报告年度和季度。

        支持以下格式：

            20260630
            2026-06-30
            2026/06/30

        返回：

            (2026, 2)

        对应：

            03-31 -> Q1
            06-30 -> Q2
            09-30 -> Q3
            12-31 -> Q4
        """

        if report_date is None:
            raise ValueError("报告期不能为空")

        value = str(report_date).strip()

        # ==========================================================
        # 统一日期格式
        # ==========================================================

        value = value.replace("-", "")
        value = value.replace("/", "")

        if len(value) != 8 or not value.isdigit():
            raise ValueError(f"无效的财务报告期: {report_date}")

        # ==========================================================
        # 提取年月日
        # ==========================================================

        year = int(value[:4])
        month = int(value[4:6])
        day = int(value[6:8])

        # ==========================================================
        # 根据报告期月份判断季度
        # ==========================================================

        quarter_map = {
            (3, 31): 1,
            (6, 30): 2,
            (9, 30): 3,
            (12, 31): 4,
        }

        quarter = quarter_map.get((month, day))

        if quarter is None:
            raise ValueError(f"无效的财务报告期: {report_date}")

        return year, quarter

    @staticmethod
    def _quarter_index(
        year: int,
        quarter: int,
    ) -> int:
        """
        将报告年度和季度转换为连续季度序号。

        用于报告期之间的先后比较。

        示例：
            2025Q1 < 2025Q2
            2025Q4 < 2026Q1
        """

        return year * 4 + quarter - 1

    def fetch_financial(
        self,
        symbol: str,
        start_year: int | None = None,
        start_quarter: int | None = None,
        end_year: int | None = None,
        end_quarter: int | None = None,
    ) -> list[Financial]:
        """
        获取指定股票的财务数据。

        返回：

            list[Financial]

        一个 Financial 对应一个报告期。

        例如：

            [
                Financial(20240630),
                Financial(20240930),
                Financial(20241231),
                Financial(20250331),
                Financial(20250630),
                Financial(20250930),
                Financial(20251231),
                Financial(20260331),
                Financial(20260630),
            ]

        注意：

            1. 本方法只负责获取和组装数据
            2. 不负责财务分析
            3. 不负责判断同比、环比
            4. 不负责选择 current / previous_year / previous_quarter
            5. Analyzer 自己处理这些逻辑
        """

        # ======================================================
        # 获取利润表
        # ======================================================

        income_statements = self.fetch_income_statement(
            symbol=symbol,
            start_year=start_year,
            start_quarter=start_quarter,
            end_year=end_year,
            end_quarter=end_quarter,
        )

        # ======================================================
        # 获取资产负债表
        # ======================================================

        balance_sheets = self.fetch_balance_sheet(
            symbol=symbol,
            start_year=start_year,
            start_quarter=start_quarter,
            end_year=end_year,
            end_quarter=end_quarter,
        )

        # ======================================================
        # 获取现金流量表
        # ======================================================

        cash_flows = self.fetch_cash_flow(
            symbol=symbol,
            start_year=start_year,
            start_quarter=start_quarter,
            end_year=end_year,
            end_quarter=end_quarter,
        )

        # ======================================================
        # 建立报告期索引
        # ======================================================

        income_map = {
            item.report_date: item for item in income_statements if item.report_date
        }

        balance_map = {
            item.report_date: item for item in balance_sheets if item.report_date
        }

        cash_flow_map = {
            item.report_date: item for item in cash_flows if item.report_date
        }

        # ======================================================
        # 合并所有报告期
        #
        # 某一张报表缺失时：
        #
        #     income=None
        #     balance=None
        #     cash_flow=None
        #
        # 仍然保留这个 Financial。
        #
        # 这样 Analyzer 可以根据实际数据决定哪些指标可以计算。
        # ======================================================

        report_dates = sorted(set(income_map) | set(balance_map) | set(cash_flow_map))

        if not report_dates:
            print(f"[财务] 未获取到财务数据: {symbol}")
            return []

        financials: list[Financial] = []

        for report_date in report_dates:

            financials.append(
                Financial(
                    symbol=symbol,
                    report_date=report_date,
                    income=income_map.get(report_date),
                    balance=balance_map.get(report_date),
                    cash_flow=cash_flow_map.get(report_date),
                )
            )

        # ======================================================
        # 按报告期排序
        # ======================================================

        financials.sort(key=lambda item: item.report_date or "")

        return financials
