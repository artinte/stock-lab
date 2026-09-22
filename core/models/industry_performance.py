from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date
from typing import Any


@dataclass
class IndustryPerformance:
    """
    单个行业在某一天的行情表现。
    """

    code: str
    name: str
    level: int

    pct: float

    stocks: int
    up: int
    down: int
    flat: int

    parent_code: str | None = None

    amount: float | None = None
    market_cap: float | None = None
    float_market_cap: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
    ) -> "IndustryPerformance":
        return cls(
            code=data["code"],
            name=data["name"],
            level=data["level"],
            pct=data["pct"],
            stocks=data["stocks"],
            up=data["up"],
            down=data["down"],
            flat=data["flat"],
            parent_code=data.get("parent_code"),
            amount=data.get("amount"),
            market_cap=data.get("market_cap"),
            float_market_cap=data.get("float_market_cap"),
        )


@dataclass
class IndustryPerformanceDaily:
    """
    某一天的行业行情数据。
    """

    date: str
    level: int
    method: str

    industries: list[IndustryPerformance] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "date": self.date,
            "level": self.level,
            "method": self.method,
            "industries": [industry.to_dict() for industry in self.industries],
        }

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
    ) -> "IndustryPerformanceDaily":
        return cls(
            date=data["date"],
            level=data["level"],
            method=data["method"],
            industries=[
                IndustryPerformance.from_dict(item)
                for item in data.get("industries", [])
            ],
        )


@dataclass
class IndustryPeriodPerformance:
    """
    行业在一个时间区间内的表现。
    """

    code: str
    name: str
    level: int

    pct: float

    start_date: str
    end_date: str

    parent_code: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class IndustryPerformancePeriod:
    """
    某个时间区间的行业行情数据。
    """

    start_date: str
    end_date: str

    level: int
    method: str

    industries: list[IndustryPeriodPerformance] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "start_date": self.start_date,
            "end_date": self.end_date,
            "level": self.level,
            "method": self.method,
            "industries": [industry.to_dict() for industry in self.industries],
        }
