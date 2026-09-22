from datetime import datetime, timedelta
from common.constants import Interval
from infra.data_manager import DataManager
from utils.stock_mapping import exchange_name

"""
股票数据网关测试程序。

本文件用于测试和验证不同股票数据源（Gateway）是否能够通过
DataManager 提供统一、正常的数据访问能力。

本程序不负责股票分析、技术指标计算或投资决策，只用于验证
数据访问层（Data Access Layer）的功能是否正常。

整体测试流程：

    测试程序
        │
        ▼
    DataManager
        │
        ▼
    GatewayRegistry
        │
        ▼
    StockDataGateway
        │
        ├── YinheGateway
        ├── AkShareGateway
        ├── TDXGateway
        └── 其他数据源
                │
                ▼
            第三方数据接口


主要测试内容：

1. 数据源创建

    通过 DataManager 创建指定的数据源：

        DataManager("yinhe")

    验证数据源是否能够正常初始化，并检查当前已经注册的
    数据源列表。

2. 数据源生命周期

    测试数据源的启动、健康检查和关闭：

        data.start()
        data.health_check()
        data.stop()

    用于验证 Gateway 是否能够正常建立和释放运行环境。

3. 股票基础信息

    测试：

        data.get_stock(symbol)

    验证数据源能否返回统一格式的股票基础信息，例如：

        - 股票代码
        - 股票名称
        - 所属行业
        - 所属市场

4. 最新行情

    测试：

        data.get_quote(symbol)

    验证数据源能否返回统一格式的实时行情，例如：

        - 最新价
        - 涨跌额
        - 涨跌幅
        - 开盘价
        - 最高价
        - 最低价
        - 成交量
        - 成交额
        - 换手率
        - 总市值

5. K 线数据

    测试：

        data.get_kline(...)

    当前主要测试日 K 线数据，并打印最近几条 K 线，
    用于确认：

        - K 线是否能够正常获取
        - 时间是否正确
        - OHLC 数据是否正确
        - 成交量是否正确

6. 估值数据

    测试：

        data.get_valuation(symbol)

    验证数据源能否返回统一格式的估值数据，例如：

        - 当前价格
        - 总市值
        - 流通市值
        - PE(TTM)
        - PE(动态)
        - PE(静态)
        - PB
        - PS

7. 批量行情

    测试：

        data.get_quotes(symbols)

    用于验证数据源是否支持一次获取多只股票的行情，
    同时验证批量接口返回的数据数量和基本字段是否正常。


异常处理：

本测试程序针对每个功能分别进行异常捕获。

如果某个数据源暂未实现某项功能，则通过
NotImplementedError 明确提示，而不会导致整个测试程序退出。

例如：

    ⚠️ 当前数据源暂未实现股票基础信息

如果接口调用过程中发生其他异常，则打印错误信息，
方便定位具体 Gateway 的实现问题。


与 DataManager 的关系：

本文件不直接调用具体数据源的 SDK 或接口。

推荐的数据访问结构为：

    Test
      │
      ▼
    DataManager
      │
      ▼
    GatewayRegistry
      │
      ▼
    StockDataGateway
      │
      ▼
    具体 Gateway
      │
      ▼
    第三方数据源


因此，本文件测试的重点是：

    “不同 Gateway 是否遵循统一接口并能够正常工作”


与指标分析模块的区别：

本文件不会计算：

    - MA
    - MACD
    - RSI
    - KDJ
    - Bollinger Bands
    - Williams

这些功能属于 indicators 模块。

同样，本文件不会进行：

    - PE 深度分析
    - 股票评分
    - 投资逻辑分析
    - AI 分析

这些功能属于 analysis 或上层业务模块。


主要测试入口：

    main()

单个数据源测试：

    test_provider(
        provider_name,
        symbol,
    )

批量行情测试：

    test_batch_quotes(
        provider_name,
        symbols,
    )


使用示例：

    python -m tests.test_providers

程序会依次：

    1. 显示已经注册的数据源
    2. 测试指定数据源是否可以启动
    3. 检查数据源健康状态
    4. 获取股票基础信息
    5. 获取最新行情
    6. 获取 K 线数据
    7. 获取估值数据
    8. 测试批量行情
    9. 关闭数据源


设计目标：

本文件属于项目的数据访问层测试工具。

通过统一测试入口，可以在新增或修改 Gateway 后快速验证：

    Gateway
       ↓
    是否成功注册
       ↓
    是否可以启动
       ↓
    是否可以正常获取数据
       ↓
    返回的数据是否符合统一 Model
       ↓
    是否可以正常关闭

从而避免具体数据源的修改影响 DataManager
以及上层股票分析模块。
"""


def print_separator(title: str = "") -> None:
    print()
    print("=" * 72)

    if title:
        print(f"  {title}")

    print("=" * 72)


def test_provider(
    provider_name: str,
    symbol: str,
) -> None:

    print_separator(f"测试数据源：{provider_name}")

    try:
        data = DataManager(provider_name)

        data.start()

        print(f"数据源：{data.provider}")
        print(f"可用数据源：" f"{', '.join(data.available_providers())}")

    except Exception as exc:
        print(f"❌ 创建数据源失败：{exc}")
        return

    print()
    print("正在检查数据源...")

    try:
        if data.health_check():
            print("✅ 数据源可用")
        else:
            print("❌ 数据源不可用")
            return

    except Exception as exc:
        print(f"❌ 数据源检查失败：{exc}")
        return

    try:
        print("正在获取股票基础信息...")

        stock = data.get_stock(symbol)
        stock.display()

    except NotImplementedError:
        print("⚠️ 当前数据源暂未实现股票基础信息")

    except Exception as exc:
        print(f"❌ 获取股票基础信息失败：{exc}")

    try:
        print()
        print("正在获取行业分类...")

        industry = data.get_industry_category(symbol)
        print(industry.display())

    except NotImplementedError:
        print("⚠️ 当前数据源暂未实现行业分类")

    except Exception as exc:
        print(f"❌ 获取行业分类失败：{exc}")

    try:
        print()
        print("正在获取最新行情...")

        quote = data.get_quote(symbol)
        quote.display()

    except NotImplementedError:
        print("⚠️ 当前数据源暂未实现最新行情")

    except Exception as exc:
        print(f"❌ 获取最新行情失败：{exc}")

    try:
        print()
        print("正在获取日 K 线...")

        klines = data.get_kline(
            symbol=symbol,
            interval=Interval.DAY_1,
            start_time=(datetime.now() - timedelta(days=365)),
            end_time=datetime.now(),
            limit=10,
        )

        print(f"✅ 获取到 {len(klines)} 条 K 线")

        for item in klines[-5:]:
            print(
                f"   {item.timestamp:%Y-%m-%d} "
                f"O:{item.open:.2f} "
                f"H:{item.high:.2f} "
                f"L:{item.low:.2f} "
                f"C:{item.close:.2f} "
                f"V:{item.volume}"
            )

    except NotImplementedError:
        print("⚠️ 当前数据源暂未实现 K 线")

    except Exception as exc:
        print(f"❌ 获取 K 线失败：{exc}")

    try:
        print()
        print("正在获取估值数据...")

        valuation = data.get_valuation(symbol)

        print("✅ 估值数据")
        print(f"   当前价格：{valuation.price}")
        print(f"   总市值：{valuation.market_cap}")
        print(f"   流通市值：" f"{valuation.circulating_market_cap}")
        print(f"   PE(TTM)：" f"{valuation.pe_ttm}")
        print(f"   PE(动态)：" f"{valuation.pe_dynamic}")
        print(f"   PE(静态)：" f"{valuation.pe_static}")
        print(f"   PB：{valuation.pb}")
        print(f"   PS：{valuation.ps_ttm}")

    except NotImplementedError:
        print("⚠️ 当前数据源暂未实现估值")

    except Exception as exc:
        print(f"❌ 获取估值失败：{exc}")

    try:
        print()
        print("正在获取财务数据...")

        financial = data.get_financial(symbol)

        if financial is None:
            print("❌ 未获取到财务数据")

        else:
            print("✅ 财务数据")

            print(f"   报告日期：" f"{financial.report_date}")

            print(f"   营业收入：" f"{financial.revenue}")

            print(f"   净利润：" f"{financial.net_profit}")

            print(f"   归母净利润：" f"{financial.net_profit_attributable}")

            print(f"   扣非净利润：" f"{financial.non_recurring_net_profit}")

            print(f"   EPS：" f"{financial.eps}")

            print(f"   每股净资产：" f"{financial.book_value_per_share}")

            print(f"   毛利率：" f"{financial.gross_margin}%")

            print(f"   净利率：" f"{financial.net_margin}%")

            print(f"   ROE：" f"{financial.roe}%")

            print(f"   资产负债率：" f"{financial.debt_to_asset_ratio}%")

            print(f"   流动比率：" f"{financial.current_ratio}%")

            print(f"   应收账款周转率：" f"{financial.receivable_turnover}")

            print(f"   存货周转率：" f"{financial.inventory_turnover}")

            print(f"   经营现金流：" f"{financial.operating_cash_flow}")

            print(f"   自由现金流：" f"{financial.free_cash_flow}")

            print(f"   数据来源：" f"{financial.source}")

    except NotImplementedError:
        print("⚠️ 当前数据源暂未实现财务数据")

    except Exception as exc:
        print(f"❌ 获取财务数据失败：{exc}")

    try:
        print()
        print("正在关闭数据源...")

        data.stop()

        print("✅ 数据源已关闭")

    except Exception as exc:
        print(f"⚠️ 关闭数据源失败：{exc}")


def test_batch_quotes(
    provider_name: str,
    symbols: list[str],
) -> None:

    print_separator(f"批量行情测试：{provider_name}")

    try:
        data = DataManager(provider_name)

        data.start()

        print(f"正在获取 {len(symbols)} 只股票...")

        quotes = data.get_quotes(symbols)

        print(f"✅ 返回 {len(quotes)} 条行情")

        for quote in quotes:
            print(
                f"   {quote.symbol:<12} "
                f"{quote.name or '-':<8} "
                f"{quote.price or 0:>10} "
                f"{quote.change_percent or 0:>8.2f}%"
            )

        data.stop()

    except Exception as exc:
        print(f"❌ 批量行情测试失败：{exc}")


def main() -> None:

    print_separator("Stock Analysis - Gateway Test")

    print("股票数据网关测试程序")

    print("用于验证不同数据源是否可以" "通过统一 DataManager 正常访问。")

    print()

    print("当前支持的数据源：")

    try:
        providers = DataManager.available_providers()

        for provider in providers:
            print(f"   • {provider}")

    except Exception as exc:
        print(f"❌ 获取数据源列表失败：{exc}")
        return

    # ==========================================================
    # 测试股票
    # ==========================================================

    symbol = "600519.SH"

    print()
    print(f"测试股票：{symbol}")

    # ==========================================================
    # 默认数据源
    # ==========================================================

    test_provider(
        "yinhe",
        symbol,
    )

    # ==========================================================
    # 批量行情
    # ==========================================================

    test_batch_quotes(
        "yinhe",
        [
            "600519.SH",
            "000001.SZ",
            "601318.SH",
        ],
    )

    # ==========================================================
    # 银河
    #
    # 如果本机已经配置银河环境，可以取消注释。
    # ==========================================================

    # test_provider(
    #     "yinhe",
    #     symbol,
    # )

    # ==========================================================
    # TDX
    #
    # 当前如果还没有实现 TDX，可以暂时不测试。
    # ==========================================================

    # test_provider(
    #     "tdx",
    #     symbol,
    # )

    print_separator("测试完成")


if __name__ == "__main__":
    main()
