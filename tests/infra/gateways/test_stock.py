from __future__ import annotations

from infra.data_manager import DataManager
from core.models.stock import Stock

"""
股票基础信息测试。

运行：
python -m tests.infra.gateways.test_stock
"""


def run_stock_test(
    manager: DataManager,
    symbol: str,
) -> None:
    print(f"【股票基础信息】{symbol}")

    try:
        stock: Stock | None = manager.stock.get_stock(symbol)

        if stock is None:
            print("❌ 未获取到股票信息")
            return

        stock.display()

    except NotImplementedError:
        print("⚠️ 当前数据源暂未实现股票基础信息")
    except Exception as exc:
        print(f"❌ 获取股票基础信息失败：{exc}")


def run_stocks_test(
    manager: DataManager,
    symbols: list[str],
) -> None:
    print(f"【批量股票基础信息】{symbols}")

    try:
        stocks: list[Stock] = manager.stock.get_stocks(symbols)

        if not stocks:
            print("❌ 未获取到股票信息")
            return

        for stock in stocks:
            stock.display()

    except NotImplementedError:
        print("⚠️ 当前数据源暂未实现批量股票基础信息")
    except Exception as exc:
        print(f"❌ 批量获取股票基础信息失败：{exc}")


def main() -> None:
    provider_name = "yinhe"

    manager = DataManager(provider_name)

    try:
        manager.start()

        print("=" * 80)
        print(f"【股票基础信息测试】{provider_name}")
        print("=" * 80)

        # 单个股票
        run_stock_test(
            manager,
            "600519.SH",
        )

        print("=" * 80)

        # 批量股票
        run_stocks_test(
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
