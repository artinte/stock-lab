# -*- coding: utf-8 -*-

"""
行业行情表现服务测试。

测试内容：
    - 行业成分股
    - 每日行业行情
    - 等权行业行情
    - 市值加权行业行情
    - 区间行业行情
    - 行业行情缓存

使用真实数据源进行测试。

运行：
    python -m tests.infra.service.test_industry_performance
"""

from __future__ import annotations

from datetime import date, timedelta

from infra.data_manager import DataManager
from infra.service.industry_performance import IndustryPerformanceService


def run_industry_stocks_test(
    service: IndustryPerformanceService,
    category: str,
    level: int,
) -> None:
    """测试行业成分股。"""

    print(f"【行业成分股】{category}")

    try:
        stocks = service.get_industry_stocks(
            category,
            level=level,
        )

        print(f"股票数量: {len(stocks)}")
        print(f"前 10 只: {stocks[:10]}")

        if not stocks:
            print("❌ 未获取到行业成分股")
            return

        print("✅ 行业成分股获取成功")

    except Exception as exc:
        print(f"❌ 获取行业成分股失败：{exc}")


def run_daily_performance_test(
    service: IndustryPerformanceService,
    performance_date: str,
    level: int,
    method: str,
) -> None:
    """测试每日行业行情。"""

    print(
        f"【每日行业行情】" f"{performance_date} " f"level={level} " f"method={method}"
    )

    try:
        result = service.get_daily_performance(
            date=performance_date,
            level=level,
            method=method,
        )

        print(f"日期: {result.date}")
        print(f"行业级别: {result.level}")
        print(f"计算方式: {result.method}")
        print(f"行业数量: {len(result.industries)}")

        if not result.industries:
            print("❌ 未获取到行业行情")
            return

        print("\n前 10 个行业：")

        for industry in result.industries[:10]:
            print(
                f"{industry.code:<12}" f"{industry.name:<16}" f"{industry.pct:>8.2f}%"
            )

        print("✅ 每日行业行情获取成功")

    except Exception as exc:
        print(f"❌ 获取每日行业行情失败：{exc}")


def run_period_performance_test(
    service: IndustryPerformanceService,
    start_date: str,
    end_date: str,
    level: int,
    method: str,
) -> None:
    """测试区间行业行情。"""

    print(
        f"【区间行业行情】"
        f"{start_date} ~ {end_date} "
        f"level={level} "
        f"method={method}"
    )

    try:
        result = service.get_period_performance(
            start_date=start_date,
            end_date=end_date,
            level=level,
            method=method,
        )

        print(f"开始日期: {result.start_date}")
        print(f"结束日期: {result.end_date}")
        print(f"行业级别: {result.level}")
        print(f"计算方式: {result.method}")
        print(f"行业数量: {len(result.industries)}")

        if not result.industries:
            print("❌ 未获取到区间行业行情")
            return

        print("\n前 10 个行业：")

        for industry in result.industries[:10]:
            print(
                f"{industry.code:<12}" f"{industry.name:<16}" f"{industry.pct:>8.2f}%"
            )

        print("✅ 区间行业行情获取成功")

    except Exception as exc:
        print(f"❌ 获取区间行业行情失败：{exc}")


def run_cache_test(
    service: IndustryPerformanceService,
    performance_date: str,
    level: int,
    method: str,
) -> None:
    """测试行业行情缓存。"""

    print(
        f"【行业行情缓存】" f"{performance_date} " f"level={level} " f"method={method}"
    )

    try:
        cache_file = service._daily_cache_file(
            date=performance_date,
            level=level,
            method=method,
        )

        print(f"缓存文件: {cache_file}")

        if cache_file.exists():
            print("✅ 缓存文件已存在")
        else:
            print("⚠️ 缓存文件不存在，将生成缓存")

        result = service.get_daily_performance(
            date=performance_date,
            level=level,
            method=method,
        )

        if cache_file.exists():
            print(f"缓存状态正常，" f"行业数量: {len(result.industries)}")
        else:
            print("❌ 行情获取完成，但缓存文件不存在")

    except Exception as exc:
        print(f"❌ 行情缓存测试失败：{exc}")


def test_industry_performance(
    manager: DataManager,
) -> None:
    """
    行业行情表现服务测试。

    使用外部传入的 DataManager，
    不创建新的数据源连接。
    """

    service = IndustryPerformanceService(
        manager=manager,
        mode="real",
    )

    # ---------------------------------------------------------
    # 行业成分股
    # ---------------------------------------------------------

    run_industry_stocks_test(
        service,
        category="半导体",
        level=2,
    )

    # ---------------------------------------------------------
    # 每日行情
    # ---------------------------------------------------------

    performance_date = (date.today() - timedelta(days=1)).isoformat()

    run_daily_performance_test(
        service,
        performance_date=performance_date,
        level=2,
        method="weighted",
    )

    # ---------------------------------------------------------
    # 每日行情：等权
    # ---------------------------------------------------------

    run_daily_performance_test(
        service,
        performance_date=performance_date,
        level=2,
        method="equal",
    )

    # ---------------------------------------------------------
    # 区间行情
    # ---------------------------------------------------------

    end_date = date.today()
    start_date = end_date - timedelta(days=5)

    run_period_performance_test(
        service,
        start_date=start_date.isoformat(),
        end_date=end_date.isoformat(),
        level=2,
        method="weighted",
    )

    # ---------------------------------------------------------
    # Cache
    # ---------------------------------------------------------

    run_cache_test(
        service,
        performance_date=performance_date,
        level=2,
        method="weighted",
    )


def main() -> None:
    """测试入口。"""

    provider_name = "yinhe"

    manager = DataManager(provider_name)

    try:
        manager.start()

        print(f"【行业行情表现测试】{provider_name}")

        test_industry_performance(
            manager,
        )

    finally:
        try:
            manager.stop()
            print("✅ 数据源已关闭")
        except Exception as exc:
            print(f"⚠️ 关闭数据源失败：{exc}")


if __name__ == "__main__":
    main()
