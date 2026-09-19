from __future__ import annotations

from infra.data_manager import DataManager
from infra.service.stock_financial_service import StockFinancialService
from infra.service.youtube_service import YouTubeService


# ============================================================
# Runtime Services
# ============================================================

data: DataManager | None = None

financial_service: StockFinancialService | None = None

youtube_service: YouTubeService | None = None


# ============================================================
# Dependencies
# ============================================================

def require_data() -> DataManager:
    """
    获取已经启动的数据服务。
    """

    if data is None:
        raise RuntimeError("数据源尚未启动")

    return data


def require_financial_service() -> StockFinancialService:
    """
    获取已经启动的财务服务。
    """

    if financial_service is None:
        raise RuntimeError("财务服务尚未启动")

    return financial_service


def require_youtube() -> YouTubeService:
    """
    获取已经启动的 YouTube 服务。
    """

    if youtube_service is None:
        raise RuntimeError("YouTube 服务尚未启动")

    return youtube_service