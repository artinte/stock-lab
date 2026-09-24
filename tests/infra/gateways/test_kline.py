from __future__ import annotations

from datetime import datetime, timedelta

from common.constants import Interval
from infra.data_manager import DataManager

"""
K线数据测试。

运行：

python -m tests.infra.gateways.test_kline
"""


def run_kline_test(
    manager: DataManager,
    symbol: str,
) -> None:
    """
    使用已有 DataManager 测试单个股票 K 线。

    注意：
        不负责 DataManager 的启动和关闭。

    用于：
        1. 独立测试
        2. 集成测试（多个模块共用一个 DataManager）
    """

    now = datetime.now()

    tests = [
        (
            "日 K",
            Interval.DAY_1,
            now - timedelta(days=365),
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
        print(f"【{name}】{symbol} / {interval.value}")

        try:
            klines = manager.stock.get_kline(
                symbol=symbol,
                interval=interval,
                start_time=start_time,
                end_time=end_time,
                limit=10,
            )

            if not klines:
                print("❌ 未获取到 K 线数据")
                continue

            print(f"✅ 获取 K 线数量：{len(klines)}")
            print()
            print("最近 5 根 K 线:")

            for kline in klines[-5:]:
                print(
                    f"  {kline.timestamp:%Y-%m-%d %H:%M:%S} "
                    f"O:{kline.open:.2f} "
                    f"H:{kline.high:.2f} "
                    f"L:{kline.low:.2f} "
                    f"C:{kline.close:.2f} "
                    f"V:{kline.volume}"
                )

            print()
            print("最新 K 线详情:")

            klines[-1].display()

        except NotImplementedError:
            print("⚠️ 当前数据源暂未实现 K 线")

        except Exception as exc:
            print(f"❌ 获取 K 线失败：{exc}")


def run_klines_test(
    manager: DataManager,
    symbols: list[str],
) -> None:
    """
    使用已有 DataManager 测试批量股票 K 线。

    注意：
        不负责 DataManager 的启动和关闭。
    """

    now = datetime.now()

    tests = [
        (
            "日 K",
            Interval.DAY_1,
            now - timedelta(days=365),
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
        print(f"【批量{name}】{len(symbols)} 只股票 / {interval.value}")

        try:
            klines_map = manager.stock.get_klines(
                symbols=symbols,
                interval=interval,
                start_time=start_time,
                end_time=end_time,
                limit=10,
            )

            if not klines_map:
                print("❌ 未获取到 K 线数据")
                continue

            print(f"✅ 获取股票数量：{len(klines_map)}")
            print()

            for symbol in symbols:
                klines = klines_map.get(symbol)

                if not klines:
                    print(f"  ❌ {symbol}：未获取到 K 线")
                    continue

                print(f"  ✅ {symbol}：" f"{len(klines)} 根 K 线")

                print("     最近一根：")

                kline = klines[-1]

                print(
                    f"       {kline.timestamp:%Y-%m-%d %H:%M:%S} "
                    f"O:{kline.open:.2f} "
                    f"H:{kline.high:.2f} "
                    f"L:{kline.low:.2f} "
                    f"C:{kline.close:.2f} "
                    f"V:{kline.volume}"
                )

            print()

        except NotImplementedError:
            print("⚠️ 当前数据源暂未实现批量 K 线")

        except Exception as exc:
            print(f"❌ 批量获取 K 线失败：{exc}")


def test_kline(
    provider_name: str,
    symbol: str,
    symbols: list[str] | None = None,
) -> None:
    """
    独立 K 线测试入口。

    单独运行时：
        创建 DataManager
        启动数据源
        测试单个 K 线
        测试批量 K 线
        关闭数据源
    """

    if symbols is None:
        symbols = [
            symbol,
            "000001.SZ",
            "300750.SZ",
            "688981.SH",
        ]

    print(f"【K线测试】{provider_name}")

    data: DataManager | None = None

    try:
        data = DataManager(provider_name)

        data.start()

        print()
        print("【单个 K 线】")

        run_kline_test(
            data,
            symbol,
        )

        print()
        print("【批量 K 线】")

        run_klines_test(
            data,
            symbols,
        )

    except Exception as exc:
        print(f"❌ K线测试失败：{exc}")

    finally:
        if data is not None:
            try:
                data.stop()
                print("✅ 数据源已关闭")

            except Exception as exc:
                print(f"⚠️ 关闭数据源失败：{exc}")


def main() -> None:
    test_kline(
        provider_name="yinhe",
        symbol="600519.SH",
    )


if __name__ == "__main__":
    main()
