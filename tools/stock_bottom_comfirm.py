from datetime import datetime, timedelta

import pandas
from matplotlib import pyplot as plt
from common.constants import Interval
from infra.data_manager import DataManager
from tools import watchlists
from tools.watchlists import WATCHLISTS
from utils.stock_industry_classification import get_stock_industry_category

"""
底部确认：从“接飞刀”到“顺风车”的逻辑重构
文章链接：https://artinte.github.io/stock-analysis/stock_bottom_comfirm.html

在投资的世界里，底部确认信号一直是投资者们追逐的热点话题。
它不仅关系到投资者的资金安全，更直接影响到投资回报率。
然而，市场上关于底部确认的讨论往往充斥着各种各样的观点和方法，让人眼花缭乱。
那么，什么是真正有效的底部确认信号呢？
本文将从“接飞刀”到“顺风车”的逻辑重构，深入探讨底部确认的核心要素和实战应用。

本脚本是为了配合文章《底部确认：从“接飞刀”到“顺风车”的逻辑重构》而编写的工具脚本。
它的主要功能是帮助投资者理解和应用文章中提到的底部确认信号的概念和方法。
通过这个脚本，投资者可以更好地识别市场中的底部确认信号，从而做出更明智的投资决策。

python -m tools.stock_bottom_comfirm
"""


STOCK_CODE = "000157"

plt.rcParams["font.sans-serif"] = [
    "SimHei",
    "Microsoft YaHei",
    "Arial Unicode MS",
]  # 适配 Windows/Mac/Linux
plt.rcParams["axes.unicode_minus"] = False  # 解决负号显示为方块的问题


# 计算 RSI 指标的函数
def calculate_rsi(data, window=14):
    delta = data.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)

    # 使用 RMA (Relative Moving Average) 算法，这是 RSI 的标准计算法
    avg_gain = gain.ewm(alpha=1 / window, min_periods=window, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / window, min_periods=window, adjust=False).mean()

    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def plot_stock_analysis(df, title_suffix=""):
    """
    通用的绘图复用函数
    :param df: 必须包含 'c', 'rsi', 'buy_signal' 列的 DataFrame
    """
    # 剔除 NaN 保证绘图连续性
    plot_df = df.dropna(subset=["rsi"])

    if plot_df.empty:
        print("数据量不足以计算 RSI，无法绘图。")
        return

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)

    # 1. 绘制价格曲线
    ax1.plot(
        plot_df.index,
        plot_df["c"],
        color="blue",
        marker="o",
        markersize=4,
        label="Price (Close)",
        alpha=0.6,
    )

    # 仅在价格图中标注买入信号点
    if "buy_signal" in plot_df.columns:
        signals = plot_df[plot_df["buy_signal"] == True]
        if not signals.empty:
            ax1.scatter(
                signals.index,
                signals["c"],
                color="red",
                marker="^",
                s=150,
                edgecolors="black",
                label="BUY SIGNAL",
                zorder=5,
            )

    ax1.set_title(f"{code} | {title_suffix}", fontsize=10)
    ax1.set_ylabel("Price")
    ax1.legend()
    ax1.grid(True, linestyle="--", alpha=0.5)

    # 2. 绘制 RSI 曲线（纯净版，不带标记）
    ax2.plot(plot_df.index, plot_df["rsi"], color="red", label="RSI (14)")
    ax2.axhline(30, color="green", linestyle="--", label="Oversold (30)")
    ax2.axhline(70, color="orange", linestyle="--", label="Overbought (70)")
    ax2.set_ylim(0, 100)
    ax2.set_ylabel("RSI Value")
    ax2.set_title("RSI Indicator (Bottom Confirmation)")
    ax2.legend()
    ax2.grid(True, linestyle="--", alpha=0.5)

    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    provider_name = "yinhe"
    manager = DataManager(provider_name)
    try:
        manager.start()

        for code in watchlists.all_symbols():
            basic_info = manager.stock.get_basic_info(code)
            print(f"正在分析 {code} ({basic_info.name}) 的数据...")
            # 1. 获取 K 线数据
            klines = manager.stock.get_kline(
                code,
                Interval.DAY_1,
                datetime.now() - timedelta(days=180),
                datetime.now(),
            )

            # 2. 特征工程 & 查杀 NaN
            df = pandas.DataFrame(
                [
                    {"o": k.open, "h": k.high, "l": k.low, "c": k.close, "v": k.volume}
                    for k in klines
                ]
            )

            # 【新增】本地快速检索行业
            industry_info = "未知行业"
            ic = get_stock_industry_category(code)
            industry_info = f"{ic.level_1} > {ic.level_2} > {ic.level_3} > {ic.level_4}"

            df["rsi"] = calculate_rsi(df["c"], 14)
            df["ma20"] = df["c"].rolling(window=20).mean()

            # 1. 跌幅背景：半年内（120天）最高点到最低点跌幅 > 30%
            # 计算滚动最高价
            df["h_6m"] = df["c"].rolling(window=120, min_periods=1).max()
            # 计算相对于最高点的跌幅 (最高 - 当前) / 当前 >= 30%
            df["max_drawdown_check"] = (df["h_6m"] - df["c"]) / df["c"] >= 0.30
            # 状态记忆：过去 60 天内只要达标过一次 30% 跌幅，背景就成立
            df["had_deep_drop"] = (
                df["max_drawdown_check"].rolling(window=60).max().astype(bool)
            )

            # 2. 探底素材：今天是否跌破 40
            df["today_is_below_40"] = df["rsi"] < 40

            # 3. 状态延伸：过去 30 天内，是否有任何一天跌破过 40
            df["in_bottom_area"] = (
                df["today_is_below_40"].rolling(window=30).max().astype(bool)
            )

            # 4. 顺风车条件：当前站上 20 日均线
            df["is_above_ma20"] = df["c"] > df["ma20"]

            # 5. 最终组合逻辑 (严格执行你的 RSI < 50 要求)
            df["buy_signal"] = (
                df["had_deep_drop"]  # 条件 A: 半年内跌得够深 (30%)
                & df["in_bottom_area"]  # 条件 B: 近期 RSI 探过底
                & df["is_above_ma20"]  # 条件 C: 今天站上 20 日线
                & (df["rsi"] < 50)  # 条件 D: 动能还未过热 (重点！)
                & (df["rsi"] > 40)  # 条件 E: 动能已在回暖
            )

            # 6. 获取 PE 数据
            valuation = manager.stock.get_valuation(code)
            if valuation and valuation.pe_ttm:
                print(
                    f"{code} ({basic_info.name}) 的当前 PE (TTM) 为: {valuation.pe_ttm}"
                )

                if  valuation.pe_ttm < 50:
                    plot_stock_analysis(df, f"{basic_info.name} ({industry_info})")
            else:
                print("未获取到 Valuation 数据")
    finally:
        try:
            manager.stop()
            print("✅ 数据源已关闭")
        except Exception as exc:
            print(f"⚠️ 关闭数据源失败：{exc}")
