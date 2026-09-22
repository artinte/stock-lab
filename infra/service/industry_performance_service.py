from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path

from infra.mock.industry_performance_mock import (
    IndustryPerformanceMock,
)
from core.models.industry_performance import (
    IndustryPerformanceDaily,
    IndustryPerformancePeriod,
    IndustryPeriodPerformance,
)


class IndustryPerformanceService:
    """
    行业行情表现服务。

    当前版本使用 Mock 数据。
    后续接入 Gateway 后，只替换数据获取部分。

    主要职责：

    1. 获取行业每日表现
    2. JSON 缓存
    3. 查询历史数据
    4. 计算区间表现
    """

    def __init__(
        self,
        cache_dir: str | Path = "data/industry",
        provider: IndustryPerformanceMock | None = None,
    ):
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

        self.provider = provider or IndustryPerformanceMock()

    # =========================================================
    # Daily
    # =========================================================

    def get_daily_performance(
        self,
        date: str | None = None,
        level: int = 2,
        method: str = "weighted",
    ) -> IndustryPerformanceDaily:

        date = date or self._today()

        cache_file = self._daily_cache_file(
            date=date,
            level=level,
            method=method,
        )

        if cache_file.exists():
            return self._load_daily(cache_file)

        industries = self.provider.get_daily(
            date=date,
            level=level,
            method=method,
        )

        result = IndustryPerformanceDaily(
            date=date,
            level=level,
            method=method,
            industries=industries,
        )

        self._save_json(
            cache_file,
            result.to_dict(),
        )

        return result

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

        cache_file = self._period_cache_file(
            start_date=start_date,
            end_date=end_date,
            level=level,
            method=method,
        )

        if cache_file.exists():
            return self._load_period(cache_file)

        daily_results = self._get_daily_range(
            start_date=start_date,
            end_date=end_date,
            level=level,
            method=method,
        )

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

        self._save_json(
            cache_file,
            result.to_dict(),
        )

        return result

    # =========================================================
    # Internal · Daily
    # =========================================================

    def _get_daily_range(
        self,
        start_date: str,
        end_date: str,
        level: int,
        method: str,
    ) -> list[IndustryPerformanceDaily]:

        start = date.fromisoformat(start_date)
        end = date.fromisoformat(end_date)

        if start > end:
            raise ValueError("start_date 不能晚于 end_date")

        results = []

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

    def _calculate_period(
        self,
        daily_results: list[IndustryPerformanceDaily],
        start_date: str,
        end_date: str,
    ) -> list[IndustryPeriodPerformance]:

        if not daily_results:
            return []

        # code -> daily pct
        history: dict[
            str,
            list[float],
        ] = {}

        metadata = {}

        for daily in daily_results:

            for industry in daily.industries:

                history.setdefault(
                    industry.code,
                    [],
                ).append(industry.pct)

                metadata[industry.code] = industry

        result = []

        for code, values in history.items():

            # MVP 阶段先使用简单累计：
            #
            # (1+r1) * (1+r2) * ... - 1
            #
            # 后续如果有真实指数/成分股数据，
            # 可以替换成更加准确的区间计算。

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

    @staticmethod
    def _today() -> str:
        return date.today().isoformat()
