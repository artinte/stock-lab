# -*- coding: utf-8 -*-

from utils.stock_industry_classification import (
    get_all_industries,
    get_category_stocks,
    get_stock_industry_category,
)


def main():
    # =========================================================================
    # 1. 股票 -> 行业
    # =========================================================================

    print("=" * 70)
    print("1. 股票行业分类")
    print("=" * 70)

    industry = get_stock_industry_category("600519")

    if industry:
        industry.display()
    else:
        print("未找到股票行业信息")

    # =========================================================================
    # 2. 行业 -> 股票
    # =========================================================================

    print("\n" + "=" * 70)
    print("2. 行业成份股")
    print("=" * 70)

    stocks = get_category_stocks("半导体")

    print(f"半导体股票数量: {len(stocks)}")
    print(f"前 10 只: {stocks[:10]}")

    # =========================================================================
    # 3. 一级行业
    # =========================================================================

    print("\n" + "=" * 70)
    print("3. 一级行业")
    print("=" * 70)

    industries = get_all_industries(1)

    print(f"一级行业数量: {len(industries)}")

    for industry in industries:
        print(f"{industry.symbol:<10}" f"{industry.name}")

    # =========================================================================
    # 4. 二级行业
    # =========================================================================

    print("\n" + "=" * 70)
    print("4. 二级行业")
    print("=" * 70)

    industries = get_all_industries(2)

    print(f"二级行业数量: {len(industries)}")

    for industry in industries[:10]:
        print(f"{industry.symbol:<10}" f"{industry.name}")

    if len(industries) > 10:
        print("...")

    # =========================================================================
    # 5. 三级、四级行业数量
    # =========================================================================

    print("\n" + "=" * 70)
    print("5. 各级行业数量")
    print("=" * 70)

    for level in [1, 2, 3, 4]:
        industries = get_all_industries(level)

        print(f"{level}级行业: " f"{len(industries)}")


if __name__ == "__main__":
    main()
