from __future__ import annotations

from core.models.quote import Quote
from infra.data_manager import DataManager

"""
股票行情数据测试。

本文件用于测试股票行情数据的获取能力，包括：

1. test_quote()
   测试获取单只股票行情。

2. test_quotes()
   测试批量获取多只股票行情。

测试链路：

    DataManager
        ↓
    StockManager
        ↓
    StockDataGateway
        ↓
    数据源（如 yinhe）
        ↓
    Quote

本文件测试的是完整的行情数据获取链路，
不是单独测试 Quote 模型。

运行：
python -m tests.infra.gateways.test_quote
"""


def test_quote(
    manager: DataManager,
    symbol: str,
) -> None:
    """测试获取单只股票行情。"""
    print(f"【单只股票行情测试】{symbol}")

    try:
        quote: Quote | None = manager.stock.get_quote(symbol)

        if quote is None:
            print("❌ 未获取到行情数据")
            return

        quote.display()

    except NotImplementedError:
        print("⚠️ 当前数据源暂未实现行情数据接口")

    except Exception as exc:
        print(f"❌ 获取股票行情失败：{exc}")


def test_quotes(
    manager: DataManager,
    symbols: list[str],
) -> None:
    """测试批量获取多只股票行情。"""
    print(f"【多只股票行情测试】共 {len(symbols)} 只")

    try:
        quotes:  list[Quote] = manager.stock.get_quotes(symbols)

        if not quotes:
            print("❌ 未获取到行情数据")
            return

        print(f"✅ 获取到 {len(quotes)} 只股票行情")

        for quote in quotes:
            quote.display()

    except NotImplementedError:
        print("⚠️ 当前数据源暂未实现批量行情数据接口")

    except Exception as exc:
        print(f"❌ 获取股票行情失败：{exc}")


def main() -> None:
    """运行股票行情测试。"""

    data = DataManager("yinhe")

    try:
        data.start()

        # 测试单只股票
        test_quote(
            manager=data,
            symbol="600519.SH",
        )

        print("\n" + "=" * 60 + "\n")

        # 测试多只股票
        test_quotes(
            manager=data,
            symbols=[
                "600519.SH",  # 贵州茅台
                "601398.SH",  # 工商银行
                "000001.SZ",  # 平安银行
                "300750.SZ",  # 宁德时代
            ],
        )

    finally:
        data.stop()
        print("✅ 数据源已关闭")


if __name__ == "__main__":
    main()