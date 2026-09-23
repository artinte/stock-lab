from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from typing import Any

"""
股票股权结构数据模型。

用于描述上市公司的股权结构、股东信息及股份类别。

主要内容：

1. 股份结构
   - 总股本
   - 流通股本
   - 非流通股本
   - 股份类别

2. 股东结构
   - 股东名称
   - 股东类型
   - 持股数量
   - 持股比例
   - 股份性质
   - 股东排名

3. 控股关系
   - 控股股东
   - 实际控制人

4. 数据属性
   - 报告期
   - 公告日期
   - 数据来源

该模型主要用于统一不同数据源的股权结构数据，
不负责数据获取、计算或持久化。
"""


@dataclass(slots=True)
class Shareholder:
    """股东信息。"""

    name: str
    rank: int | None = None

    shareholder_type: str | None = None
    share_type: str | None = None

    shares: Decimal | None = None
    ownership_ratio: Decimal | None = None

    change_shares: Decimal | None = None
    change_ratio: Decimal | None = None

    is_controlling_shareholder: bool = False
    is_actual_controller: bool = False

    source: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """转换为字典。"""
        return {
            "name": self.name,
            "rank": self.rank,
            "shareholder_type": self.shareholder_type,
            "share_type": self.share_type,
            "shares": self.shares,
            "ownership_ratio": self.ownership_ratio,
            "change_shares": self.change_shares,
            "change_ratio": self.change_ratio,
            "is_controlling_shareholder": self.is_controlling_shareholder,
            "is_actual_controller": self.is_actual_controller,
            "source": self.source,
        }


@dataclass(slots=True)
class ShareClass:
    """股份类别。"""

    name: str
    shares: Decimal | None = None
    ownership_ratio: Decimal | None = None

    listed: bool = True
    tradable: bool = True

    description: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """转换为字典。"""
        return {
            "name": self.name,
            "shares": self.shares,
            "ownership_ratio": self.ownership_ratio,
            "listed": self.listed,
            "tradable": self.tradable,
            "description": self.description,
        }


@dataclass(slots=True)
class EquityStructure:
    """
    上市公司股权结构。

    一个 EquityStructure 对应一个股票在某个报告期的股权结构快照。
    """

    symbol: str
    name: str | None = None

    # =========================
    # 股本结构
    # =========================

    total_shares: Decimal | None = None
    float_shares: Decimal | None = None
    non_float_shares: Decimal | None = None

    # =========================
    # 股份类别
    # =========================

    share_classes: list[ShareClass] = field(default_factory=list)

    # =========================
    # 股东结构
    # =========================

    shareholders: list[Shareholder] = field(default_factory=list)

    # =========================
    # 控股关系
    # =========================

    controlling_shareholder: str | None = None
    actual_controller: str | None = None

    controlling_ratio: Decimal | None = None

    # =========================
    # 数据时间
    # =========================

    report_date: date | None = None
    announcement_date: date | None = None

    # =========================
    # 数据来源
    # =========================

    source: str | None = None

    updated_at: datetime | None = None

    # =========================
    # 基础方法
    # =========================

    def to_dict(self) -> dict[str, Any]:
        """转换为字典。"""
        return {
            "symbol": self.symbol,
            "name": self.name,
            "total_shares": self.total_shares,
            "float_shares": self.float_shares,
            "non_float_shares": self.non_float_shares,
            "share_classes": [item.to_dict() for item in self.share_classes],
            "shareholders": [item.to_dict() for item in self.shareholders],
            "controlling_shareholder": self.controlling_shareholder,
            "actual_controller": self.actual_controller,
            "controlling_ratio": self.controlling_ratio,
            "report_date": self.report_date,
            "announcement_date": self.announcement_date,
            "source": self.source,
            "updated_at": self.updated_at,
        }

    def display(self) -> None:
        """以适合终端查看的形式显示股权结构。"""

        print("=" * 72)
        print("股权结构")
        print("=" * 72)

        # -------------------------
        # 基本信息
        # -------------------------

        print(f"股票：{self.symbol}")

        if self.name:
            print(f"名称：{self.name}")

        if self.report_date:
            print(f"报告期：{self.report_date}")

        if self.announcement_date:
            print(f"公告日期：{self.announcement_date}")

        # -------------------------
        # 股本结构
        # -------------------------

        print("\n【股本结构】")

        self._display_value(
            "总股本",
            self.total_shares,
        )

        self._display_value(
            "流通股本",
            self.float_shares,
        )

        self._display_value(
            "非流通股本",
            self.non_float_shares,
        )

        # -------------------------
        # 控股关系
        # -------------------------

        if self.controlling_shareholder or self.actual_controller:
            print("\n【控股关系】")

            if self.controlling_shareholder:
                print(f"控股股东：{self.controlling_shareholder}")

            if self.controlling_ratio is not None:
                print(f"控股比例：" f"{self._format_percent(self.controlling_ratio)}")

            if self.actual_controller:
                print(f"实际控制人：{self.actual_controller}")

        # -------------------------
        # 股份类别
        # -------------------------

        if self.share_classes:
            print("\n【股份类别】")

            for item in self.share_classes:
                shares = self._format_number(item.shares)
                ratio = self._format_percent(item.ownership_ratio)

                print(f"{item.name:<16}" f"股数：{shares:<16}" f"占比：{ratio}")

        # -------------------------
        # 股东
        # -------------------------

        if self.shareholders:
            print("\n【主要股东】")

            for shareholder in self.shareholders:
                rank = (
                    f"{shareholder.rank:>2}" if shareholder.rank is not None else "--"
                )

                shares = self._format_number(shareholder.shares)

                ratio = self._format_percent(shareholder.ownership_ratio)

                print(
                    f"{rank}. "
                    f"{shareholder.name:<24}"
                    f"持股：{shares:<16}"
                    f"占比：{ratio}"
                )

        # -------------------------
        # 数据来源
        # -------------------------

        if self.source:
            print(f"\n数据来源：{self.source}")

        if self.updated_at:
            print(f"更新时间：{self.updated_at}")

        print("=" * 72)

    @staticmethod
    def _format_number(
        value: Decimal | None,
    ) -> str:
        """格式化数值。"""
        if value is None:
            return "-"

        return f"{value:,.0f}"

    @staticmethod
    def _format_percent(
        value: Decimal | None,
    ) -> str:
        """格式化百分比。"""
        if value is None:
            return "-"

        return f"{value:.2f}%"

    @staticmethod
    def _display_value(
        label: str,
        value: Decimal | None,
    ) -> None:
        """显示股本字段。"""
        print(f"{label}：" f"{EquityStructure._format_number(value)}")
