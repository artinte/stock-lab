from __future__ import annotations

from infra.analysis.valuation_analyzer import ValuationAnalyzer
from infra.data_manager import DataManager

"""
股票估值分析测试。

运行：
python -m tests.analysis.test_valuation
"""


def run_valuation_test(
    manager: DataManager,
    symbol: str,
) -> None:
    """使用已有 DataManager 获取原始数据，并测试估值分析。"""

    print(f"【股票估值分析】{symbol}")

    try:
        valuation = manager.stock.get_valuation(symbol)
        if valuation is None:
            print("❌ 未生成估值数据")
            return
        print("✅ 估值分析完成")

        valuation.display()

    except NotImplementedError as exc:
        print(f"⚠️ 当前数据源暂未实现接口：{exc}")

    except Exception as exc:
        print(f"❌ 估值分析失败：{exc}")


def test_valuation(
    provider_name: str,
    symbol: str,
) -> None:
    """独立测试股票估值分析。"""

    print(f"【股票估值测试】{provider_name} / {symbol}")

    data: DataManager | None = None

    try:
        data = DataManager(provider_name)
        data.start()

        run_valuation_test(
            data,
            symbol,
        )

    finally:
        if data is not None:
            try:
                data.stop()
                print("✅ 数据源已关闭")
            except Exception as exc:
                print(f"⚠️ 关闭数据源失败：{exc}")


def main() -> None:
    test_valuation(
        provider_name="yinhe",
        symbol="600519.SH",
    )


if __name__ == "__main__":
    main()
