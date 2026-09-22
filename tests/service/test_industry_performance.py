from infra.service.industry_performance_service import (
    IndustryPerformanceService,
)

service = IndustryPerformanceService()


# =========================================================
# 今日行业行情
# =========================================================

daily = service.get_daily_performance(
    date="2026-09-22",
    level=2,
    method="weighted",
)

print(f"\n{daily.date} " f"行业数量: {len(daily.industries)}")

for industry in daily.industries[:5]:

    print(
        industry.name,
        industry.pct,
        industry.up,
        industry.down,
    )


# =========================================================
# 区间行情
# =========================================================

period = service.get_period_performance(
    start_date="2026-09-01",
    end_date="2026-09-22",
    level=2,
    method="weighted",
)

print(f"\n{period.start_date}" f" ~ " f"{period.end_date}")

for industry in period.industries[:10]:

    print(
        industry.name,
        industry.pct,
    )
