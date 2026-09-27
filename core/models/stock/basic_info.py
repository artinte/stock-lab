"""
===============================================================================
模块名称：股票基础信息模型
模块职责：定义股票 / 证券的基础静态信息数据模型
===============================================================================

功能说明：
    本模块定义 BasicInfo 数据模型，用于描述一只证券自身的基础属性。

    这些信息主要来自股票基础资料接口，例如：

        - 股票代码
        - 股票名称
        - 上市板块
        - 交易所
        - 上市日期
        - 首次公开发行价格
        - 退市日期
        - 上市状态
        - 公司全称
        - 数据来源

数据边界：
    BasicInfo 只负责描述证券本身的基础属性，不负责以下业务数据：

        - 行业分类
        - 新闻资讯
        - 公告信息
        - 财务数据
        - 行情数据
        - K 线数据
        - 估值数据
        - 技术指标

字段说明：
    exchange：
        表示证券所属交易所，例如上海证券交易所、深圳证券交易所。

    market：
        表示证券所属上市板块，例如主板、创业板、科创板。

    listed_status：
        True  表示当前处于上市状态。
        False 表示当前不处于上市状态。
        None  表示上市状态未知。

数据流：
    DataSource
        ↓
    StockGateway
        ↓
    BasicInfo
        ↓
    StockManager
        ↓
    Service / Router

序列化：
    to_dict()
        BasicInfo → dict → JSON

    from_dict()
        dict → BasicInfo

设计原则：
    1. 模型只负责数据承载，不负责数据获取。
    2. 模型不依赖具体数据源实现。
    3. 可选字段使用 None 表示数据缺失或未知。
    4. to_dict() 输出适合 JSON 持久化。
    5. from_dict() 负责将缓存数据恢复为模型对象。
    6. 数据清洗和数据源适配由 Gateway / Service 层负责。
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from common.enums.exchange import Exchange
from utils.stock_mapping import exchange_name


@dataclass(slots=True)
class BasicInfo:
    """股票基础信息，描述证券本身的静态属性。"""

    # 股票代码，例如 600519.SH
    symbol: str

    # 股票简称，例如 贵州茅台
    name: str | None = None

    # 上市板块，例如 主板、科创板、创业板
    market: str | None = None

    # 交易所
    exchange: Exchange | None = None

    # 上市日期
    listing_date: date | None = None

    # 首次公开发行价格
    ipo_price: float | None = None

    # 退市日期
    delisting_date: date | None = None

    # 上市状态：True=在市，False=非在市，None=未知
    listed_status: bool | None = None

    # 公司全称
    company_name: str | None = None

    # 数据来源，例如 yinhe、akshare
    source: str | None = None

    def to_dict(self) -> dict[str, object]:
        """
        将股票基础信息转换为可 JSON 序列化的字典。

        处理规则：
            - Exchange 转换为对应的 value。
            - date 转换为 ISO 日期字符串。
            - None 保持为 None。
        """
        return {
            "symbol": self.symbol,
            "name": self.name,
            "market": self.market,
            "exchange": self.exchange.value if self.exchange else None,
            "listing_date": (
                self.listing_date.isoformat() if self.listing_date is not None else None
            ),
            "ipo_price": self.ipo_price,
            "delisting_date": (
                self.delisting_date.isoformat()
                if self.delisting_date is not None
                else None
            ),
            "listed_status": self.listed_status,
            "company_name": self.company_name,
            "source": self.source,
        }

    @classmethod
    def from_dict(cls, data: dict) -> BasicInfo:
        """
        从字典恢复股票基础信息模型。

        主要用于：
            - JSON 缓存读取
            - 本地数据恢复
            - API 数据转换

        对日期字段和交易所字段进行对应的类型转换。
        """
        listing_date = data.get("listing_date")
        if listing_date and listing_date != "-":
            listing_date = date.fromisoformat(listing_date)
        else:
            listing_date = None

        delisting_date = data.get("delisting_date")
        if delisting_date and delisting_date != "-":
            delisting_date = date.fromisoformat(delisting_date)
        else:
            delisting_date = None

        exchange = data.get("exchange")
        if exchange and exchange != "-":
            exchange = Exchange(exchange)
        else:
            exchange = None

        return cls(
            symbol=data.get("symbol", ""),
            name=data.get("name"),
            market=data.get("market"),
            exchange=exchange,
            listing_date=listing_date,
            ipo_price=data.get("ipo_price"),
            delisting_date=delisting_date,
            listed_status=data.get("listed_status"),
            company_name=data.get("company_name"),
            source=data.get("source"),
        )

    def display(self) -> None:
        """以适合控制台查看的格式打印股票基础信息。"""
        print("✅ 股票基础信息")
        print(f"  股票代码：{self.symbol}")
        print(f"  股票名称：{self.name or '-'}")
        print(f"  上市板块：{self.market or '-'}")
        print(f"  交易所：{exchange_name(self.exchange) or '-'}")
        print(
            f"  上市日期："
            f"{self.listing_date if self.listing_date is not None else '-'}"
        )
        print(
            f"  上市价格：" f"{self.ipo_price if self.ipo_price is not None else '-'}"
        )
        print(
            f"  退市日期："
            f"{self.delisting_date if self.delisting_date is not None else '-'}"
        )
        print(
            f"  上市状态："
            f"{self.listed_status if self.listed_status is not None else '-'}"
        )
        print(f"  公司全称：{self.company_name or '-'}")
        print(f"  数据来源：{self.source or '-'}")
