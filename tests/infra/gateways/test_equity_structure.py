from __future__ import annotations

from core.models.equity_structure import EquityStructure
from infra.data_manager import DataManager

"""
股票股权结构数据测试。

本文件用于测试股票股权结构数据的获取能力，包括：

1. test_equity_structure()
   测试获取单只股票的股权结构。

2. test_equity_structures()
   测试批量获取多只股票的股权结构。

测试链路：

    DataManager
        ↓
    StockManager
        ↓
    StockDataGateway
        ↓
    数据源（如 yinhe）
        ↓
    EquityStructure

本文件测试的是完整的股权结构数据获取链路，
不是单独测试 EquityStructure 模型。

运行：
python -m tests.infra.gateways.test_equity_structure
"""


def test_equity_structure(
    manager: DataManager,
    symbol: str,
) -> None:
    """测试获取单只股票的股权结构。"""
    print(f"【单只股票股权结构测试】{symbol}")

    try:
        structure: EquityStructure | None = manager.stock.get_equity_structure(symbol)

        if structure is None:
            print("❌ 未获取到股权结构数据")
            return

        structure.display()

    except NotImplementedError:
        print("⚠️ 当前数据源暂未实现股权结构数据接口")

    except Exception as exc:
        print(f"❌ 获取股票股权结构失败：{exc}")


def test_equity_structures(
    manager: DataManager,
    symbols: list[str],
) -> None:
    """测试批量获取多只股票的股权结构。"""
    print(f"【多只股票股权结构测试】共 {len(symbols)} 只")

    try:
        structures: list[EquityStructure] = manager.stock.get_equity_structures(symbols)

        if not structures:
            print("❌ 未获取到股权结构数据")
            return

        print(f"✅ 获取到 {len(structures)} 只股票的股权结构")

        for structure in structures:
            print()
            structure.display()

    except NotImplementedError:
        print("⚠️ 当前数据源暂未实现批量股权结构数据接口")

    except Exception as exc:
        print(f"❌ 获取股票股权结构失败：{exc}")


def main() -> None:
    """运行股票股权结构测试。"""

    data = DataManager("yinhe")

    try:
        data.start()

        # =========================
        # 单只股票
        # =========================

        test_equity_structure(
            manager=data,
            symbol="600519.SH",
        )

        print("\n" + "=" * 72 + "\n")

        # =========================
        # 多只股票
        # =========================

        test_equity_structures(
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
