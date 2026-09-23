# -*- coding: utf-8 -*-
from functools import lru_cache
from typing import Dict, List, Optional, Union
import pandas as pd

from common.constants import IndustryStandard
from core.models.industry import Industry
from .download_industry_data import get_csindex_industry_data

"""
==============================================================================
模块名称 (Module Name) : CSIndex Industry Classification Query Tool
功能描述 (Description) : 本模块提供中证行业分类数据的离线检索与处理工具。
==============================================================================
"""

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

ZH_NUM_MAP = {1: "一", 2: "二", 3: "三", 4: "四"}


def _parse_level(level: Optional[Union[int, str]]) -> Optional[int]:
    """统一解析层级输入为标准的 1~4 整数"""
    if level is None:
        return None
    return LEVEL_MAP.get(level, LEVEL_MAP.get(str(level).strip()))


class StockItem:
    """单只股票数据对象，支持属性访问 (stock.code, stock.name, stock.l3 等)"""

    def __init__(self, row_dict: dict):
        raw_code = str(row_dict.get("code", "")).split(".")[0]
        self.code: str = raw_code.zfill(6) if raw_code else ""
        self.name: str = str(row_dict.get("name", ""))
        self.l1: str = str(row_dict.get("l1", ""))
        self.l2: str = str(row_dict.get("l2", ""))
        self.l3: str = str(row_dict.get("l3", ""))
        self.l4: str = str(row_dict.get("l4", ""))

    def __repr__(self) -> str:
        return f"<Stock {self.code} {self.name} | {self.l1}->{self.l2}->{self.l3}->{self.l4}>"

    def to_dict(self) -> dict:
        return {
            "code": self.code,
            "name": self.name,
            "l1": self.l1,
            "l2": self.l2,
            "l3": self.l3,
            "l4": self.l4,
        }


class StockQueryResult:
    """股票查询结果容器，封装 DataFrame，解决访问繁琐问题"""

    def __init__(self, df: pd.DataFrame):
        self._df: pd.DataFrame = df.reset_index(drop=True)

    def top(self, n: int = 5) -> "StockQueryResult":
        """获取前 N 条结果"""
        return StockQueryResult(self._df.head(n))

    def summary(self, level: Union[int, str] = 3) -> pd.DataFrame:
        """只提取核心摘要列 (代码、名称、指定行业层级)"""
        lvl_num = _parse_level(level) or 3
        target_lvl = f"l{lvl_num}"
        cols = ["code", "name", target_lvl]
        return self._df[[c for c in cols if c in self._df.columns]]

    def to_list(self) -> List[StockItem]:
        """转为 Python 对象列表"""
        return [StockItem(row) for row in self._df.to_dict(orient="records")]

    def to_df(self) -> pd.DataFrame:
        """提取底层原生 DataFrame"""
        return self._df.copy()

    def industry(
        self,
    ) -> pd.Series:
        """
        获取行业路径。
        """

        return self._df.apply(
            self._industry_path,
            axis=1,
        )

    def _industry_path(
        self,
        row: pd.Series,
    ) -> str:
        """
        拼接行业层级。

        示例：

        l1 - l2 - l3 - l4
        """

        levels = []

        for col in [
            "l1",
            "l2",
            "l3",
            "l4",
        ]:
            value = row.get(col)

            if value is not None and str(value).strip():
                levels.append(str(value))

        return " - ".join(levels)

    def __len__(self) -> int:

        return len(self._df)

    def __str__(self) -> str:
        if self._df.empty:
            return "<StockQueryResult: 空数据>"

        return self._industry_path(self._df.iloc[0])

    def __repr__(self) -> str:
        return self.__str__()


class CategoryQueryResult:
    """行业分类列表容器"""

    def __init__(self, data: Union[List[str], pd.DataFrame]):
        self._data = data

    def top(self, n: int = 5) -> "CategoryQueryResult":
        """获取前 N 个分类"""
        if isinstance(self._data, pd.DataFrame):
            return CategoryQueryResult(self._data.head(n))
        return CategoryQueryResult(self._data[:n])

    def to_list(self) -> Union[List[str], List[Dict[str, str]]]:
        """直接获取纯字符串名称列表，或带代码的字典列表"""
        if isinstance(self._data, pd.DataFrame):
            return self._data.to_dict(orient="records")
        return list(self._data)

    def to_df(self) -> pd.DataFrame:
        """获取包含分类数据的 DataFrame"""
        if isinstance(self._data, pd.DataFrame):
            return self._data.copy()
        return pd.DataFrame(self._data, columns=["category_name"])

    def __len__(self) -> int:
        return len(self._data)

    def __repr__(self) -> str:
        if isinstance(self._data, pd.DataFrame):
            return self._data.to_string(index=False)
        return (
            f"全量行业分类 ({len(self._data)}个):\n"
            + ", ".join(map(str, self._data[:10]))
            + ("..." if len(self._data) > 10 else "")
        )


@lru_cache(maxsize=1)
def _get_cached_data() -> pd.DataFrame:
    """读取数据并自动清洗映射为统一表头 (code, name, l1, l2, l3, l4)"""
    df = get_csindex_industry_data().copy()
    code_col = next(
        (c for c in ["证券代码", "成分券代码", "代码"] if c in df.columns),
        df.columns[0],
    )

    rename_dict = {code_col: "code", "证券简称": "name"}
    for lvl_num, lvl_zh in ZH_NUM_MAP.items():
        rename_dict[f"中证{lvl_zh}级行业分类简称"] = f"l{lvl_num}"
        rename_dict[f"中证{lvl_zh}级行业分类代码"] = f"l{lvl_num}_code"

    df = df.rename(columns=rename_dict)
    df["code"] = df["code"].astype(str).str.split(".").str[0].str.strip().str.zfill(6)
    df["name"] = df["name"].astype(str).str.strip()
    return df


def get_stock_industry_category(
    stocks: Union[str, int, list[Union[str, int]]],
) -> Union[Industry, list[Industry], None]:
    """
    查询股票所属行业。

    Args:
        stocks:
            股票代码、股票名称，或者股票代码/名称列表。

            例如：
                "600519"
                "600519.SH"
                "贵州茅台"
                ["600519", "000858", "000568"]

    Returns:
        单个股票:
            Industry | None

        多个股票:
            list[Industry]
    """

    df = _get_cached_data()

    raw_list = [stocks] if isinstance(stocks, (str, int)) else stocks

    target_codes: list[str] = []
    target_names: list[str] = []

    for stock in raw_list:
        value = str(stock).strip()

        code = value.split(".")[0]

        if code.isdigit():
            target_codes.append(code.zfill(6))
        else:
            target_names.append(value)

    mask = df["code"].isin(target_codes) | df["name"].isin(target_names)

    res = df[mask]

    industries: list[Industry] = []

    for _, row in res.iterrows():
        industries.append(
            Industry(
                symbol=str(row["code"]),
                name=row["name"],
                level_1=row.get("l1"),
                level_2=row.get("l2"),
                level_3=row.get("l3"),
                level_4=row.get("l4"),
                standard=IndustryStandard.CSI,
                source="中证指数",
            )
        )

    # 单个输入 -> 单个对象
    if isinstance(stocks, (str, int)):
        return industries[0] if industries else None

    # 多个输入 -> 多个对象
    return industries


def get_category_stocks(
    category_name: str,
    level: Optional[Union[int, str]] = None,
    top: Optional[int] = None,
) -> StockQueryResult:
    """获取某个行业下的所有股票 (支持模糊匹配和跨层级自动检索)"""
    df = _get_cached_data()
    clean_cat = str(category_name).strip()
    lvl_num = _parse_level(level)

    if lvl_num is not None:
        target_col = f"l{lvl_num}_code" if clean_cat.isdigit() else f"l{lvl_num}"
        if target_col in df.columns:
            res = df[df[target_col].astype(str).str.strip() == clean_cat]
            if res.empty and not clean_cat.isdigit():
                res = df[df[target_col].astype(str).str.contains(clean_cat, na=False)]
        else:
            res = df.iloc[0:0]
    else:
        if clean_cat.isdigit():
            code_cols = [
                c for c in df.columns if c.startswith("l") and c.endswith("_code")
            ]
            mask = (
                df[code_cols]
                .astype(str)
                .apply(lambda col: col.str.strip() == clean_cat)
                .any(axis=1)
            )
        else:
            name_cols = [c for c in ["l1", "l2", "l3", "l4"] if c in df.columns]
            mask = (
                df[name_cols]
                .astype(str)
                .apply(lambda col: col.str.contains(clean_cat, na=False))
                .any(axis=1)
            )
        res = df[mask]

    if top:
        res = res.head(top)

    return StockQueryResult(res)


def get_all_category(
    level: Union[int, str] = 1,
    return_code: bool = False,
    top: Optional[int] = None,
) -> CategoryQueryResult:
    """获取全量行业分类列表"""
    df = _get_cached_data()
    lvl_num = _parse_level(level) or 1

    name_col = f"l{lvl_num}"
    code_col = f"l{lvl_num}_code"

    if return_code and code_col in df.columns:
        res_df = (
            df[[code_col, name_col]].dropna().drop_duplicates().reset_index(drop=True)
        )
        res_df.columns = ["category_code", "category_name"]
        if top:
            res_df = res_df.head(top)
        return CategoryQueryResult(res_df)

    res_list = df[name_col].dropna().unique().tolist()
    if top:
        res_list = res_list[:top]
    return CategoryQueryResult(res_list)
