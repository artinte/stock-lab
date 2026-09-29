from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(slots=True)
class Quote:
    """
    股票最新行情快照。

    Quote 表示股票在某一个时间点的市场行情状态。

    主要包括：

        - 最新价格
        - 开盘 / 最高 / 最低 / 昨收
        - 涨跌 / 涨跌幅 / 振幅
        - 成交量 / 成交额
        - 成交均价
        - 换手率 / 量比
        - 总市值 / 流通市值
        - 涨停价 / 跌停价
        - 交易状态
        - 数据来源

    不包含：

        - PE / PB / PS 等估值数据
        - 总股本 / 流通股本等基础数据
        - 财务报表数据
        - 技术指标
        - AI 分析结果

    数据来源可以是：

        - AmazingData / 银河
        - AkShare
        - TDX
        - 东方财富
        - 其他行情数据源

    所有数据源最终统一转换为 Quote。
    """

    # ==========================================================
    # 基础信息
    # ==========================================================

    symbol: str
    """
    股票代码。

    例如：

        600519.SH
        000001.SZ
        300750.SZ
    """

    name: Optional[str] = None
    """
    股票名称。

    例如：

        贵州茅台
        平安银行
        宁德时代
    """

    timestamp: Optional[datetime] = None
    """
    行情时间。

    表示这条行情快照对应的时间。
    """

    source: Optional[str] = None
    """
    数据来源代码。

    例如：

        yinhe
        akshare
        tdx
        eastmoney
    """

    currency: Optional[str] = None
    """
    货币。

    例如：

        CNY
        HKD
        USD
    """

    # ==========================================================
    # 价格
    # ==========================================================

    last_price: Optional[float] = None
    """
    最新价 / 当前价格。
    """

    previous_close: Optional[float] = None
    """
    昨收价。
    """

    open_price: Optional[float] = None
    """
    开盘价。
    """

    high_price: Optional[float] = None
    """
    最高价。
    """

    low_price: Optional[float] = None
    """
    最低价。
    """

    # ==========================================================
    # 涨跌
    # ==========================================================

    # 涨跌额。通常：最新价 - 昨收价
    change: Optional[float] = None

    # 涨跌幅，单位：%
    change_percent: Optional[float] = None

    amplitude: Optional[float] = None
    """
    振幅，单位：%。

    通常根据：

        (最高价 - 最低价) / 昨收价 × 100%
    """

    # ==========================================================
    # 成交
    # ==========================================================

    # 成交量
    volume: Optional[float] = None

    # 成交额
    amount: Optional[float] = None

    # 成交均价
    average_price: Optional[float] = None


    """
    换手率，单位：%。

    例如：

        0.1981
        5.32
    """
    turnover: Optional[float] = None

    # 量比
    volume_ratio: Optional[float] = None

    # 总市值
    market_cap: Optional[float] = None

    # 流通市值
    float_market_cap: Optional[float] = None

    # 涨停价
    limit_up: Optional[float] = None

    # 跌停价
    limit_down: Optional[float] = None

    # 市场状态
    status: Optional[str] = None
    """
    当前交易状态。

    例如：

        trading
        suspended
        closed

    不同数据源可以使用不同状态，
    Gateway 负责统一转换。
    """

    # ==========================================================
    # Display
    # ==========================================================

    def display(self) -> None:
        """
        平铺显示最新行情。

        显示规则：

            - 所有字段固定显示
            - 空值统一显示 "-"
            - 字段顺序固定
            - 时间统一为 YYYY-MM-DD HH:MM:SS
            - 百分比统一保留 4 位
            - 金额 / 市值使用千分位
            - 不输出不存在于 Quote 的其他数据
        """

        def fmt(value: object) -> str:
            """格式化普通字段。"""

            if value is None:
                return "-"

            if isinstance(value, str):
                value = value.strip()

                if not value:
                    return "-"

            return str(value)

        def fmt_datetime(
            value: Optional[datetime],
        ) -> str:
            """格式化时间。"""

            if value is None:
                return "-"

            return value.strftime("%Y-%m-%d %H:%M:%S")

        def fmt_price(
            value: Optional[float],
        ) -> str:
            """格式化价格。"""

            if value is None:
                return "-"

            return f"{value:,.4f}".rstrip("0").rstrip(".")

        def fmt_number(
            value: Optional[float],
        ) -> str:
            """格式化普通数值。"""

            if value is None:
                return "-"

            return f"{value:,.2f}"

        def fmt_percent(
            value: Optional[float],
        ) -> str:
            """格式化百分比。"""

            if value is None:
                return "-"

            return f"{value:.4f}%"

        def fmt_amount(
            value: Optional[float],
        ) -> str:
            """格式化金额。"""

            if value is None:
                return "-"

            return f"{value:,.2f}"

        def fmt_market_cap(
            value: Optional[float],
        ) -> str:
            """格式化市值。"""

            if value is None:
                return "-"

            if value >= 100_000_000_000:
                return f"{value / 100_000_000_000:.2f} 千亿"

            if value >= 100_000_000:
                return f"{value / 100_000_000:.2f} 亿"

            if value >= 10_000:
                return f"{value / 10_000:.2f} 万"

            return f"{value:,.2f}"

        # ======================================================
        # 基础信息
        # ======================================================

        print("✅ 最新行情")
        print(f"股票代码: {fmt(self.symbol)}")
        print(f"股票名称: {fmt(self.name)}")
        print(f"时间: {fmt_datetime(self.timestamp)}")
        print(f"数据来源: {fmt(self.source)}")
        print(f"货币: {fmt(self.currency)}")

        # ======================================================
        # 价格
        # ======================================================

        print(f"当前价格: {fmt_price(self.last_price)}")
        print(f"昨收: {fmt_price(self.previous_close)}")
        print(f"开盘: {fmt_price(self.open_price)}")
        print(f"最高: {fmt_price(self.high_price)}")
        print(f"最低: {fmt_price(self.low_price)}")

        # ======================================================
        # 涨跌
        # ======================================================

        print(f"涨跌: {fmt_price(self.change)}")
        print(f"涨跌幅: {fmt_percent(self.change_percent)}")
        print(f"振幅: {fmt_percent(self.amplitude)}")

        # ======================================================
        # 成交
        # ======================================================

        print(f"成交量: {fmt_number(self.volume)}")
        print(f"成交额: {fmt_amount(self.amount)}")
        print(f"成交均价: {fmt_price(self.average_price)}")
        print(f"换手率: {fmt_percent(self.turnover)}")
        print(f"量比: {fmt_number(self.volume_ratio)}")

        # ======================================================
        # 市值
        # ======================================================

        print(f"总市值: {fmt_market_cap(self.market_cap)}")
        print(f"流通市值: " f"{fmt_market_cap(self.float_market_cap)}")

        # ======================================================
        # 涨跌停
        # ======================================================

        print(f"涨停: {fmt_price(self.limit_up)}")
        print(f"跌停: {fmt_price(self.limit_down)}")

        # ======================================================
        # 状态
        # ======================================================

        print(f"状态: {fmt(self.status)}")
