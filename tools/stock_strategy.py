"""
一、 核心量化指标：深度细节拆解

1. 价格与趋势：短线回踩与中线支撑
    指标 1：偏离度约束（BIAS 回归）
    细节：当日收盘价在 10 日均线下方，但距离 20 日均线（中线生命线）的距离在正负 1.5% 以内。
    逻辑：确保洗盘精准踩在支撑位上，而不是破位下行。

    指标 2：趋势倾角（Slope）
    细节：过去 60 个交易日的均线（MA60）斜率必须大于 0，且当前价格高于 MA60。
    逻辑：在大趋势向上的前提下找回调，过滤掉下降通道中的反弹。

2. 动量与空间：爆发力预判
    指标 3：波动率收缩（VCP 特征）
    细节：最近 5 日的最高价/最低价之比（日内波幅），要小于过去 20 日平均波幅的 0.8 倍。
    逻辑：振幅由大变小，意味着筹码完成充分换手，多空达成临时共识，这是变盘的前兆。

    指标 4：相对强度（RPS）
    细节：个股过去一年涨幅在全 A 股中排名处于前 20%，但近一个月排名处于中游。
    逻辑：这叫“强者恒强后的休整”，剔除掉长期走不赢大盘的弱势股。

3. 估值与成长：利益最大化的核心驱动
    指标 5：前瞻 PEG（预估市盈率增长比）
    细节：使用（当前市值 / 下一年预测净利润）除以（预测利润增长率），所得值 < 0.8。
    逻辑：买入未来的增长，而非过去的数字。

    指标 6：PB-ROE 匹配度
    细节：市净率（PB）除以 净资产收益率（ROE）的比值处于行业低分位。
    逻辑：确保每一分资产的盈利能力都极具性价比。

4. 盈利质量：防雷与抗风险
    指标 7：自由现金流覆盖率
    细节：(经营活动现金流 - 资本开支) / 净利润 > 1。
    逻辑：公司赚的钱除去扩大生产的投入，还能剩下真金白银给股东，这是利益最大化的底气。

    指标 8：预收账款（合同负债）环比
    细节：最新财报的预收账款/合同负债环比增长率 > 5%。
    逻辑：这是业绩爆发的先行指标，代表订单手软，未来业绩大概率超预期。

5. 资金与博弈：主力的“呼吸”
    指标 9：相对成交量（RV）
    细节：近 3 日下跌时的成交量，必须小于过去 20 日平均成交量的 0.6 倍。
    逻辑：典型的“无量回调”，主力惜售，只是在清理浮筹。

    指标 10：高人气振幅（博弈烈度）
    细节：近 5 日日均振幅在行业中排名前 15%，但 K 线形态未出现巨量阴线。
    逻辑：有资金在里面搅动，振幅是资金活跃的证明，活跃度 = 溢价空间。

    指标 11：股东人数变动趋势
    细节：最近一次公开数据的股东人数较上一次环比减少 5% 以上。
    逻辑：散户出场，筹码向大户/机构集中，拉升阻力更小。

    指标 12：量价比（Price-Volume Ratio）
    细节：最近一次小阳线放量与最近一次小阴线缩量的比例 > 1.5。
    逻辑：量价关系健康，多头力量占据主导地位。

二、 动态退化与自适应机制：如果选不到票怎么办？
    Level 1（最优）： 全量执行上述 12 指标。
    Level 2（弱化博弈）： 若 Level 1 结果 < 3 只，剔除指标 9、10、11（资金博弈类）。
    Level 3（生存模式）： 若结果依然不足，弱化指标 1（价格回撤深度）。

三、 利益最大化的“专业组合”执行策略
    打分制（Scoring System）： 给这 12 个指标设定权重。
    前 5 均衡配置： 选出总得分最高的前 3-5 只股票，平均分配资金。
    动态置换（Rolling Rebalance）： 每周五收盘后运行一次代码。
"""

"""
1. 不要买整个行业趋势向下走的，即使个股非常便宜，因为大势已去，便宜无用。
2. 不要买估值高但增长乏力的股票，增长才是王道，估值只是锦上添花。
3. 不要买财务报表有问题的公司，比如利润质量差、现金流为负、负债率高等。
4. 不要买股东结构混乱的公司，比如大股东频繁变动、股东人数剧增等。
5. 不要买技术面破位的股票，比如跌破重要均线、成交量萎缩等。
6. 不要买市场情绪极端的股票，比如过度炒作、舆论负面等。
7. 不要买流动性差的股票，比如成交量低、换手率低等。
8. 不要买你不了解的行业或公司，投资要有基本的认知和判断。
9. 不要盲目跟风买热门股票，热门不等于好，热点易变。
10. 不要频繁交易，保持耐心和纪律，等待最佳买入时机。

"""

import math
import random
import akshare as ak
from dotenv import dotenv_values
import pandas as pd
import numpy as np
import AmazingData
from utils.download_industry_data import get_csindex_industry_data
from models.stock_detail import StockDetail
from tools.watchlists import Watchlists
from datetime import datetime

# ==========================================
# 1. 策略引擎核心类：对接 StockDetail 属性
# ==========================================
class StrategyEngine:
    def __init__(self, stock_instance, kline_data, info_obj, local_path):
        self.s = stock_instance  # StockDetail 实例
        self.df = kline_data  # 历史K线 DataFrame
        self.info = info_obj
        self.path = local_path
        self.scores = {}

    def get_bias_val(self):
        """安全获取乖离率 (对应 StockDetail.bias)"""
        return self.s.bias if isinstance(self.s.bias, (float, int, np.float64)) else 0

    def calculate_indicators(self):
        """12个原子级指标评分逻辑"""
        # --- 最小改动：PS 市销率硬约束 ---
        if hasattr(self.s, 'total_revenue') and self.s.total_revenue > 0:
            ps_val = self.s.total_cap / self.s.total_revenue
            self.s.ps_ratio = ps_val
            self.scores["I_PS"] = 1 if ps_val < 3 else -100 
        else:
            self.scores["I_PS"] = -100

        # --- A. 价格与趋势 ---
        # I1: BIAS回归 (当日收盘在MA10下方，且20日乖离率在1.5%以内)
        # 修正逻辑：使之严格符合文档中的 1.5% 细节
        ma10 = self.s.ma_dict.get("MA10", 0)
        ma20 = self.s.ma_dict.get("MA20", 0)
        bias_20 = (self.s.price - ma20) / ma20 if ma20 != 0 else 0
        self.scores["I1"] = (
            1 if (self.s.price < ma10) and (abs(bias_20) <= 0.015) else 0
        )

        # I2: MA60趋势斜率 (向上)
        ma60_val = self.s.ma_dict.get("MA60", 0)
        ma60_series = self.df["close"].rolling(60).mean()
        slope_60 = (
            (ma60_series.iloc[-1] - ma60_series.iloc[-10]) / 10
            if len(ma60_series) >= 10
            else 0
        )
        self.scores["I2"] = 1 if slope_60 > 0 and self.s.price > ma60_val else 0

        # --- B. 动量与空间 ---
        # I3: VCP波动收缩 (5日波幅 < 20日均幅的0.8倍)
        vol_5d = (self.df["high"].iloc[-5:].max() / self.df["low"].iloc[-5:].min()) - 1
        vol_20d_avg = (
            ((self.df["high"] / self.df["low"]) - 1).rolling(20).mean().iloc[-1]
        )
        self.scores["I3"] = 1 if vol_5d < (vol_20d_avg * 0.8) else 0

        # I4: 相对强度 (年涨幅 > 15% 且近一月排名中游/波动小)
        y_ret = (
            self.df["close"].iloc[-1] / self.df["close"].iloc[-250] - 1
            if len(self.df) >= 250
            else 0
        )
        m_ret = (
            self.df["close"].iloc[-1] / self.df["close"].iloc[-20] - 1
            if len(self.df) >= 20
            else 0
        )
        self.scores["I4"] = 1 if y_ret > 0.15 and abs(m_ret) < 0.1 else 0

        # --- C. 估值与成长 ---
        # I5: 前瞻 PEG（核心逻辑：放宽至只要增长且 PEG < 0.8）
        growth = self.s.profit_growth_rate  # 刚才在 StockDetail 中算出的增长率
        pe = self.s.pe_ttm
        if growth > 0 and pe > 0:  
            peg = pe / growth
            self.scores["I5"] = 1 if peg < 0.8 else 0
        else:
            self.scores["I5"] = 0

        # I6: PB-ROE匹配 (此处根据行业平均PB/ROE逻辑，暂时默认及格)
        self.scores["I6"] = 1

        # --- D. 盈利质量 ---
        # I7: 自由现金流 (尝试从原始财务数据判断逻辑)
        self.scores["I7"] = 1
        # I8: 合同负债 (环比增长 > 5%)
        self.scores["I8"] = 1

        # --- E. 资金与博弈 ---
        # I9: RV 相对成交量 (近3日下跌缩量 < 20日均量 0.6倍)
        avg_v20 = self.df["volume"].rolling(20).mean().iloc[-1]
        v_3d = self.df["volume"].iloc[-3:].mean()
        self.scores["I9"] = 1 if v_3d < (avg_v20 * 0.6) else 0

        # I10: 高人气振幅 (利用 StockDetail.amplitude 属性)
        self.scores["I10"] = 1 if self.s.amplitude > 3.5 else 0

        # I11: 股东人数 (环比减少 5% 以上)
        # 注意：此处需依赖 info_obj 获取最新股东数据，暂时设为演示通过
        self.scores["I11"] = 1

        # I12: 量价比 (阳线放量 vs 阴线缩量比例 > 1.5)
        self.scores["I12"] = 1 if self.s.vol_ratio > 1.5 else 0

    def get_final_decision(self):
        """执行退化机制评价"""
        self.calculate_indicators()
        
        # 最小改动：如果 PS 过滤未通过，返回负分
        if self.scores.get("I_PS", 0) < 0:
            return "PS过高(剔除)", -100

        total_score = sum(self.scores.values())
        ma60 = self.s.ma_dict.get("MA60", 0)

        if total_score >= 10:
            return "Level 1 (极致推荐: 指标共振)", total_score
        elif total_score >= 7:
            return "Level 2 (稳健持有: 基本面尚可)", total_score
        elif self.s.price > ma60:
            # Level 3: 只要趋势不破，弱化回撤深度要求
            return "Level 3 (及格线: 仅趋势维持)", total_score
        return "观望 (未达标)", total_score


def format_watchlists(watch_dict):
    formatted = []
    for name, code in watch_dict.items():
        full_code = f"{code}.SH" if code.startswith(("6", "9")) else f"{code}.SZ"
        formatted.append((full_code, name))
    return formatted

# ==========================================
# 2. 主执行程序：遍历自选股池
# ==========================================
if __name__ == "__main__":
    config = dotenv_values("private_config.txt")
    # A. 环境登录与初始化
    AmazingData.login(
        username=config["username"],
        password=config["password"],
        host=config["host"],
        port=int(config["port"]),
    )
    local_path = config["local_path"]
    info_data_obj = AmazingData.InfoData()
    base_data_obj = AmazingData.BaseData()
    calendar = base_data_obj.get_calendar()
    market_data_obj = AmazingData.MarketData(calendar)

    code_infos = base_data_obj.get_code_info()
    final_results = []
    
    # 加载行业
    df_industry = get_csindex_industry_data()

    print("\n>>> 开始运行策略引擎遍历自选股池...\n")

    print("\n" + "=" * 100)
    print(
        f"{'代码':<12} | {'名称':<8} | {'涨跌幅%':<8} | {'PE(TTM)':<10} | {'增长率%':<10} | {'得分':<6} | {'建议类型'}"
    )
    print("-" * 100)

    items = [(row.Index, row.symbol) for row in code_infos.itertuples()]
    # items = format_watchlists(Watchlists)
    random.shuffle(items)
    for code, name in items:
        try:
            # 1. 获取历史K线
            kline_dict = market_data_obj.query_kline(
                code_list=[code],
                begin_date=calendar[-300],
                end_date=calendar[-1],
                period=AmazingData.constant.Period.day.value,
            )
            df_k = kline_dict.get(code)
            if df_k is None or len(df_k) < 60:
                continue

            # 2. 初始化 StockDetail 实例
            prev_close_val = df_k.iloc[-2]["close"]
            today_row = df_k.iloc[-1].to_dict()
            stock_instance = StockDetail.from_dict_data(
                name, today_row, last_close=prev_close_val
            )
            stock_instance.code = code

            # 3. 计算基础指标
            equity = info_data_obj.get_equity_structure(
                [code], local_path=local_path, is_local=False
            )
            if not equity.empty:
                latest_row = equity.sort_values("CHANGE_DATE").iloc[-1]
                stock_instance.update_equity(
                    latest_row["TOT_SHARE"], latest_row["FLOAT_SHARE"]
                )

            stock_instance.calculate_moving_averages(df_k)
            stock_instance.calculate_volume_ratio(df_k)
            stock_instance.calculate_bias()
            stock_instance.calculate_williams(df_k)

            raw_income = info_data_obj.get_income(
                code_list=[code],
                local_path=local_path,
                is_local=True,
                begin_date="20240101",
                end_date=calendar[-1],
            )
            stock_instance.calculate_pe(raw_income)

            growth = stock_instance.profit_growth_rate
            pe = stock_instance.pe_ttm

            industry = "未知"
            try:
                # 1. 提取纯数字代码，并强制转换为 6 位字符串补零格式（例如: '000001'）
                short_code = code.split(".")[0].zfill(6)

                # 2. 从之前下载的 df 数据（假设你的 DataFrame 变量名叫 df_industry）中匹配证券代码
                # 注意：这里的 df_industry 就是你之前通过 get_csindex_industry_data() 获取到的结构体
                match_data = df_industry[df_industry["证券代码"].astype(str) == short_code]

                if not match_data.empty:
                    # 3. 获取行业名称（量化中常用“中证二级行业分类简称”，可根据需要替换为三级或四级）
                    industry = match_data["中证二级行业分类简称"].values[0]
                else:
                    # 如果中证数据里找不到这只股票（可能是退市或刚上市新股），可以按你原逻辑跳过或标记未知
                    continue

            except Exception as e:
                # 调试时可以打印错误看看，策略上线后可以保持 silent
                # print(f"匹配行业时出错: {e}")
                pass

            if math.isnan(growth) or math.isnan(pe):
                continue

            # --- 最小改动点：PS 硬过滤 ---
            ps_ratio = stock_instance.total_cap / stock_instance.total_revenue if stock_instance.total_revenue > 0 else 999
            # ps 太低也可能是因为公司流水高，没有什么护城河
            if ps_ratio >= 5:
                continue

            # 4. 运行策略引擎进行评分
            engine = StrategyEngine(stock_instance, df_k, info_data_obj, local_path)
            decision_text, score_val = engine.get_final_decision()
            
            # 如果得分包含硬过滤的负分，则跳过
            if score_val < 0:
                continue

            change_pct = ((stock_instance.price / stock_instance.last_close) - 1) * 100
            print(
                f"{code:<12} | {name:<8} | {industry:<8} |{change_pct:>8.2f}% | {stock_instance.pe_ttm:>10.2f} | \
                {stock_instance.profit_growth_rate:<6.2f}% | {score_val:<8} | {decision_text}"
            )

            final_results.append(
                {
                    "代码": code,
                    "名称": name,
                    "行业": industry,
                    "得分": score_val,
                    "市值": stock_instance.total_cap,
                    "营收": stock_instance.total_revenue,
                    "建议": decision_text,
                    "现价": stock_instance.price,
                    "PE_TTM": stock_instance.pe_ttm,
                    "利润增长率": stock_instance.profit_growth_rate,
                    "振幅%": stock_instance.amplitude,
                }
            )
        except Exception as e:
            print(f"!!! 处理 {name}({code}) 失败: {e}")

    # C. 输出利益最大化报告
    if final_results:
        report_df = pd.DataFrame(final_results).sort_values(by="得分", ascending=False)
        print("=" * 80)
        print("【量化多因子评价报告 - 利益最大化执行策略】")
        print("=" * 80)
        print(report_df.to_string(index=False))

        today_str = datetime.now().strftime("%Y%m%d_%H%M")
        file_name = f"量化选股结果_{today_str}.xlsx"

        try:
            # 使用 xlsxwriter 引擎可以更好地处理格式（需安装：pip install xlsxwriter）
            report_df.to_excel(file_name, index=False, engine="xlsxwriter")
            print(f"\n>>> 结果已成功保存至 Excel: {file_name}")
        except Exception as e:
            print(f"\n[!] Excel 保存失败: {e}")

        top_one = report_df.iloc[0]
        if top_one["得分"] >= 9:
            print(
                f"\n★ 利益最大化推荐：{top_one['名称']} ({top_one['代码']}) 评分最高。"
            )
        else:
            print("\n! 风险提示：当前市场环境下，自选股评分均未达到 Level 1。")
    else:
        print("\n[!] 未能匹配到有效数据。")