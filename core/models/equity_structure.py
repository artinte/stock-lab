from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any

"""
股票股本结构数据模型。

用于描述上市公司的核心股本结构以及股本变动信息。

主要包括：

- 总股本
- 流通股本
- 流通 A 股
- 流通 B 股
- 限售股
- 股本变动日期
- 股本变动原因

该模型是 Stock Lab 的统一业务模型，
不直接对应某一个数据源的全部原始字段。

股份数量统一使用“万股”作为单位。
"""


@dataclass
class EquityStructure:
    """股票股本结构。"""

    # 基本信息
    symbol: str
    name: str | None = None

    # 核心股本
    total_shares: float | None = None
    float_shares: float | None = None

    # 流通结构
    float_a_shares: float | None = None
    float_b_shares: float | None = None

    # 限售结构
    restricted_shares: float | None = None

    # 股本变动
    announcement_date: date | None = None
    change_date: date | None = None
    ex_change_date: date | None = None
    change_reason: str | None = None

    # 数据来源
    source: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """转换为字典，用于缓存和序列化。"""

        return {
            "symbol": self.symbol,
            "name": self.name,
            "total_shares": self.total_shares,
            "float_shares": self.float_shares,
            "float_a_shares": self.float_a_shares,
            "float_b_shares": self.float_b_shares,
            "restricted_shares": self.restricted_shares,

            "announcement_date": (
                self.announcement_date.isoformat()
                if self.announcement_date
                else None
            ),
            "change_date": (
                self.change_date.isoformat()
                if self.change_date
                else None
            ),
            "ex_change_date": (
                self.ex_change_date.isoformat()
                if self.ex_change_date
                else None
            ),

            "change_reason": self.change_reason,
            "source": self.source,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EquityStructure:
        """从字典恢复股本结构对象。"""

        def parse_date(value: Any) -> date | None:
            if value is None:
                return None

            if isinstance(value, date):
                return value

            value = str(value).strip()

            if not value or value == "-":
                return None

            try:
                # 例如：20250331
                if len(value) == 8 and value.isdigit():
                    return date(
                        int(value[:4]),
                        int(value[4:6]),
                        int(value[6:8]),
                    )

                # 例如：2025-03-31
                return date.fromisoformat(value)

            except ValueError:
                return None

        return cls(
            symbol=data["symbol"],
            name=data.get("name"),
            total_shares=data.get("total_shares"),
            float_shares=data.get("float_shares"),
            float_a_shares=data.get("float_a_shares"),
            float_b_shares=data.get("float_b_shares"),
            restricted_shares=data.get("restricted_shares"),
            announcement_date=parse_date(data.get("announcement_date")),
            change_date=parse_date(data.get("change_date")),
            ex_change_date=parse_date(data.get("ex_change_date")),
            change_reason=data.get("change_reason"),
            source=data.get("source"),
        )

    def display(self) -> None:
        """以适合终端查看的形式显示股本结构。"""

        print(f"股票：{self.symbol}")

        if self.name:
            print(f"名称：{self.name}")

        print("\n【核心股本】")
        self._display_shares("总股本", self.total_shares)
        self._display_shares("流通股本", self.float_shares)

        if any(
            value is not None
            for value in (
                self.float_a_shares,
                self.float_b_shares,
            )
        ):
            print("\n【流通结构】")
            self._display_shares(
                "流通 A 股",
                self.float_a_shares,
            )
            self._display_shares(
                "流通 B 股",
                self.float_b_shares,
            )

        if self.restricted_shares is not None:
            print("\n【限售结构】")
            self._display_shares(
                "限售股",
                self.restricted_shares,
            )

        if any(
            value is not None
            for value in (
                self.announcement_date,
                self.change_date,
                self.ex_change_date,
                self.change_reason,
            )
        ):
            print("\n【股本变动】")

            if self.announcement_date:
                print(f"公告日期：{self.announcement_date}")

            if self.change_date:
                print(f"变动日期：{self.change_date}")

            if self.ex_change_date:
                print(f"除权日期：{self.ex_change_date}")

            if self.change_reason:
                print(f"变动原因：{self.change_reason}")

        if self.source:
            print("\n【数据来源】")
            print(f"数据来源：{self.source}")

        print("=" * 64)

    @staticmethod
    def _display_shares(
        label: str,
        value: float | None,
    ) -> None:
        """显示股数。"""

        if value is None:
            print(f"{label}：-")
            return

        print(f"{label}：{value:,.2f} 万股")
