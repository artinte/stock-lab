from utils.stock_industry_classification import (
    get_stock_industry_category,
    get_category_stocks,
    get_all_category,
)


def test_stock_industry_category(symbol: str = "600519"):
    """
    测试：获取个股行业分类信息。
    """
    print("==================================================================")
    print(f" 个股行业信息：{symbol}")
    print("==================================================================")

    result = get_stock_industry_category(symbol)

    print("\n[1] 直接打印结果:")
    result.display()

    print("\n[2] 三级行业摘要:")
    print(result.summary(level=3))

    print("\n[3] StockItem 对象:")
    items = result.to_list()

    if not items:
        print("未获取到行业信息")
        return result

    item = items[0]

    print(f"股票名称: {item.name}")
    print(f"股票代码: {item.code}")
    print(f"一级分类: {item.l1}")
    print(f"二级分类: {item.l2}")
    print(f"三级分类: {item.l3}")

    return result


def test_category_stocks(
    category: str = "半导体",
    level: int | None = None,
    top: int = 5,
):
    """
    测试：根据行业分类获取成份股。
    """
    print("==================================================================")
    print(f" 行业成份股：{category}")
    print("==================================================================")

    result = get_category_stocks(
        category,
        level=level,
        top=top,
    )

    print("\n[1] 查询结果:")
    print(result)

    print("\n[2] 行业摘要:")
    print(result.summary(level=level or 3))

    print("\n[3] 成份股:")
    for stock in result.to_list():
        print(
            f"代码: {stock.code} | "
            f"名称: {stock.name:<6} | "
            f"一级: {stock.l1} | "
            f"二级: {stock.l2} | "
            f"三级: {stock.l3}"
        )

    return result


def test_all_category(
    level: int = 1,
    top: int | None = None,
    return_code: bool = False,
):
    """
    测试：获取全量行业分类。
    """
    print("==================================================================")
    print(f" 全量行业分类：level={level}")
    print("==================================================================")

    result = get_all_category(
        level=level,
        top=top,
        return_code=return_code,
    )

    print("\n[1] 分类结果:")
    print(result)

    return result


def test_all_category_examples():
    """
    测试：不同形式获取行业分类。
    """

    print("==================================================================")
    print(" 行业分类列表测试")
    print("==================================================================")

    # 一级行业
    print("\n[1] 所有一级行业名称:")
    l1 = get_all_category(level=1)
    print(l1)

    # 二级行业
    print("\n[2] 前 5 个二级行业:")
    l2 = get_all_category(level=2, top=5)
    print(l2.to_list())

    # 三级行业 + 分类代码
    print("\n[3] 前 5 个三级行业及分类代码:")
    l3 = get_all_category(
        level=3,
        return_code=True,
        top=5,
    )
    print(l3)

    return l1, l2, l3


def run_industry_test(symbol):
    industry = get_stock_industry_category(symbol)
    industry.display()

def main():
    """
    统一测试入口。
    """

    run_industry_test("600519")

    # 2. 行业成份股：全层级模糊匹配
    test_category_stocks(
        category="半导体",
        top=5,
    )

    # 3. 行业成份股：指定二级行业
    test_category_stocks(
        category="半导体",
        level=2,
        top=5,
    )

    # 4. 全量行业分类
    test_all_category_examples()


if __name__ == "__main__":
    main()