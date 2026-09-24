"""
股票行业分类功能测试。

测试内容：
    - 股票 -> 行业分类
    - 行业 -> 成份股
    - 获取各级行业列表
    - 统计各级行业数量

用于验证中证行业分类数据及相关查询函数是否正常工作。
"""

from utils.stock_industry_classification import (
    get_all_industries,
    get_category_stocks,
    get_stock_industry_category,
)


def test_industry_classification():
    """测试股票行业分类相关功能。"""

    # 1. 股票 -> 行业
    print("\n【1. 股票行业分类】")
    industry = get_stock_industry_category("600519")
    if industry:
        industry.display()
    else:
        print("未找到股票行业信息")

    # 2. 行业 -> 股票
    print("\n【2. 行业成份股】")
    stocks = get_category_stocks("半导体")
    print(f"半导体股票数量: {len(stocks)}")
    print(f"前 10 只: {stocks[:10]}")

    # 3. 一级行业
    print("\n【3. 一级行业】")
    industries = get_all_industries(level=1)
    print(f"一级行业数量: {len(industries)}")
    for industry in industries:
        print(f"{industry.symbol:<10}{industry.name}")

    # 4. 二级行业
    print("\n【4. 二级行业】")
    industries = get_all_industries(level=2)
    print(f"二级行业数量: {len(industries)}")
    for industry in industries[:10]:
        print(f"{industry.symbol:<10}{industry.name}")
    if len(industries) > 10:
        print("...")

    # 5. 各级行业数量
    print("\n【5. 各级行业数量】")
    for level in [1, 2, 3, 4]:
        industries = get_all_industries(level)
        print(f"{level}级行业: {len(industries)}")


def main():
    test_industry_classification()


if __name__ == "__main__":
    main()
