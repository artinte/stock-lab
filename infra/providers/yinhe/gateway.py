from __future__ import annotations

import datetime
import os
import traceback
from typing import Any, Optional

import AmazingData
import pandas
from dotenv import load_dotenv
import tgw

from common.enums.quote_level import QuoteLevel
from core.models.stock import Stock
from infra.gateways.stock_data import StockDataGateway
from common.constants import Interval, TEN_THOUSAND
from core.models.financial.financial import IncomeStatement
from core.models.financial.financial import CashFlow
from core.models.financial.financial import BalanceSheet
from core.models.financial.financial import Financial
from core.models.kline import Kline
from core.models.valuation import Valuation
from core.models.quote import Quote
from infra.providers.yinhe.equity_structure import YinheEquityStructure
from infra.providers.yinhe.etf import YinheETF
from infra.providers.yinhe.financial import YinheFinancial
from infra.providers.yinhe.kline import YinheKline
from infra.providers.yinhe.quote import YinheQuote
from infra.providers.yinhe.stock import YinheStock
from infra.providers.yinhe.valuation import YinheValuation
from infra.registry import GatewayRegistry

from utils.stock_mapping import normalize_symbol

"""
银河证券数据网关。

银河证券提供两组API：
pip install tgw-1.7.1-py3-none-any.whl 
pip install AmazingData-1.0.0-cp312-none-any.whl

具体介绍联系相关券商。

本模块实现基于 AmazingData 的银河证券数据源适配器，
将 AmazingData 提供的原始数据转换为项目内部统一的数据模型
和接口，使上层业务无需直接依赖具体的数据源实现。

主要功能包括：

- 管理 AmazingData 数据源的登录、注销和运行状态。
- 获取股票基础信息。
- 获取历史 K 线，并转换为统一的 Kline 模型。
- 获取股票财务数据。
- 获取股票最新价格及总市值。
- 根据财务数据和市值计算静态 PE、动态 PE 和 TTM PE。
- 将估值结果转换为统一的 Valuation 模型。
- 对股票代码进行标准化，自动识别上海、深圳和北京市场。

本模块属于数据源适配层，上层业务统一通过
StockDataGateway 访问数据，不应直接依赖 AmazingData。

数据流：

    DataManager
        ↓
    StockDataGateway
        ↓
    YinheGateway
        ↓
    AmazingData
        ↓
    银河证券数据服务

当前已支持：

- 股票基础信息
- 历史 K 线
- 财务数据
- 估值数据

实时行情接口暂未接入，相关方法会明确抛出 NotImplementedError。
"""


@GatewayRegistry.register("yinhe")
class YinheGateway(StockDataGateway):
    """
    银河证券数据网关。

    负责将 AmazingData 数据接口适配到统一的
    StockDataGateway 接口。

    上层业务只依赖 StockDataGateway，
    不应该直接依赖 AmazingData。
    """

    name = "yinhe"
    display_name = "银河证券"

    def __init__(
        self,
        config: Optional[dict] = None,
    ) -> None:
        """
        初始化银河证券数据网关。

        Parameters
        ----------
        config:
            数据源配置，例如：

                {
                    "host": "...",
                    "port": 1234,
                    "username": "...",
                    "password": "...",
                    "local_path": "..."
                }
        """

        self.config = config or {}

        self._started = False

        self.user = ""
        self.host = ""
        self.port = 0

        self.local_path = os.path.curdir

        # AmazingData 数据接口
        self.info_data = None
        self.base_data = None
        self.calendar = None
        self.market_data = None

        # ==========================================================
        # 组合式设计（Composition）
        #
        # YinheGateway 作为银河证券数据源的统一入口，
        # 负责生命周期管理以及对外接口转发。
        #
        # 具体业务功能按照数据类型拆分到独立组件中：
        #
        #     YinheStock       股票基础信息
        #     YinheKline       K线数据
        #     YinheQuote       行情数据
        #     YinheFinancial   财务数据
        #     YinheValuation   估值数据
        #
        # 这些组件共享同一个 YinheGateway 实例，
        # 可以访问银河证券的数据连接、登录状态以及
        # AmazingData 接口对象。
        #
        # 这样可以避免 YinheGateway 成为一个过大的上帝类，
        # 同时保持 DataManager 和 StockDataGateway 接口稳定。
        #
        # 注意：
        # 这些组件并不是独立的数据源，
        # 而是 YinheGateway 内部针对不同业务能力的拆分。
        # ==========================================================

        self.stock = YinheStock(self)

        self.kline = YinheKline(self)

        self.equity_structure = YinheEquityStructure(self)

        self.quote = YinheQuote(self)

        self.income_statement = IncomeStatement(self)

        self.balance_sheet = BalanceSheet(self)

        self.cash_flow_statement = CashFlow(self)

        self.financial = YinheFinancial(self)

        self.valuation = YinheValuation(self)

        self.etf = YinheETF(self)

    # ==========================================================
    # 生命周期
    # ==========================================================

    def login(
        self,
        config: Optional[dict] = None,
    ) -> bool:
        """
        登录银河证券数据源。

        登录成功后初始化：

            InfoData
            BaseData
            Calendar
            MarketData
        """

        if config:
            self.config.update(config)
        else:
            load_dotenv()

            self.config = {
                "username": os.getenv("amazing_username", ""),
                "password": os.getenv("amazing_password", ""),
                "host": os.getenv("amazing_host", ""),
                "port": int(os.getenv("amazing_port", "0")),
                "local_path": os.getenv("local_path", os.path.curdir),
            }

        try:
            self.user = self.config.get("username", "default")
            self.host = self.config.get("host", "127.0.0.1")
            self.port = int(self.config.get("port", 0))
            self.local_path = self.config.get("local_path", os.path.curdir)

            print(
                f"[银河网关] 尝试登录: "
                f"网址：{self.host}:{self.port}\n"
                f"用户: {self.user}"
            )

            # --------------------------------------------------
            # 登录 AmazingData
            # --------------------------------------------------

            AmazingData.login(
                username=self.config["username"],
                password=self.config["password"],
                host=self.config["host"],
                port=self.port,
            )

            # --------------------------------------------------
            # 初始化数据接口
            # --------------------------------------------------

            self.info_data = AmazingData.InfoData()
            self.base_data = AmazingData.BaseData()
            self.calendar = self.base_data.get_calendar()
            self.market_data = AmazingData.MarketData(self.calendar)
            self._started = True

            print("[银河网关] 登录成功")
            return True

        except ValueError:
            print("[银河网关] 端口格式无效，请检查配置。")
            traceback.print_exc()
            self._started = False
            return False

        except Exception as e:
            print(f"[银河网关] 登录异常: {e}")
            self._started = False
            return False

    def logout(self) -> None:
        """
        注销银河数据源。
        """
        if self._started:
            try:
                print("[银河网关] 退出登录")
                AmazingData.logout(self.user)
            except Exception as e:
                print(f"[银河网关] 注销异常: {e}")

        self.info_data = None
        self.base_data = None
        self.calendar = None
        self.market_data = None
        self._started = False

    def health_check(self) -> bool:
        """
        检查数据源是否已经启动。
        """
        return self._started

    def fetch_stock(
        self,
        symbol: str,
    ) -> Stock:
        """
        获取股票基础信息。

        当前返回：

            {
                "symbol": "...",
                "name": "..."
            }
        """
        return self.stock.fetch_stock(symbol)

    def fetch_stocks(
        self,
        symbols: list[str],
    ) -> list[Stock]:
        """
        批量获取股票基础信息。
        """
        return self.stock.fetch_stocks(symbols)

    def fetch_kline(
        self,
        symbol: str,
        interval: Interval = Interval.DAY_1,
        start_time: Optional[datetime.datetime] = None,
        end_time: Optional[datetime.datetime] = None,
        limit: int = 1000,
    ) -> list[Kline]:
        """
        获取历史 K 线。

        AmazingData 原始数据：
            DataFrame

        转换为：
            list[Kline]
        """
        if end_time is None:
            end_time = datetime.datetime.now()

        if start_time is None:
            if interval == "1d":
                start_time = end_time - datetime.timedelta(days=limit * 2)
            elif interval == "1w":
                start_time = end_time - datetime.timedelta(weeks=limit * 2)
            elif interval == "1M":
                start_time = end_time - datetime.timedelta(days=limit * 31 * 2)
        return self.kline.fetch_kline(symbol, interval, start_time, end_time, limit)

    def fetch_equity_structure(
        self,
        symbol,
    ):
        return self.equity_structure.fetch_equity_structure(symbol)

    def fetch_equity_structures(
        self,
        symbols,
    ):
        return self.equity_structure.fetch_equity_structures(symbols)

    def fetch_quote(
        self,
        symbol: str,
        quote_level: Optional[QuoteLevel] = None,
    ) -> Optional[Quote]:
        """
        获取股票最新行情。

        当前 AmazingData 未直接接入实时行情接口，
        使用最近交易日 K 线构造行情快照。

        因此：

            price = 最近交易日收盘价
            prev_close = 前一交易日收盘价

        注意：
            这里不是实时行情。
        """
        return self.quote.fetch_quote(symbol=symbol, quote_level=quote_level)

    def fetch_quotes(
        self,
        symbols: list[str],
        quote_level: Optional[QuoteLevel] = None,
    ):
        """
        批量获取股票最新行情。
        """
        return self.quote.fetch_quotes(
            symbols,
            quote_level,
        )

    def fetch_valuation(
        self,
        symbol: str,
    ) -> Valuation:
        """
        获取股票估值数据。

        包括：

            当前价格
            总市值
            静态 PE
            动态 PE
            TTM PE
        """
        return self.valuation.fetch_valuation(symbol)

    def fetch_etf_composition(
        self,
        symbol: str,
        trade_date: datetime.date | None = None,
    ):
        return self.etf.fetch_etf_composition(symbol, trade_date)

    def _get_latest_financial_row(
        self,
        df,
    ):
        """
        获取最新一期财务数据。
        """

        if df is None or df.empty:
            return None

        if "REPORTING_PERIOD" in df.columns:
            df = df.copy()
            df["REPORTING_PERIOD"] = df["REPORTING_PERIOD"].astype(str)
            df = df.sort_values("REPORTING_PERIOD")
        return df.iloc[-1]

    def fetch_balance_sheet(
        self,
        symbol: str,
        start_year: Optional[int] = None,
        start_quarter: Optional[int] = None,
        end_year: Optional[int] = None,
        end_quarter: Optional[int] = None,
    ) -> BalanceSheet | None:
        """
        获取资产负债表。

        银河 get_balance_sheet() 返回：

            {
                "600519.SH": DataFrame
            }

        转换为统一 BalanceSheet 模型。
        """

        self._ensure_started()
        symbol = normalize_symbol(symbol)
        return self.financial.fetch_balance_sheet(
            symbol,
            start_year,
            start_quarter,
            end_year,
            end_quarter,
        )

    def fetch_income_statement(
        self,
        symbol: str,
        start_year: Optional[int] = None,
        start_quarter: Optional[int] = None,
        end_year: Optional[int] = None,
        end_quarter: Optional[int] = None,
    ) -> list[IncomeStatement]:
        """
        获取银河利润表数据。

        本方法由 StockDataGateway.fetch_income_statement()
        调用，不负责校验报告期参数。

        参数：
            symbol:
                标准化后的股票代码。

            start_year:
                起始报告年度。

            start_quarter:
                起始报告季度，取值 1~4。

            end_year:
                结束报告年度。

            end_quarter:
                结束报告季度，取值 1~4。

        查询规则：
            - 不指定开始和结束报告期：返回全部历史数据。
            - 只指定开始报告期：返回从开始报告期到最新的数据。
            - 只指定结束报告期：返回从最早数据到结束报告期的数据。
            - 同时指定开始和结束报告期：返回闭区间内的数据。

        返回：
            list[IncomeStatement]:
                标准化后的利润表数据。
                如果没有数据，则返回空列表。
        """

        self._ensure_started()
        symbol = normalize_symbol(symbol)
        self._validate_report_period(
            start_year,
            start_quarter,
            end_year,
            end_quarter,
        )

        return self.financial.fetch_income_statement(
            symbol,
            start_year,
            start_quarter,
            end_year,
            end_quarter,
        )

    def fetch_cash_flow(
        self,
        symbol: str,
        start_year: Optional[int] = None,
        start_quarter: Optional[int] = None,
        end_year: Optional[int] = None,
        end_quarter: Optional[int] = None,
    ) -> list[CashFlow]:
        """
        获取现金流量表。

        银河 get_cash_flow() 返回：

            {
                "600519.SH": DataFrame
            }

        转换为统一 CashFlowStatement 模型。
        """

        self._ensure_started()
        self._validate_report_period(
            start_year,
            start_quarter,
            end_year,
            end_quarter,
        )

        symbol = normalize_symbol(symbol)
        return self.financial.fetch_cash_flow(
            symbol,
            start_year,
            start_quarter,
            end_year,
            end_quarter,
        )

    def fetch_financial(
        self,
        symbol: str,
        start_year,
        start_quarter,
        end_year,
        end_quarter,
    ) -> Financial | None:

        self._ensure_started()
        symbol = normalize_symbol(symbol)
        return self.financial.fetch_financial(
            symbol,
            start_year,
            start_quarter,
            end_year,
            end_quarter,
        )

    def _ensure_started(self) -> None:
        """
        确保数据源已经启动。
        """
        if not self._started:
            raise RuntimeError("银河数据源尚未启动，" "请先调用 DataManager.start()")

    @property
    def version(self) -> str:
        try:
            return tgw.GetVersion()
        except Exception:
            return "unknown"
