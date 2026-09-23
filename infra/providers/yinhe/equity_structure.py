from __future__ import annotations

from datetime import date
from typing import Optional

from common.constants import TEN_THOUSAND
from core.cache.file import FileCache
from core.cache.paths import get_cache_path

from core.models.equity_structure import EquityStructure

from utils.stock_mapping import normalize_symbol

"""
银河股本结构数据适配器。

负责：

1. 从银河数据源获取股票股本结构
2. 将银河原始字段转换为 EquityStructure
3. 使用本地 JSON 缓存减少重复请求
4. 支持单只股票和批量股票查询

银河原始接口：

    info_data.get_equity_structure()

统一转换为：

    EquityStructure
"""


class YinheEquityStructure:
    """银河股票股本结构适配器。"""

    def __init__(self, gateway):
        self.gateway = gateway

        self._equity_structure_cache = FileCache[EquityStructure](
            path=get_cache_path(
                provider="yinhe",
                name="equity_structure",
            ),
            ttl_days=1,
            serializer=EquityStructure.to_dict,
            deserializer=EquityStructure.from_dict,
        )

    @staticmethod
    def _parse_date(value) -> date | None:
        """解析日期字段。"""

        if value is None:
            return None

        if isinstance(value, date):
            return value

        value = str(value).strip()

        if not value or value == "-":
            return None

        try:
            # 例如：20250331
            if len(value) == 8 and value.isdigit():
                return date(
                    int(value[:4]),
                    int(value[4:6]),
                    int(value[6:8]),
                )

            # 例如：2025-03-31
            return date.fromisoformat(value)

        except ValueError:
            return None

    @staticmethod
    def _clean_value(value):
        """清理银河原始字段。"""

        if value is None:
            return None

        try:
            if value != value:
                return None
        except Exception:
            pass

        value = str(value).strip()

        if not value or value in {
            "-",
            "--",
            "None",
            "nan",
            "NaN",
            "NULL",
        }:
            return None

        return value

    @classmethod
    def _to_float(cls, value) -> float | None:
        """转换为浮点数。"""

        value = cls._clean_value(value)

        if value is None:
            return None

        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _to_bool(value) -> bool | None:
        """转换为布尔值。"""

        if value is None:
            return None

        try:
            if value != value:
                return None
        except Exception:
            pass

        if isinstance(value, bool):
            return value

        try:
            return bool(int(value))
        except (TypeError, ValueError):
            return None

    @classmethod
    def _select_latest(cls, records):
        """
        从同一股票的多条股本记录中选择最新有效记录。

        优先级：

        1. CURRENT_SIGN = 1
        2. IS_VALID = 1
        3. 公告日期
        4. 股本变动日期
        """

        if records is None or len(records) == 0:
            return None

        records = records.copy()

        # 最新记录
        if "CURRENT_SIGN" in records.columns:
            current = records[
                records["CURRENT_SIGN"].apply(lambda value: cls._to_bool(value) is True)
            ]

            if not current.empty:
                records = current

        # 有效记录
        if "IS_VALID" in records.columns:
            valid = records[
                records["IS_VALID"].apply(lambda value: cls._to_bool(value) is True)
            ]

            if not valid.empty:
                records = valid

        # 优先使用公告日期
        if "ANN_DATE" in records.columns:
            records["_ann_date"] = records["ANN_DATE"].apply(cls._parse_date)

        else:
            records["_ann_date"] = None

        # 再使用股本变动日期
        if "CHANGE_DATE" in records.columns:
            records["_change_date"] = records["CHANGE_DATE"].apply(cls._parse_date)

        else:
            records["_change_date"] = None

        records = records.sort_values(
            by=["_ann_date", "_change_date"],
            ascending=False,
            na_position="last",
        )

        return records.iloc[0]

    @classmethod
    def _parse_equity_structure(
        cls,
        row,
        source: str,
    ) -> EquityStructure | None:
        """将银河原始数据转换为 EquityStructure。"""

        symbol = cls._clean_value(row.get("MARKET_CODE"))

        if symbol is None:
            return None

        return EquityStructure(
            symbol=symbol,
            total_shares=cls._to_float(row.get("TOT_SHARE")) * TEN_THOUSAND,
            float_shares=cls._to_float(row.get("FLOAT_SHARE")) * TEN_THOUSAND,
            float_a_shares=cls._to_float(row.get("FLOAT_A_SHARE")) * TEN_THOUSAND,
            float_b_shares=cls._to_float(row.get("FLOAT_B_SHARE")) * TEN_THOUSAND,
            restricted_shares=cls._to_float(row.get("TOT_RESTRICTED_SHARE"))
            * TEN_THOUSAND,
            announcement_date=cls._parse_date(row.get("ANN_DATE")),
            change_date=cls._parse_date(row.get("CHANGE_DATE")),
            ex_change_date=cls._parse_date(row.get("EX_CHANGE_DATE")),
            change_reason=(
                cls._clean_value(row.get("SHARE_CHANGE_REASON"))
                or cls._clean_value(row.get("SHARE_CHANGE_REASON_STR"))
            ),
            source=source,
        )

    def fetch_equity_structure(
        self,
        symbol: str,
    ) -> Optional[EquityStructure]:
        """获取单只股票的股本结构。"""

        structures = self.fetch_equity_structures([symbol])

        return structures[0] if structures else None

    def fetch_equity_structures(
        self,
        symbols: list[str],
    ) -> list[EquityStructure]:
        """批量获取股票股本结构。"""

        self.gateway._ensure_started()

        if not symbols:
            return []

        normalized_symbols = list(
            dict.fromkeys(normalize_symbol(symbol) for symbol in symbols)
        )

        structures: dict[str, EquityStructure] = {}
        missing_symbols: list[str] = []

        # 先读取缓存
        for symbol in normalized_symbols:
            cached_structure = self._equity_structure_cache.get(symbol)

            if cached_structure is not None:
                structures[symbol] = cached_structure
            else:
                missing_symbols.append(symbol)

        # 获取缓存未命中的数据
        if missing_symbols:
            try:
                equity_structure = self.gateway.info_data.get_equity_structure(
                    missing_symbols,
                    local_path=self.gateway.local_path,
                    is_local=True,
                )

            except Exception as exc:
                print(f"[银河网关] 获取股票股本结构失败 " f"{missing_symbols}: {exc}")
                equity_structure = None

            if (
                equity_structure is not None
                and not equity_structure.empty
                and "MARKET_CODE" in equity_structure.columns
            ):
                for symbol in missing_symbols:
                    records = equity_structure[
                        equity_structure["MARKET_CODE"].astype(str) == symbol
                    ]

                    if records.empty:
                        continue

                    # 同一股票可能存在多条历史记录，
                    # 选择最新有效记录。
                    row = self._select_latest(records)

                    if row is None:
                        continue

                    structure = self._parse_equity_structure(
                        row=row,
                        source=self.gateway.display_name,
                    )

                    if structure is None:
                        continue

                    try:
                        self._equity_structure_cache.set(
                            key=structure.symbol,
                            value=structure,
                        )
                    except Exception as exc:
                        print(
                            f"[银河网关] 缓存股票股本结构失败 "
                            f"{structure.symbol}: {exc}"
                        )

                    structures[symbol] = structure

        # 按输入顺序返回
        return [
            structures[symbol] for symbol in normalized_symbols if symbol in structures
        ]
