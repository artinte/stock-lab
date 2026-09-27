from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


from core.models.stock.basic_info import BasicInfo
from core.models.company import Company
from core.models.capital import Capital
from core.models.industry import Industry
from core.models.institution import InstitutionData
from core.models.news import News
from core.models.announcement import Announcement
from core.models.event import Event

from core.models.quote import Quote
from core.models.kline import Kline
from core.models.valuation import Valuation
from core.models.financial.financial import Financial


@dataclass(slots=True)
class StockCenter:
    """
    股票信息中心。

    用于聚合一只股票的所有信息。

    数据来源包括：

        数据网关:
            Quote
            Kline
            Financial
            Valuation

        基础数据:
            Stock
            Company
            Capital
            Industry

        爬虫:
            News
            Announcement

        AI分析:
            Event
            Investment Logic


    典型流程：

        输入股票代码

            ↓

        DataManager

            ↓

        多数据源获取

            ↓

        StockCenter

            ↓

        AI分析

            ↓

        投资报告
    """

    # ==========================================================
    # 股票标识
    # ==========================================================

    symbol: str

    name: Optional[str] = None

    # ==========================================================
    # 基础信息
    # ==========================================================

    stock: Optional[BasicInfo] = None

    company: Optional[Company] = None

    # ==========================================================
    # 股本结构
    # ==========================================================

    capital: Optional[Capital] = None

    # ==========================================================
    # 行业
    # ==========================================================

    industry: Optional[Industry] = None

    # ==========================================================
    # 行情
    # ==========================================================

    quote: Optional[Quote] = None

    klines: list[Kline] = field(default_factory=list)

    # ==========================================================
    # 财务
    # ==========================================================

    financial: Optional[Financial] = None

    valuation: Optional[Valuation] = None

    # ==========================================================
    # 机构
    # ==========================================================

    institutions: Optional[InstitutionData] = None

    # ==========================================================
    # 新闻公告事件
    # ==========================================================

    news: list[News] = field(default_factory=list)

    announcements: list[Announcement] = field(default_factory=list)

    events: list[Event] = field(default_factory=list)

    # ==========================================================
    # 技术分析
    # ==========================================================

    technical: Optional[dict] = None

    # ==========================================================
    # AI分析结果
    # ==========================================================

    fundamental_analysis: Optional[str] = None

    valuation_analysis: Optional[str] = None

    investment_logic: Optional[str] = None

    risk_analysis: Optional[str] = None

    # ==========================================================
    # 元数据
    # ==========================================================

    created_at: datetime = field(default_factory=datetime.now)

    updated_at: datetime = field(default_factory=datetime.now)

    extra: dict = field(default_factory=dict)

    # ==========================================================
    # 方法
    # ==========================================================

    def update_time(self):

        self.updated_at = datetime.now()

    def add_news(
        self,
        news: News,
    ):

        self.news.append(news)

        self.update_time()

    def add_event(
        self,
        event: Event,
    ):

        self.events.append(event)

        self.update_time()

    def add_announcement(
        self,
        announcement: Announcement,
    ):

        self.announcements.append(announcement)

        self.update_time()

    def summary(self) -> dict:
        """
        返回股票概要。

        方便：

            API
            Web
            CLI
            AI Prompt

        使用。
        """

        return {
            "symbol": self.symbol,
            "name": self.name,
            "price": self.quote.price if self.quote else None,
            "pe_ttm": self.valuation.pe_ttm if self.valuation else None,
            "market_cap": self.valuation.market_cap if self.valuation else None,
            "industry": self.industry.primary_industry if self.industry else None,
            "news_count": len(self.news),
            "event_count": len(self.events),
            "updated_at": self.updated_at.isoformat(),
        }
