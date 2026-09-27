from __future__ import annotations

from datetime import datetime, timedelta

from common.constants import Interval
from core.models.stock.kline import Kline
from infra.data_manager import DataManager

"""
K 线数据测试。

运行：
python -m tests.infra.gateways.stock.test_kline
"""


def run_kline_test(
    manager: DataManager,
    symbol: str,
) -> None:
    print(f"【股票 K 线】{symbol}")

    now = datetime.now()

    tests = [
        (
            "日 K",
            Interval.DAY_1,
            now - timedelta(days=180),
            now,
        ),
        (
            "5分钟 K",
            Interval.MINUTE_5,
            now - timedelta(days=5),
            now,
        ),
    ]

    for name, interval, start_time, end_time in tests:
        print(f"  【{name}】")

        try:
            klines: list[Kline] = manager.stock.get_kline(
                symbol=symbol,
                interval=interval,
                start_time=start_time,
                end_time=end_time,
                limit=1000,
            )

            if not klines:
                print("  ❌ 未获取到 K 线数据")
                continue

            print(f"  ✅ 获取 K 线数量：{len(klines)}")
            print("  最新 K 线：")
            klines[-1].display()

        except NotImplementedError:
            print("  ⚠️ 当前数据源暂未实现 K 线")

        except Exception as exc:
            print(f"  ❌ 获取 K 线失败：{exc}")


def run_klines_test(
    manager: DataManager,
    symbols: list[str],
) -> None:
    print(f"【批量股票 K 线】{symbols}")

    now = datetime.now()

    tests = [
        (
            "日 K",
            Interval.DAY_1,
            now - timedelta(days=180),
            now,
        ),
        (
            "5分钟 K",
            Interval.MINUTE_5,
            now - timedelta(days=5),
            now,
        ),
    ]

    for name, interval, start_time, end_time in tests:
        print(f"  【批量{name}】")

        try:
            klines_map: dict[str, list[Kline]] = (
                manager.stock.get_klines(
                    symbols=symbols,
                    interval=interval,
                    start_time=start_time,
                    end_time=end_time,
                    limit=1000,
                )
            )

            if not klines_map:
                print("  ❌ 未获取到 K 线数据")
                continue

            print(f"  ✅ 获取股票数量：{len(klines_map)}")

            for symbol in symbols:
                klines = klines_map.get(symbol)

                if not klines:
                    print(f"  ❌ {symbol}：未获取 K 线")
                    continue

                print(
                    f"  ✅ {symbol}："
                    f"{len(klines)} 根 K 线"
                )

                print("  最新 K 线：")
                klines[-1].display()

        except NotImplementedError:
            print("  ⚠️ 当前数据源暂未实现批量 K 线")

        except Exception as exc:
            print(f"  ❌ 批量获取 K 线失败：{exc}")


def main() -> None:
    provider_name = "yinhe"
    manager = DataManager(provider_name)

    try:
        manager.start()

        print("=" * 80)
        print(f"【K 线数据测试】{provider_name}")
        print("=" * 80)

        print("【单个股票】")
        run_kline_test(
            manager,
            "600519.SH",
        )

        print("=" * 80)

        print("【多个股票】")
        run_klines_test(
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