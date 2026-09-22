from core.models.industry import Industry
from core.models.industry_profile import IndustryProfile
from utils.stock_industry_category import StockQueryResult, get_stock_industry_category


class IndustryService:
    """
    行业数据服务。

    负责：

        股票代码
            ↓
        行业分类

        行业分类
            ↓
        行业画像
    """

    def __init__(
        self,
        provider=None,
    ):
        self.provider = provider

    def get_industry_category(
        self,
        symbol: str,
    ) -> Industry:
        industry = get_stock_industry_category(symbol)
        return industry
    
    def get_industries(
        self,
        symbols: list[str],
    ) -> list[Industry]:
        industries: list[Industry] = []
        for symbol in symbols:
            industry = self.get_industry_category(symbol)
            if industry is not None:
                industries.append(industry)
        return industries

    def get_industry_profile(
        self,
        industry: Industry,
    ) -> IndustryProfile:
        pass
