# -*- coding: utf-8 -*-

"""
==============================================================================
模块名称 : 中证行业分类数据查询
功能描述 : 提供中证行业分类、股票行业归属以及行业股票列表查询。
==============================================================================
"""

from functools import lru_cache
from typing import Optional, Union

import pandas as pd

from common.constants import IndustryStandard
from core.models.industry import Industry
from .download_industry_data import get_csindex_industry_data

# =============================================================================
# 常量
# =============================================================================

LEVEL_MAP = {
    1: 1,
    "1": 1,
    "一级": 1,
    "一": 1,
    2: 2,
    "2": 2,
    "二级": 2,
    "二": 2,
    3: 3,
    "3": 3,
    "三级": 3,
    "三": 3,
    4: 4,
    "4": 4,
    "四级": 4,
    "四": 4,
}

ZH_NUM_MAP = {
    1: "一",
    2: "二",
    3: "三",
    4: "四",
}


# =============================================================================
# 内部工具
# =============================================================================


def _parse_level(level: Union[int, str]) -> int:
    """将行业层级统一转换为 1~4 的整数。"""

    value = LEVEL_MAP.get(level)

    if value is None:
        value = LEVEL_MAP.get(str(level).strip())

    if value is None:
        raise ValueError(f"无效的行业层级: {level!r}，" "支持 1~4、一级~四级。")

    return value


def _normalize_stock_code(code: Union[str, int]) -> str:
    """标准化股票代码。"""

    value = str(code).strip()

    # 去除交易所后缀，例如 600519.SH
    value = value.split(".")[0]

    if value.isdigit():
        return value.zfill(6)

    return value


# =============================================================================
# 数据读取
# =============================================================================


@lru_cache(maxsize=1)
def _get_cached_data() -> pd.DataFrame:
    """
    获取并缓存中证行业分类数据。

    数据统一转换为：

        code
        name
        l1
        l1_code
        l2
        l2_code
        l3
        l3_code
        l4
        l4_code
    """

    df = get_csindex_industry_data().copy()

    # -------------------------------------------------------------------------
    # 股票代码
    # -------------------------------------------------------------------------

    code_col = next(
        (
            column
            for column in [
                "证券代码",
                "成分券代码",
                "代码",
            ]
            if column in df.columns
        ),
        None,
    )

    if code_col is None:
        raise ValueError("中证行业数据中不存在股票代码字段。")

    # -------------------------------------------------------------------------
    # 字段映射
    # -------------------------------------------------------------------------

    rename_map = {
        code_col: "code",
        "证券简称": "name",
    }

    for level, level_name in ZH_NUM_MAP.items():
        rename_map[f"中证{level_name}级行业分类代码"] = f"l{level}_code"

        rename_map[f"中证{level_name}级行业分类简称"] = f"l{level}"

    df = df.rename(columns=rename_map)

    # -------------------------------------------------------------------------
    # 基础清洗
    # -------------------------------------------------------------------------

    df["code"] = df["code"].astype(str).str.split(".").str[0].str.strip().str.zfill(6)

    df["name"] = df["name"].astype(str).str.strip()

    for level in range(1, 5):
        for suffix in ["", "_code"]:
            column = f"l{level}{suffix}"

            if column in df.columns:
                df[column] = df[column].fillna("").astype(str).str.strip()

    return df


# =============================================================================
# 行业查询
# =============================================================================


def get_all_industries(
    level: Union[int, str] = 1,
) -> list[Industry]:
    """
    获取指定层级的全部中证行业分类。

    参数：
        level:
            行业层级：

                1 / "一级"
                2 / "二级"
                3 / "三级"
                4 / "四级"

    返回：
        list[Industry]

    示例：

        industries = get_all_industries(1)

        for industry in industries:
            print(industry.symbol, industry.name)
    """

    level = _parse_level(level)

    df = _get_cached_data()

    code_column = f"l{level}_code"
    name_column = f"l{level}"

    columns = [
        code_column,
        name_column,
    ]

    # 只保留有效行业
    data = df[columns].dropna().drop_duplicates()

    industries: list[Industry] = []

    for _, row in data.iterrows():

        code = str(row[code_column]).strip()
        name = str(row[name_column]).strip()

        if not code or not name:
            continue

        industries.append(
            Industry(
                symbol=code,
                name=name,
                level_1=name if level == 1 else None,
                level_2=name if level == 2 else None,
                level_3=name if level == 3 else None,
                level_4=name if level == 4 else None,
                standard=IndustryStandard.CSI,
                source="中证指数",
            )
        )

    return industries


def get_stock_industry_category(
    stock: Union[str, int],
) -> Optional[Industry]:
    """
    查询单只股票所属的中证行业分类。

    参数：
        stock:
            股票代码或股票名称。

            例如：

                "600519"
                "600519.SH"
                "贵州茅台"

    返回：
        Industry | None
    """

    df = _get_cached_data()

    value = str(stock).strip()

    if value.isdigit() or "." in value:
        code = _normalize_stock_code(value)

        result = df[df["code"] == code]
    else:
        result = df[df["name"] == value]

    if result.empty:
        return None

    row = result.iloc[0]

    return Industry(
        symbol=str(row["code"]),
        name=str(row["name"]),
        level_1=str(row["l1"]),
        level_2=str(row["l2"]),
        level_3=str(row["l3"]),
        level_4=str(row["l4"]),
        standard=IndustryStandard.CSI,
        source="中证指数",
    )


def get_category_stocks(
    category: Union[str, int],
    level: Optional[Union[int, str]] = None,
) -> list[str]:
    """
    获取指定行业分类下的全部股票代码。

    参数：
        category:
            行业代码或行业名称。

        level:
            行业层级。

            如果指定 level，则只在该层级查询。

            如果不指定，则根据行业代码自动匹配
            一级、二级、三级、四级。

    返回：
        list[str]

    示例：

        get_category_stocks("401010")

        返回：

        [
            "000001",
            "600000",
            "601398",
            ...
        ]
    """

    df = _get_cached_data()

    value = str(category).strip()

    if level is not None:
        level = _parse_level(level)

        if value.isdigit():
            column = f"l{level}_code"
        else:
            column = f"l{level}"

        if column not in df.columns:
            return []

        mask = df[column] == value

    else:
        # ---------------------------------------------------------------------
        # 未指定层级：
        # 行业代码在一级~四级代码中查找
        # ---------------------------------------------------------------------

        if value.isdigit():

            code_columns = [
                "l1_code",
                "l2_code",
                "l3_code",
                "l4_code",
            ]

            mask = df[code_columns].eq(value).any(axis=1)

        else:

            name_columns = [
                "l1",
                "l2",
                "l3",
                "l4",
            ]

            mask = df[name_columns].eq(value).any(axis=1)

    return df.loc[mask, "code"].drop_duplicates().tolist()
