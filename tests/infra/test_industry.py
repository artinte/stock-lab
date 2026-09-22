from __future__ import annotations

from infra.data_manager import DataManager
from core.models.industry import Industry

"""
行业信息测试。

运行：
python -m tests.gateways.test_industry
"""


def run_industry_test(
    manager: DataManager,
    symbol: str,
) -> None:
    print(f"【行业信息】{symbol}")

    try:
        industry: Industry | None = manager.get_industry_category(symbol)

        if industry is None:
            print("❌ 未获取到行业信息")
            return

        industry.display()

    except NotImplementedError:
        print("⚠️ 当前数据源暂未实现行业信息")
    except Exception as exc:
        print(f"❌ 获取行业信息失败：{exc}")


def run_industries_test(
    manager: DataManager,
    symbols: list[str],
) -> None:
    print(f"【批量行业信息】{symbols}")

    try:
        industries: list[Industry] = manager.get_industries(symbols)

        if not industries:
            print("❌ 未获取到行业信息")
            return

        for industry in industries:
            industry.display()

    except NotImplementedError:
        print("⚠️ 当前数据源暂未实现批量行业信息")
    except Exception as exc:
        print(f"❌ 批量获取行业信息失败：{exc}")


def main() -> None:
    provider_name = "yinhe"

    manager = DataManager(provider_name)

    try:
        manager.start()

        print("=" * 80)
        print(f"【行业信息测试】{provider_name}")
        print("=" * 80)

        # 单个股票
        run_industry_test(
            manager,
            "600519.SH",
        )

        print("=" * 80)

        # 批量股票
        run_industries_test(
            manager,
            [
                "600519.SH",
                "000001.SZ",
                "300750.SZ",
                "688981.SH",
            ],
        )

        print("=" * 80)

    finally:
        try:
            manager.stop()
            print("✅ 数据源已关闭")
        except Exception as exc:
            print(f"⚠️ 关闭数据源失败：{exc}")


if __name__ == "__main__":
    main()

