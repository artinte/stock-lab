# -*- coding: utf-8 -*-
"""
==============================================================================
模块名称 (Module Name) : Stock Code & Entity Utilities
功能描述 (Description) : 跨交易所股票代码与名称互转工具，支持多平台后缀与雪球链接拼装。

官方数据源参考 (Official Data Sources):
- 上海证券交易所 (SSE): https://www.sse.com.cn/assortment/stock/list/share/
- 深圳证券交易所 (SZSE): https://www.szse.cn/market/product/stock/list/index.html

执行：python -m utils.stock_mapping
==============================================================================
"""

import re
from enum import Enum
from typing import Optional, Union, Dict
from common.enums.exchange import Exchange
from utils.stock_industry_classification import get_stock_industry_category

# 上海证券交易所 (Shanghai Stock Exchange - SSE)
# 沪市主板代码前缀
SSE_MAIN_BOARD_PREFIX = "60"
# 科创板代码前缀
SSE_STAR_MARKET_PREFIX = "688"

# 深圳证券交易所 (Shenzhen Stock Exchange - SZSE)
# 深市主板/中小板代码前缀
SZSE_MAIN_BOARD_PREFIX = "00"
# 创业板代码前缀
SZSE_CHINEXT_PREFIX = "30"

# 北京证券交易所 (Beijing Stock Exchange - BSE)
BSE_PREFIXES = ("8", "43", "47", "92")


class MarketExchange(Enum):
    """交易所枚举"""

    SSE = "SSE"  # 上海证券交易所 (Shanghai Stock Exchange)
    SZSE = "SZSE"  # 深圳证券交易所 (Shenzhen Stock Exchange)
    BSE = "BSE"  # 北京证券交易所 (Beijing Stock Exchange)
    UNKNOWN = "UNKNOWN"


class SymbolFormat(Enum):
    """代码后缀/前缀格式类型"""

    RAW = "RAW"  # 原始 6 位代码，如 '600433'
    LOWER_SUFFIX = "LOWER"  # 小写点后缀，如 '600433.sh', '000001.sz'
    UPPER_SUFFIX = "UPPER"  # 大写点后缀 (Wind/Tushare)，如 '600433.SH', '000001.SZ'
    PREFIX_UPPER = "PREFIX"  # 大写前缀 (雪球/富途)，如 'SH600433', 'SZ000001'
    JOINQUANT = "JOINQUANT"  # 聚宽/RQAlpha 格式，如 '600433.XSHG', '000001.XSHE'
    XUEQIU_URL = "XUEQIU_URL"  # 雪球股票主页链接，如 'https://xueqiu.com/S/SH600433'


class StockCodeConverter:
    """商业级股票代码与实体转换器"""

    XUEQIU_BASE_URL = "https://xueqiu.com/S/"

    @staticmethod
    def clean_code(code: Union[str, int]) -> str:
        """清洗输入代码并补齐为 6 位标准数字字符串"""
        if isinstance(code, int):
            return f"{code:06d}"

        # 提取纯数字部分
        digits = re.sub(r"\D", "", str(code))
        if not digits:
            return ""
        return digits.zfill(6)

    @classmethod
    def infer_exchange(cls, code: Union[str, int]) -> MarketExchange:
        """根据 6 位股票代码前缀智能推断交易所"""
        standard_code = cls.clean_code(code)
        if not standard_code:
            return MarketExchange.UNKNOWN

        # 主板、科创板 (上海)
        if standard_code.startswith(("600", "601", "603", "605", "688", "689", "900")):
            return MarketExchange.SSE
        # 主板、创业板 (深圳)
        elif standard_code.startswith(
            ("000", "001", "002", "003", "300", "301", "302", "200")
        ):
            return MarketExchange.SZSE
        # 北交所
        elif standard_code.startswith(("83", "87", "88", "43")):
            return MarketExchange.BSE

        return MarketExchange.UNKNOWN

    @classmethod
    def format_symbol(
        cls,
        code: Union[str, int],
        fmt: Union[SymbolFormat, str] = SymbolFormat.UPPER_SUFFIX,
    ) -> str:
        """
        将原始股票代码转换为指定平台的格式或拼装链接

        :param code: 股票代码
        :param fmt: 期望的输出格式，支持 SymbolFormat 枚举或字符串
        """
        raw_code = cls.clean_code(code)
        if not raw_code:
            return str(code)

        if isinstance(fmt, str):
            try:
                fmt = SymbolFormat[fmt.upper()]
            except KeyError:
                fmt = SymbolFormat.UPPER_SUFFIX

        exchange = cls.infer_exchange(raw_code)

        if fmt == SymbolFormat.RAW or exchange == MarketExchange.UNKNOWN:
            return raw_code

        # 根据交易所映射前后缀
        suffix_map = {
            MarketExchange.SSE: {
                "s_upper": ".SH",
                "s_lower": ".sh",
                "p_upper": "SH",
                "jq": ".XSHG",
            },
            MarketExchange.SZSE: {
                "s_upper": ".SZ",
                "s_lower": ".sz",
                "p_upper": "SZ",
                "jq": ".XSHE",
            },
            MarketExchange.BSE: {
                "s_upper": ".BJ",
                "s_lower": ".bj",
                "p_upper": "BJ",
                "jq": ".XBJG",
            },
        }

        mapping = suffix_map.get(exchange, {})

        if fmt == SymbolFormat.UPPER_SUFFIX:
            return f"{raw_code}{mapping.get('s_upper', '')}"
        elif fmt == SymbolFormat.LOWER_SUFFIX:
            return f"{raw_code}{mapping.get('s_lower', '')}"
        elif fmt == SymbolFormat.PREFIX_UPPER:
            return f"{mapping.get('p_upper', '')}{raw_code}"
        elif fmt == SymbolFormat.JOINQUANT:
            return f"{raw_code}{mapping.get('jq', '')}"
        elif fmt == SymbolFormat.XUEQIU_URL:
            prefix_symbol = f"{mapping.get('p_upper', '')}{raw_code}"
            return f"{cls.XUEQIU_BASE_URL}{prefix_symbol}"

        return raw_code

    @classmethod
    def get_xueqiu_url(cls, code_or_name: Union[str, int]) -> Optional[str]:
        """
        快捷拼装雪球股票主页链接
        :param code_or_name: 股票代码或名称（如 '600433', '600433.SH', '冠豪高新'）
        :return: 对应的雪球 URL
        """
        clean_code = cls.clean_code(code_or_name)

        # 如果传入的是股票名称，先转成代码
        if not (clean_code and len(clean_code) == 6 and clean_code.isdigit()):
            query_result = get_stock_industry_category(str(code_or_name))
            items = query_result.to_list()
            if items:
                clean_code = items[0].code
            else:
                return None

        return cls.format_symbol(clean_code, fmt=SymbolFormat.XUEQIU_URL)


def stock_code_to_name(
    code: Union[str, int], default: Optional[str] = None
) -> Optional[str]:
    """根据股票代码获取股票名称"""
    clean_code = StockCodeConverter.clean_code(code)
    if not clean_code:
        return default

    query_result = get_stock_industry_category(clean_code)
    items = query_result.to_list()
    if items:
        return items[0].name
    return default


def stock_name_to_code(
    name: str,
    default: Optional[str] = None,
    fmt: Union[SymbolFormat, str] = SymbolFormat.RAW,
) -> Optional[str]:
    """根据股票名称获取股票代码"""
    query_result = get_stock_industry_category(name)
    items = query_result.to_list()
    if items:
        raw_code = items[0].code
        return StockCodeConverter.format_symbol(raw_code, fmt=fmt)
    return default


def get_stock_info(identifier: Union[str, int]) -> Optional[Dict[str, str]]:
    """获取股票的全维度元数据 (含雪球链接)"""
    clean_code = StockCodeConverter.clean_code(identifier)

    if clean_code and len(clean_code) == 6 and clean_code.isdigit():
        code = clean_code
        name = stock_code_to_name(code)
    else:
        name = str(identifier)
        code = stock_name_to_code(name, fmt=SymbolFormat.RAW)

    if not code or not name:
        return None

    exchange = StockCodeConverter.infer_exchange(code)

    return {
        "code": code,
        "name": name,
        "exchange": exchange.value,
        "symbol_wind": StockCodeConverter.format_symbol(
            code, SymbolFormat.UPPER_SUFFIX
        ),
        "symbol_xueqiu": StockCodeConverter.format_symbol(
            code, SymbolFormat.PREFIX_UPPER
        ),
        "xueqiu_url": StockCodeConverter.format_symbol(code, SymbolFormat.XUEQIU_URL),
        "symbol_joinquant": StockCodeConverter.format_symbol(
            code, SymbolFormat.JOINQUANT
        ),
    }


# ============================================================
# 指数代码
# ============================================================

INDEX_SYMBOLS = {
    # A 股主要指数
    "000001": "000001.SH",  # 上证指数
    "399001": "399001.SZ",  # 深证成指
    "399006": "399006.SZ",  # 创业板指
    "000688": "000688.SH",  # 科创50
    # 常用指数
    "000016": "000016.SH",  # 上证50
    "000300": "000300.SH",  # 沪深300
    "000905": "000905.SH",  # 中证500
    "000852": "000852.SH",  # 中证1000
    "000906": "000906.SH",  # 中证800
    "399005": "399005.SZ",  # 中小100
    "399300": "399300.SZ",  # 沪深300（深市指数代码）
}


def normalize_symbol(symbol: str) -> str:
    """
    标准化证券代码。

    内部统一格式：

        上海股票 -> XXXXX.SH
        深圳股票 -> XXXXX.SZ
        北京股票 -> XXXXX.BJ
        上海指数 -> XXXXX.SH
        深圳指数 -> XXXXX.SZ

    注意：
        指数代码优先处理，不能单纯依赖股票代码规则。
    """

    symbol = str(symbol).strip().upper()

    if not symbol:
        return symbol

    # 1. 已经是标准格式
    if "." in symbol:
        return symbol

    # 2. 指数特殊处理
    #
    # 必须放在股票判断之前
    if symbol in INDEX_SYMBOLS:
        return INDEX_SYMBOLS[symbol]

    # 3. 上海股票
    if symbol.startswith(
        (
            "600",
            "601",
            "603",
            "605",
            "688",
            "689",
        )
    ):
        return f"{symbol}.SH"

    # 4. 深圳股票
    if symbol.startswith(
        (
            "000",
            "001",
            "002",
            "003",
            "300",
            "301",
        )
    ):
        return f"{symbol}.SZ"

    # 5. 北京股票
    if symbol.startswith(
        (
            "4",
            "8",
        )
    ):
        return f"{symbol}.BJ"

    # 6. 无法判断
    return symbol


def add_exchange_suffix(stock_code):
    """
    根据 A 股代码规则添加交易所后缀
    逻辑：已有后缀不处理，无后缀根据前缀自动补全
    """
    if not stock_code:
        return ""

    # 1. 预处理：转大写并去空格
    code = stock_code.strip().upper()

    # 2. 如果已经有正确后缀，直接返回
    if code.endswith((".SH", ".SZ", ".BJ")):
        return code

    # 3. 提取纯数字部分，防止类似 600519.ss 的错误输入
    base_code = code.split(".")[0]

    # 4. 根据你提供的前缀常量进行判断
    # 沪市 (SH)
    if base_code.startswith(SSE_MAIN_BOARD_PREFIX) or base_code.startswith(
        SSE_STAR_MARKET_PREFIX
    ):
        return f"{base_code}.SH"

    # 深市 (SZ)
    if base_code.startswith(SZSE_MAIN_BOARD_PREFIX) or base_code.startswith(
        SZSE_CHINEXT_PREFIX
    ):
        return f"{base_code}.SZ"

    # 北交所 (BJ)
    if base_code.startswith(BSE_PREFIXES):
        return f"{base_code}.BJ"

    # 5. 不匹配则返回原始 base_code
    return base_code


def get_exchange(symbol: str) -> Exchange | None:
    """
    根据股票代码判断交易所。

    支持：

        600519.SH
        000001.SZ
        688981
        430047.BJ

    """

    symbol = symbol.upper().strip()

    # 去掉后缀
    if "." in symbol:
        code, suffix = symbol.split(".", 1)

        if suffix == "SH":
            return Exchange.SSE

        if suffix == "SZ":
            return Exchange.SZSE

        if suffix == "BJ":
            return Exchange.BSE

    code = symbol

    # 上海
    if code.startswith(
        (
            "600",
            "601",
            "603",
            "605",
            "688",
            "689",
        )
    ):
        return Exchange.SSE

    # 深圳
    if code.startswith(
        (
            "000",
            "001",
            "002",
            "003",
            "300",
            "301",
        )
    ):
        return Exchange.SZSE

    # 北京
    if code.startswith(
        (
            "4",
            "8",
        )
    ):
        return Exchange.BSE

    return None


_EXCHANGE_NAMES = {
    Exchange.SSE: "上海证券交易所",
    Exchange.SZSE: "深圳证券交易所",
    Exchange.BSE: "北京证券交易所",
    Exchange.NASDAQ: "纳斯达克证券交易所",
    Exchange.NYSE: "纽约证券交易所",
}


def exchange_name(
    exchange: Exchange | None,
) -> str:
    """
    获取交易所中文名称。
    """

    if exchange is None:
        return "--"

    return _EXCHANGE_NAMES.get(
        exchange,
        "未知交易所",
    )
