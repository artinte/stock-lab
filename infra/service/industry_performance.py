"""
==============================================================================
模块名称 : 行业行情表现服务
功能描述 : 基于行业成分股行情计算行业表现，并进行 JSON 缓存。

支持模式：

    real
        使用 StockManager 获取真实股票行情。

    mock
        使用模拟股票行情计算行业表现。
        不访问真实行情接口，适合前端开发和接口联调。

    auto
        优先使用真实行情。
        真实行情失败或无数据时自动使用 Mock。
==============================================================================
"""

from __future__ import annotations

import json
import random
from datetime import date, timedelta
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from core.models.industry_performance import (
    IndustryPerformanceDaily,
    IndustryPerformancePeriod,
    IndustryPeriodPerformance,
)
from infra.data_manager import DataManager
from utils.stock_industry_classification import (
    get_all_industries,
    get_category_stocks,
)


class IndustryPerformanceService:
    """
    行业行情表现服务。

    主要职责：

    1. 获取中证行业分类
    2. 获取行业成分股
    3. 通过 StockManager 获取股票行情
    4. 计算行业每日涨跌幅
    5. JSON 缓存每日数据
    6. 查询历史数据
    7. 计算区间表现

    支持三种行情模式：

        real
            使用真实股票行情。

        mock
            使用模拟股票行情。

        auto
            真实行情失败后自动使用 Mock。

    数据链路：

        中证行业分类
              ↓
        get_all_industries()
              ↓
        industry.symbol
              ↓
        get_category_stocks()
              ↓
        股票代码
              ↓
        StockManager
              ↓
        股票行情
              ↓
        行业涨跌幅
              ↓
        JSON Cache

    注意：

        本 Service 不创建 DataManager。
        DataManager 由外部统一创建并注入。

        本 Service 只从 DataManager 获取 StockManager，
        与系统中的其他股票业务共享同一个 StockManager。
    """

    def __init__(
        self,
        manager: DataManager,
        cache_dir: str | Path = "data/industry",
        mode: str = "mock",
    ) -> None:
        """
        初始化行业行情表现服务。

        参数：
            manager:
                外部统一创建的 DataManager。

            cache_dir:
                行业行情 JSON 缓存目录。

            mode:
                行情数据模式：

                    real
                        使用真实行情。

                    mock
                        使用 Mock 行情。

                    auto
                        优先真实行情，失败后使用 Mock。
        """

        # =====================================================
        # DataManager / StockManager
        # =====================================================

        self.data_manager = manager

        # =====================================================
        # 行情模式
        # =====================================================

        mode = mode.strip().lower()

        if mode not in {
            "real",
            "mock",
            "auto",
        }:
            raise ValueError(
                f"无效的行业行情模式: {mode!r}，" "支持：real / mock / auto"
            )

        self.mode = mode

        # =====================================================
        # Cache
        # =====================================================

        self.cache_dir = Path(cache_dir)

        self.daily_dir = self.cache_dir / "daily"
        self.period_dir = self.cache_dir / "period"

        self.daily_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.period_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

    # =========================================================
    # Industry
    # =========================================================

    def get_industries(
        self,
        level: int = 2,
    ):
        """
        获取指定层级的全部行业。
        """

        return get_all_industries(level)

    def get_industry_stocks(
        self,
        category: str | int,
        level: int | None = None,
    ) -> list[str]:
        """
        获取指定行业的全部成分股。

        参数：
            category:
                行业代码或行业名称。

            level:
                行业层级。

        返回：
            股票代码列表。
        """

        return get_category_stocks(
            category,
            level=level,
        )

    # =========================================================
    # Daily
    # =========================================================

    def get_daily_performance(
        self,
        date: str | None = None,
        level: int = 2,
        method: str = "weighted",
        use_cached: bool = False,
    ) -> IndustryPerformanceDaily:
        """
        获取指定日期的行业表现。

        参数：
            date:
                日期，例如："2026-09-23"，不指定时使用今天。

            level:
                行业层级：1 - 2 - 3 - 4

            method:
                计算方式：
                    weighted 按总市值加权
                    equal 等权平均

        返回：
            IndustryPerformanceDaily
        """

        date = date or self._today()

        self._validate_method(method)

        cache_file = self._daily_cache_file(
            date=date,
            level=level,
            method=method,
        )

        # -----------------------------------------------------
        # 优先读取缓存
        # -----------------------------------------------------
        
        if use_cached and cache_file.exists():
            return self._load_daily(cache_file)

        # -----------------------------------------------------
        # 计算行业表现
        # -----------------------------------------------------

        industries = self._calculate_daily(
            level=level,
            method=method,
        )

        result = IndustryPerformanceDaily(
            date=date,
            level=level,
            method=method,
            industries=industries,
        )

        # -----------------------------------------------------
        # 保存缓存
        # -----------------------------------------------------

        self._save_json(
            cache_file,
            result.to_dict(),
        )

        return result

    # =========================================================
    # Daily Calculation
    # =========================================================

    def _calculate_daily(
        self,
        level: int,
        method: str,
    ) -> list[IndustryPeriodPerformance]:
        """
        计算行业每日表现。

        每个行业：

            1. 获取行业成分股
            2. 获取股票行情
            3. 提取股票涨跌幅
            4. 根据 method 计算行业涨跌幅
        """
        industries = get_all_industries(level)

        results: list[IndustryPeriodPerformance] = []

        for industry in industries:

            # -------------------------------------------------
            # 获取行业成分股
            # -------------------------------------------------
            stocks = get_category_stocks(
                industry.symbol,
                level=level,
            )
            if not stocks:
                continue

            # -------------------------------------------------
            # 获取股票行情
            # -------------------------------------------------

            quotes = self._fetch_quotes(stocks)
            if not quotes:
                continue

            # -------------------------------------------------
            # 计算行业涨跌幅
            # -------------------------------------------------

            pct = self._calculate_industry_pct(
                quotes=quotes,
                method=method,
            )

            if pct is None:
                continue

            # -------------------------------------------------
            # 创建行业表现对象
            # -------------------------------------------------

            results.append(
                IndustryPeriodPerformance(
                    code=industry.symbol,
                    name=industry.name,
                    level=level,
                    pct=pct,
                    start_date=None,
                    end_date=None,
                    parent_code=self._get_parent_code(
                        industry,
                        level,
                    ),
                )
            )

        return results

    # =========================================================
    # Quote
    # =========================================================

    def _fetch_quotes(
        self,
        stocks: list[str],
    ) -> list[Any]:
        """
        根据当前 mode 获取股票行情。

        real：
            使用真实 StockManager。

        mock：
            使用 Mock 行情。

        auto：
            优先真实行情，失败后使用 Mock。
        """

        if not stocks:
            return []

        # =====================================================
        # Mock
        # =====================================================

        if self.mode == "mock":
            return self._fetch_mock_quotes(stocks)

        # =====================================================
        # Real
        # =====================================================

        if self.mode == "real":
            return self.data_manager.stock.get_quotes(stocks)

        # =====================================================
        # Auto
        # =====================================================

        try:
            quotes = self.data_manager.stock.get_quotes(stocks)

            if quotes:
                return quotes

            print("[行业行情] 真实行情无数据，" "切换 Mock。")

        except Exception as e:

            print(f"[行业行情] 真实行情失败，" f"切换 Mock：{e}")

        return self._fetch_mock_quotes(stocks)


    # =========================================================
    # Mock Quote
    # =========================================================

    @staticmethod
    def _fetch_mock_quotes(
        stocks: list[str],
    ) -> list[Any]:
        """
        生成 Mock 股票行情。

        这里只生成行业计算所需要的两个字段：

            pct
                股票涨跌幅。

            market_cap
                股票总市值。

        不创建完整 Quote，
        因为行业表现计算并不需要其它字段。
        """

        quotes = []

        for symbol in stocks:

            # -------------------------------------------------
            # 模拟涨跌幅
            # -------------------------------------------------

            pct = random.uniform(
                -8.0,
                8.0,
            )

            # -------------------------------------------------
            # 模拟总市值
            #
            # 不同股票使用不同市值，
            # 让 weighted 模式产生实际权重差异。
            # -------------------------------------------------

            market_cap = random.uniform(
                5e9,
                500e9,
            )

            quotes.append(
                SimpleNamespace(
                    symbol=symbol,
                    pct=round(
                        pct,
                        2,
                    ),
                    market_cap=market_cap,
                )
            )

        return quotes

    # =========================================================
    # Industry Performance Calculation
    # =========================================================

    @classmethod
    def _calculate_industry_pct(
        cls,
        quotes: list[Any],
        method: str,
    ) -> float | None:
        """
        根据股票行情计算行业涨跌幅。

        weighted：
            按总市值加权。

        equal：
            等权平均。

        Quote.pct 使用百分比数值，例如：

            2.35
            -1.28

        而不是：

            0.0235
            -0.0128
        """

        if not quotes:
            return None

        valid_quotes: list[tuple[Any, float]] = []

        for quote in quotes:
            pct = cls._get_quote_pct(quote)

            if pct is None:
                continue

            valid_quotes.append(
                (
                    quote,
                    pct,
                )
            )

        if not valid_quotes:
            return None

        # =====================================================
        # 等权平均
        # =====================================================

        if method == "equal":

            total = sum(pct for _, pct in valid_quotes)

            return round(
                total / len(valid_quotes),
                2,
            )

        # =====================================================
        # 市值加权
        # =====================================================

        weighted_total = 0.0
        weight_total = 0.0

        for quote, pct in valid_quotes:

            market_cap = cls._get_market_cap(quote)

            if market_cap is None:
                continue

            if market_cap <= 0:
                continue

            weighted_total += pct * market_cap

            weight_total += market_cap

        # -----------------------------------------------------
        # 没有有效市值时回退等权
        # -----------------------------------------------------

        if weight_total <= 0:

            total = sum(pct for _, pct in valid_quotes)

            return round(
                total / len(valid_quotes),
                2,
            )

        return round(
            weighted_total / weight_total,
            2,
        )

    # =========================================================
    # Quote Helpers
    # =========================================================

    @staticmethod
    def _get_quote_pct(
        quote: Any,
    ) -> float | None:
        """
        获取股票涨跌幅。

        优先使用 pct。

        同时兼容其它可能的字段名称。
        """

        fields = (
            "pct",
            "change_pct",
            "change_percent",
            "percent",
            "change_rate",
        )

        for field in fields:

            value = getattr(
                quote,
                field,
                None,
            )

            if value is None:
                continue

            try:
                return float(value)

            except (
                TypeError,
                ValueError,
            ):
                continue

        return None

    @staticmethod
    def _get_market_cap(
        quote: Any,
    ) -> float | None:
        """
        获取股票总市值。

        兼容不同 Quote 字段名称。
        """

        fields = (
            "total_market_value",
            "market_cap",
            "total_mv",
            "market_value",
        )

        for field in fields:

            value = getattr(
                quote,
                field,
                None,
            )

            if value is None:
                continue

            try:
                return float(value)

            except (
                TypeError,
                ValueError,
            ):
                continue

        return None

    # =========================================================
    # Parent Industry
    # =========================================================

    @staticmethod
    def _get_parent_code(
        industry: Any,
        level: int,
    ) -> str | None:
        """
        获取行业父级代码。

        如果 Industry 模型已经提供 parent_code，
        则直接使用。

        当前 Industry 查询函数如果没有提供父级代码，
        则返回 None。
        """

        parent_code = getattr(
            industry,
            "parent_code",
            None,
        )

        if parent_code:
            return parent_code

        return None

    # =========================================================
    # Period
    # =========================================================

    def get_period_performance(
        self,
        start_date: str,
        end_date: str,
        level: int = 2,
        method: str = "weighted",
    ) -> IndustryPerformancePeriod:
        """
        获取指定时间区间的行业表现。

        区间表现通过每日涨跌幅复合计算。
        """

        self._validate_method(method)

        cache_file = self._period_cache_file(
            start_date=start_date,
            end_date=end_date,
            level=level,
            method=method,
        )

        # -----------------------------------------------------
        # 优先读取缓存
        # -----------------------------------------------------

        if cache_file.exists():

            return self._load_period(cache_file)

        # -----------------------------------------------------
        # 获取每日数据
        # -----------------------------------------------------

        daily_results = self._get_daily_range(
            start_date=start_date,
            end_date=end_date,
            level=level,
            method=method,
        )

        # -----------------------------------------------------
        # 计算区间表现
        # -----------------------------------------------------

        industries = self._calculate_period(
            daily_results=daily_results,
            start_date=start_date,
            end_date=end_date,
        )

        result = IndustryPerformancePeriod(
            start_date=start_date,
            end_date=end_date,
            level=level,
            method=method,
            industries=industries,
        )

        # -----------------------------------------------------
        # 保存缓存
        # -----------------------------------------------------

        self._save_json(
            cache_file,
            result.to_dict(),
        )

        return result

    # =========================================================
    # Internal · Daily Range
    # =========================================================

    def _get_daily_range(
        self,
        start_date: str,
        end_date: str,
        level: int,
        method: str,
    ) -> list[IndustryPerformanceDaily]:
        """
        获取指定日期范围内的每日行业表现。
        """

        start = date.fromisoformat(start_date)

        end = date.fromisoformat(end_date)

        if start > end:

            raise ValueError("start_date 不能晚于 end_date")

        results: list[IndustryPerformanceDaily] = []

        current = start

        while current <= end:

            current_date = current.isoformat()

            results.append(
                self.get_daily_performance(
                    date=current_date,
                    level=level,
                    method=method,
                )
            )

            current += timedelta(days=1)

        return results

    # =========================================================
    # Internal · Period Calculation
    # =========================================================

    @staticmethod
    def _calculate_period(
        daily_results: list[IndustryPerformanceDaily],
        start_date: str,
        end_date: str,
    ) -> list[IndustryPeriodPerformance]:
        """
        根据每日涨跌幅计算区间累计表现。
        """

        if not daily_results:
            return []

        # -----------------------------------------------------
        # code -> 每日涨跌幅
        # -----------------------------------------------------

        history: dict[
            str,
            list[float],
        ] = {}

        # -----------------------------------------------------
        # code -> 行业元数据
        # -----------------------------------------------------

        metadata: dict[
            str,
            Any,
        ] = {}

        for daily in daily_results:

            for industry in daily.industries:

                history.setdefault(
                    industry.code,
                    [],
                ).append(industry.pct)

                metadata[industry.code] = industry

        result: list[IndustryPeriodPerformance] = []

        # -----------------------------------------------------
        # 计算累计收益
        # -----------------------------------------------------

        for code, values in history.items():

            total = 1.0

            for pct in values:

                total *= 1 + pct / 100

            total_pct = round(
                (total - 1) * 100,
                2,
            )

            industry = metadata[code]

            result.append(
                IndustryPeriodPerformance(
                    code=industry.code,
                    name=industry.name,
                    level=industry.level,
                    pct=total_pct,
                    start_date=start_date,
                    end_date=end_date,
                    parent_code=industry.parent_code,
                )
            )

        # -----------------------------------------------------
        # 按涨跌幅排序
        # -----------------------------------------------------

        result.sort(
            key=lambda item: item.pct,
            reverse=True,
        )

        return result

    # =========================================================
    # Cache
    # =========================================================

    def _daily_cache_file(
        self,
        date: str,
        level: int,
        method: str,
    ) -> Path:

        return self.daily_dir / f"{date}_level{level}_{method}.json"

    def _period_cache_file(
        self,
        start_date: str,
        end_date: str,
        level: int,
        method: str,
    ) -> Path:

        return self.period_dir / (
            f"{start_date}_{end_date}" f"_level{level}_{method}.json"
        )

    def _load_daily(
        self,
        path: Path,
    ) -> IndustryPerformanceDaily:
        print(f"[行业行情] 加载每日缓存: {path}")
        with path.open(
            "r",
            encoding="utf-8",
        ) as file:

            data = json.load(file)

        return IndustryPerformanceDaily.from_dict(data)

    def _load_period(
        self,
        path: Path,
    ) -> IndustryPerformancePeriod:

        with path.open(
            "r",
            encoding="utf-8",
        ) as file:

            data = json.load(file)

        industries = [
            IndustryPeriodPerformance(**item)
            for item in data.get(
                "industries",
                [],
            )
        ]

        return IndustryPerformancePeriod(
            start_date=data["start_date"],
            end_date=data["end_date"],
            level=data["level"],
            method=data["method"],
            industries=industries,
        )

    @staticmethod
    def _save_json(
        path: Path,
        data: dict,
    ) -> None:

        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with path.open(
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                data,
                file,
                ensure_ascii=False,
                indent=2,
            )

    # =========================================================
    # Validation
    # =========================================================

    @staticmethod
    def _validate_method(
        method: str,
    ) -> None:

        if method not in {
            "weighted",
            "equal",
        }:

            raise ValueError("method 必须是 'weighted' 或 'equal'")

    # =========================================================
    # Utility
    # =========================================================

    @staticmethod
    def _today() -> str:
        return date.today().isoformat()
