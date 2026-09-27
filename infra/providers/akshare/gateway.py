from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

import akshare as ak

from common.constants import Interval
from infra.gateways.stock_data import StockDataGateway
from infra.registry import GatewayRegistry
from core.models.financial.financial import Financial
from core.models.stock.kline import Kline
from core.models.quote import Quote
from core.models.stock.basic_info import BasicInfo
from core.models.valuation import Valuation


@GatewayRegistry.register("akshare")
class AkShareGateway(StockDataGateway):
    """
    AkShare 股票数据网关。

    将 AkShare 原始数据转换为项目统一的数据模型。

    数据流：

        DataManager
            ↓
        StockDataGateway
            ↓
        AkShareGateway
            ↓
        AkShare

    上层业务只依赖 StockDataGateway，
    不应该直接依赖 AkShare。
    """

    name = "akshare"

    display_name = "AkShare"

    def __init__(
        self,
        config: Optional[dict] = None,
    ) -> None:
        super().__init__(config)

    # ==========================================================
    # 生命周期
    # ==========================================================

    def login(
        self,
        config: Optional[dict] = None,
    ) -> bool:
        """
        启动 AkShare 数据源。

        AkShare 不需要账号登录，因此这里只负责
        Gateway 生命周期管理。
        """

        if config:
            self.config.update(config)

        self._started = True

        return True

    def logout(self) -> None:
        """
        关闭 AkShare 数据源。
        """

        self._started = False

    def health_check(self) -> bool:
        """
        检查 AkShare 是否能够正常访问。
        """

        if not self._started:
            return False

        try:
            data = ak.stock_zh_a_spot_em()

            return data is not None and not data.empty

        except Exception as exc:
            print(f"[AkShare] 健康检查失败: {exc}")
            return False

    # ==========================================================
    # 股票基础信息
    # ==========================================================

    def fetch_basic_info(
        self,
        symbol: str,
    ) -> Optional[BasicInfo]:
        """
        获取股票基础信息。
        """

        self._ensure_started()

        code = self._normalize_symbol(symbol)

        try:
            data = ak.stock_zh_a_spot_em()

            if data is None or data.empty:
                return None

            row = data[data["代码"].astype(str) == code]

            if row.empty:
                return None

            item = row.iloc[0]

            return BasicInfo(
                symbol=symbol,
                name=self._get_value(
                    item,
                    "名称",
                ),
                market=self._detect_market(code),
                industry=None,
            )

        except Exception as exc:
            print(f"[AkShare] 获取股票基础信息失败 " f"{symbol}: {exc}")

            return None

    # ==========================================================
    # 单只行情
    # ==========================================================

    def fetch_quote(
        self,
        symbol: str,
    ) -> Optional[Quote]:
        """
        获取单只股票最新行情。

        AkShare 的 stock_zh_a_spot_em()
        返回的是全市场实时行情。

        这里获取全市场数据后，
        根据股票代码筛选目标股票。
        """

        self._ensure_started()

        code = self._normalize_symbol(symbol)

        try:
            data = ak.stock_zh_a_spot_em()

            if data is None or data.empty:
                return None

            row = data[data["代码"].astype(str) == code]

            if row.empty:
                print(f"[AkShare] 未找到股票行情: {symbol}")
                return None

            return self._convert_quote(
                symbol,
                row.iloc[0],
            )

        except Exception as exc:
            print(f"[AkShare] 获取行情失败 " f"{symbol}: {exc}")

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

        AkShare 一次获取全市场行情，
        然后在本地筛选目标股票。
        """

        self._ensure_started()

        if not symbols:
            return []

        try:
            data = ak.stock_zh_a_spot_em()

            if data is None or data.empty:
                return []

            symbol_map = {self._normalize_symbol(symbol): symbol for symbol in symbols}

            result: list[Quote] = []

            for _, row in data.iterrows():

                code = str(row["代码"])

                original_symbol = symbol_map.get(code)

                if original_symbol is None:
                    continue

                quote = self._convert_quote(
                    original_symbol,
                    row,
                )

                result.append(quote)

            return result

        except Exception as exc:
            print(f"[AkShare] 批量获取行情失败: {exc}")

            return []

    # ==========================================================
    # K 线
    # ==========================================================

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

        支持：

            1分钟
            5分钟
            15分钟
            30分钟
            60分钟
            日线
            周线
            月线
        """

        self._ensure_started()

        code = self._normalize_symbol(symbol)

        period = self._convert_interval(interval)

        start_date = start_time.strftime("%Y%m%d") if start_time else "19900101"

        end_date = (
            end_time.strftime("%Y%m%d")
            if end_time
            else datetime.now().strftime("%Y%m%d")
        )

        try:
            data = ak.stock_zh_a_hist(
                symbol=code,
                period=period,
                start_date=start_date,
                end_date=end_date,
                adjust="qfq",
            )

            if data is None or data.empty:
                return []

            result: list[Kline] = []

            for _, row in data.iterrows():

                try:
                    result.append(
                        Kline(
                            symbol=symbol,
                            timestamp=self._parse_datetime(row["日期"]),
                            interval=interval,
                            open=self._to_float(row["开盘"]),
                            high=self._to_float(row["最高"]),
                            low=self._to_float(row["最低"]),
                            close=self._to_float(row["收盘"]),
                            volume=self._to_float(row["成交量"]),
                            amount=self._to_float(row["成交额"]),
                        )
                    )

                except Exception as exc:
                    print(f"[AkShare] Kline 转换失败: {exc}")

                    continue

            result.sort(key=lambda item: item.timestamp)

            if limit > 0:
                result = result[-limit:]

            return result

        except Exception as exc:
            print(f"[AkShare] 获取 K 线失败 " f"{symbol}: {exc}")

            return []

    # ==========================================================
    # 估值
    # ==========================================================

    def fetch_valuation(
        self,
        symbol: str,
    ) -> Optional[Valuation]:
        """
        获取股票估值。

        AkShare 实时行情接口可以直接提供：

            最新价格
            总市值
            流通市值
            动态 PE
            PB

        静态 PE 和 TTM PE 如果数据源没有提供，
        则暂时保持 None。
        """

        self._ensure_started()

        code = self._normalize_symbol(symbol)

        try:
            data = ak.stock_zh_a_spot_em()

            if data is None or data.empty:
                return None

            row = data[data["代码"].astype(str) == code]

            if row.empty:
                return None

            item = row.iloc[0]

            price = self._get_float(
                item,
                "最新价",
            )

            return Valuation(
                symbol=symbol,
                timestamp=datetime.now(),
                price=price,
                market_cap=self._get_float(
                    item,
                    "总市值",
                ),
                circulating_market_cap=self._get_float(
                    item,
                    "流通市值",
                ),
                pe_dynamic=self._get_float(
                    item,
                    "市盈率-动态",
                ),
                pe_ttm=None,
                pe_static=None,
                pb=self._get_float(
                    item,
                    "市净率",
                ),
            )

        except Exception as exc:
            print(f"[AkShare] 获取估值失败 " f"{symbol}: {exc}")

            return None

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

    # ==========================================================
    # 财务数据
    # ==========================================================

    def fetch_financial(
        self,
        symbol: str,
    ) -> Optional[Financial]:
        """
        获取股票财务数据。

        使用：

            ak.stock_financial_analysis_indicator()
        """

        self._ensure_started()

        code = self._normalize_symbol(symbol)

        try:
            data = ak.stock_financial_analysis_indicator(
                symbol=code,
            )

            if data is None or data.empty:
                return None

            row = data.iloc[0]

            return self._convert_financial(
                symbol,
                row,
            )

        except Exception as exc:
            print(f"[AkShare] 获取财务数据失败 " f"{symbol}: {exc}")

            return None

    # ==========================================================
    # Financial 转换
    # ==========================================================

    def _convert_financial(
        self,
        symbol: str,
        row: Any,
    ) -> Financial:
        """
        AkShare 财务数据 → Financial。
        """

        values = {
            "symbol": symbol,
            "report_date": self._get_value(
                row,
                "日期",
            ),
            "roe": self._get_float(
                row,
                "净资产收益率",
            ),
            "gross_margin": self._get_float(
                row,
                "销售毛利率",
            ),
            "net_margin": self._get_float(
                row,
                "销售净利率",
            ),
            "revenue_growth": self._get_float(
                row,
                "主营业务收入增长率",
            ),
            "profit_growth": self._get_float(
                row,
                "净利润增长率",
            ),
        }

        try:
            return Financial(**values)

        except TypeError as exc:
            raise RuntimeError(
                "Financial 模型字段与 " "AkShareGateway 映射不一致。"
            ) from exc

    # ==========================================================
    # Quote 转换
    # ==========================================================

    @classmethod
    def _convert_quote(
        cls,
        symbol: str,
        row: Any,
    ) -> Quote:
        """
        AkShare 行情数据 → Quote。
        """

        return Quote(
            symbol=symbol,
            name=cls._get_value(
                row,
                "名称",
            ),
            timestamp=datetime.now(),
            last_price=cls._get_float(
                row,
                "最新价",
            ),
            prev_close=cls._get_float(
                row,
                "昨收",
            ),
            open=cls._get_float(
                row,
                "今开",
            ),
            high=cls._get_float(
                row,
                "最高",
            ),
            low=cls._get_float(
                row,
                "最低",
            ),
            change=cls._get_float(
                row,
                "涨跌额",
            ),
            change_percent=cls._get_float(
                row,
                "涨跌幅",
            ),
            volume=cls._get_float(
                row,
                "成交量",
            ),
            amount=cls._get_float(
                row,
                "成交额",
            ),
            turnover=cls._get_float(
                row,
                "换手率",
            ),
            volume_ratio=cls._get_float(
                row,
                "量比",
            ),
            market_cap=cls._get_float(
                row,
                "总市值",
            ),
            circulating_market_cap=cls._get_float(
                row,
                "流通市值",
            ),
            pe_dynamic=cls._get_float(
                row,
                "市盈率-动态",
            ),
            pb=cls._get_float(
                row,
                "市净率",
            ),
            high_limit=cls._get_float(
                row,
                "涨停",
            ),
            low_limit=cls._get_float(
                row,
                "跌停",
            ),
            average_price=cls._get_float(
                row,
                "均价",
            ),
            amplitude=cls._get_float(
                row,
                "振幅",
            ),
        )

    # ==========================================================
    # 股票代码
    # ==========================================================

    @staticmethod
    def _normalize_symbol(
        symbol: str,
    ) -> str:
        """
        标准化股票代码。

        例如：

            600519
            600519.SH

        最终统一为：

            600519
        """

        value = symbol.strip().upper()

        if "." in value:
            value = value.split(
                ".",
                1,
            )[0]

        return value

    @staticmethod
    def _detect_market(
        code: str,
    ) -> str:
        """
        根据股票代码判断市场。
        """

        if code.startswith(
            (
                "600",
                "601",
                "603",
                "605",
                "688",
                "689",
            )
        ):
            return "SH"

        if code.startswith(
            (
                "000",
                "001",
                "002",
                "003",
                "300",
                "301",
            )
        ):
            return "SZ"

        if code.startswith(
            (
                "4",
                "8",
            )
        ):
            return "BJ"

        return "UNKNOWN"

    # ==========================================================
    # Interval
    # ==========================================================

    @staticmethod
    def _convert_interval(
        interval: Interval,
    ) -> str:
        """
        项目 Interval → AkShare period。
        """

        mapping = {
            Interval.MINUTE_1: "1",
            Interval.MINUTE_5: "5",
            Interval.MINUTE_15: "15",
            Interval.MINUTE_30: "30",
            Interval.MINUTE_60: "60",
            Interval.DAY_1: "daily",
            Interval.WEEK_1: "weekly",
            Interval.MONTH_1: "monthly",
        }

        try:
            return mapping[interval]

        except KeyError:
            raise ValueError(f"AkShare 不支持的 K 线周期：{interval}")

    # ==========================================================
    # DataFrame / Row 工具
    # ==========================================================

    @staticmethod
    def _get_value(
        row: Any,
        column: str,
        default: Any = None,
    ) -> Any:
        """
        安全读取字段。
        """

        try:
            value = row[column]

            if value is None:
                return default

            return value

        except (
            KeyError,
            TypeError,
            IndexError,
        ):
            return default

    @classmethod
    def _get_float(
        cls,
        row: Any,
        column: str,
        default: Optional[float] = None,
    ) -> Optional[float]:
        """
        安全读取浮点数。
        """

        value = cls._get_value(
            row,
            column,
            default,
        )

        return cls._to_float(
            value,
            default,
        )

    @staticmethod
    def _to_float(
        value: Any,
        default: Optional[float] = None,
    ) -> Optional[float]:
        """
        转换成 float。
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

    @staticmethod
    def _parse_datetime(
        value: Any,
    ) -> datetime:
        """
        转换时间。
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

        return datetime.fromisoformat(str(value))

    # ==========================================================
    # 状态
    # ==========================================================

    def _ensure_started(self) -> None:
        """
        确保数据源已经启动。
        """

        if not self._started:
            raise RuntimeError(
                "AkShare 数据源尚未启动，" "请先调用 DataManager.start()"
            )


def main() -> None:
    """
    AkShare 网关测试。
    """

    symbol = "600519"

    gateway = AkShareGateway()

    try:
        print()
        print("AkShare Gateway Test")

        # ------------------------------------------------------
        # 1. 登录
        # ------------------------------------------------------

        print()
        print("[1] 登录")

        if not gateway.login():
            print("❌ 登录失败")
            return

        print("✅ 登录成功")

        # ------------------------------------------------------
        # 2. 健康检查
        # ------------------------------------------------------

        print()
        print("[2] 健康检查")

        print("✅ 正常" if gateway.health_check() else "❌ 异常")

        # ------------------------------------------------------
        # 3. 股票
        # ------------------------------------------------------

        print()
        print(f"[3] 股票信息: {symbol}")

        stock = gateway.fetch_basic_info(symbol)

        print(stock)

        # ------------------------------------------------------
        # 4. Quote
        # ------------------------------------------------------

        print()
        print(f"[4] 最新行情: {symbol}")

        quote = gateway.fetch_quote(symbol)

        print(quote)

        # ------------------------------------------------------
        # 5. K 线
        # ------------------------------------------------------

        print()
        print(f"[5] K 线: {symbol}")

        klines = gateway.fetch_kline(
            symbol=symbol,
            interval=Interval.DAY_1,
            limit=10,
        )

        print(f"获取 {len(klines)} 条 K 线")

        for item in klines:
            print(item)

        # ------------------------------------------------------
        # 6. 财务
        # ------------------------------------------------------

        print()
        print(f"[6] 财务: {symbol}")

        financial = gateway.fetch_financial(symbol)

        print(financial)

        # ------------------------------------------------------
        # 7. 估值
        # ------------------------------------------------------

        print()
        print(f"[7] 估值: {symbol}")

        valuation = gateway.fetch_valuation(symbol)

        print(valuation)

        print()
        print("✅ AkShare Gateway 测试完成")

    except KeyboardInterrupt:
        print()
        print("⚠️ 用户中断")

    except Exception as exc:
        print()
        print(f"❌ 测试失败: {exc}")

        import traceback

        traceback.print_exc()

    finally:
        gateway.logout()


if __name__ == "__main__":
    main()
