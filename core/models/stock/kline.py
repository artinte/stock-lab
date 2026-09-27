"""
模块名称：K 线数据模型

功能描述：
    定义 Stock Lab 统一的标准 K 线数据模型。

    不同数据源通过 Gateway 获取原始 K 线数据后，
    统一转换为 Kline 结构，供行情查询、K 线图表、
    技术分析、历史数据缓存等功能使用。

数据边界：
    本模块只负责定义标准 K 线数据结构，
    不负责数据源请求、数据清洗、K 线计算、
    复权处理或业务分析。

时间约定：
    timestamp 表示当前 K 线周期的开始时间。

    例如：
        5 分钟 K：09:30:00 表示 09:30 ~ 09:35。
        日 K：表示对应交易日的交易周期。

唯一标识：
    K 线的唯一标识由以下三个字段共同决定：

        symbol + interval + timestamp

    通过 key 属性生成稳定的唯一标识。
    相同证券、相同周期、相同时间的 K 线，
    无论何时生成，其 key 都保持一致。

数据序列化：
    提供 to_dict() 和 from_dict()，
    用于 JSON 缓存以及模型与字典之间的转换。
"""

from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from common.constants import Interval


@dataclass(slots=True)
class Kline:
    """
    标准 K 线数据模型。

    描述证券在指定时间周期内的 OHLCV 行情数据。
    不同数据源由 Gateway 统一转换为该结构。
    """

    # 标准证券代码，例如 600519.SH
    symbol: str

    # K 线周期
    interval: Interval

    # K 线时间（周期开始时间）
    timestamp: datetime

    # 当前周期开盘价
    open: float

    # 当前周期最高价
    high: float

    # 当前周期最低价
    low: float

    # 当前周期收盘价
    close: float

    # 当前周期成交量
    volume: float | None = None

    # 当前周期成交额
    amount: float | None = None

    @property
    def key(self) -> str:
        """
        返回 K 线唯一标识。

        唯一标识由证券代码、K 线周期和时间组成。
        """
        return (
            f"{self.symbol}_" f"{self.interval.value}_" f"{self.timestamp.isoformat()}"
        )

    def to_dict(self) -> dict[str, object]:
        """
        将 K 线数据转换为字典。
        """
        return {
            "key": self.key,
            "symbol": self.symbol,
            "interval": self.interval.value,
            "timestamp": self.timestamp.isoformat(),
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume": self.volume,
            "amount": self.amount,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> Kline:
        """
        从字典创建 K 线数据模型。
        """
        timestamp = data["timestamp"]

        if isinstance(timestamp, datetime):
            parsed_timestamp = timestamp
        else:
            parsed_timestamp = datetime.fromisoformat(str(timestamp))

        return cls(
            symbol=str(data["symbol"]),
            interval=Interval(data["interval"]),
            timestamp=parsed_timestamp,
            open=float(data["open"]),
            high=float(data["high"]),
            low=float(data["low"]),
            close=float(data["close"]),
            volume=(float(data["volume"]) if data.get("volume") is not None else None),
            amount=(float(data["amount"]) if data.get("amount") is not None else None),
        )

    def display(self) -> None:
        """
        打印 K 线数据。
        """
        print("✅ K线数据")
        print(f"  唯一标识：{self.key}")
        print(f"  证券代码：{self.symbol}")
        print(f"  K线周期：{self.interval.value}")
        print(f"  交易时间：{self.timestamp}")
        print(f"  开盘价：{self.open:.2f}")
        print(f"  最高价：{self.high:.2f}")
        print(f"  最低价：{self.low:.2f}")
        print(f"  收盘价：{self.close:.2f}")
        print(f"  成交量：{self.volume if self.volume is not None else '-'}")
        print(f"  成交额：{self.amount if self.amount is not None else '-'}")
