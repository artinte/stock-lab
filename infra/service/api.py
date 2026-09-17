from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from infra.service.stock_financial_service import StockFinancialService
from infra.data_manager import DataManager
from core.models.crypto.quote import CryptoQuote
from core.models.crypto.kline import CryptoKline

# ============================================================
# 全局数据管理器
# ============================================================

data: DataManager | None = None
financial_service: StockFinancialService | None = None


# ============================================================
# 服务生命周期
# ============================================================


@asynccontextmanager
async def lifespan(app: FastAPI):
    global data
    global financial_service

    # ==================== 启动 ====================

    print()
    print("=" * 60)
    print("正在启动股票数据服务...")
    print("股票数据源：yinhe")
    print("加密货币数据源: binance")
    print("=" * 60)

    try:
        data = DataManager("yinhe")
        data.start()

        financial_service = StockFinancialService(data)

        print("✅ 股票数据服务启动成功")

    except Exception as exc:
        data = None

        print(f"❌ 股票数据服务启动失败：{exc}")

        raise

    # ==================== 运行 ====================

    yield

    # ==================== 关闭 ====================

    print()
    print("=" * 60)
    print("正在关闭股票数据服务...")
    print("=" * 60)

    if data is not None:
        try:
            data.stop()
            print("✅ 数据源已关闭")

        except Exception as exc:
            print(f"⚠️ 关闭数据源失败：{exc}")

        finally:
            data = None


def require_data() -> DataManager:
    """
    获取 DataManager。

    如果数据源没有启动，直接抛出异常。
    """

    if data is None:

        raise RuntimeError("数据源尚未启动")

    return data


# ============================================================
# FastAPI
# ============================================================

app = FastAPI(
    title="A股股票研究中心 API",
    description="股票行情与研究数据 API",
    version="1.0.0",
    lifespan=lifespan,
)


# ============================================================
# 路径配置
# ============================================================

# 项目根目录下的前端目录
FRONTEND_DIR = Path("docs")


# ============================================================
# API：健康检查
# ============================================================


@app.get("/api/health")
def health_check():
    """
    检查 API 和数据服务是否正常。
    """

    manager = data

    return {
        "success": True,
        "api": "running",
        "stock_provider": (manager.stock_provider if manager is not None else None),
        "crypto_provider": (manager.crypto_provider if manager is not None else None),
        "data_manager": manager is not None,
    }


# ============================================================
# API：市场指数
# ============================================================


@app.get("/api/indices")
def get_indices(indices: str = Query(...)):
    """
    获取指定指数行情。

    示例：
        /api/indices?indices=000001,399001,399006,000688
    """

    if data is None:
        return {
            "success": False,
            "message": "数据源尚未启动",
        }

    symbols = [
        symbol.strip().upper() for symbol in indices.split(",") if symbol.strip()
    ]

    try:
        quotes = data.get_quotes(symbols)

    except Exception as exc:
        print(f"❌ 批量获取指数行情失败：{exc}")

        return {
            "success": False,
            "message": "获取指数行情失败",
        }

    result = []

    for quote in quotes:
        result.append(
            {
                "code": quote.symbol,
                "name": quote.name,
                "price": quote.last_price,
                "change": quote.change,
                "changePercent": quote.change_percent,
            }
        )

    return {
        "success": True,
        "data": result,
    }


# =========================================================
# 1. 股票行情
# =========================================================


def success(
    symbol: str,
    data_value: Any = None,
) -> dict:

    return {
        "success": True,
        "symbol": symbol,
        "data": data_value,
    }


def failure(
    symbol: str,
    message: str = "暂无数据",
) -> dict:

    return {
        "success": False,
        "symbol": symbol,
        "message": message,
        "data": None,
    }


@app.get("/api/stock/{symbol}")
def get_stock(symbol: str):

    symbol = symbol.strip().upper()

    print(f"📊 获取股票信息：{symbol}")

    try:

        manager = require_data()

        stock = manager.get_stock(symbol)

        if stock is None:

            return failure(
                symbol,
                "未获取到股票信息",
            )
        else:
            print(stock)

        return success(
            symbol,
            {
                "symbol": stock.symbol,
                "name": stock.name,
                "market": getattr(stock, "market", None),
                "area": getattr(stock, "area", None),
                "listDate": getattr(stock, "list_date", None),
            },
        )

    except NotImplementedError:

        return failure(
            symbol,
            "当前数据源暂未实现股票信息接口",
        )

    except Exception as exc:

        print(f"❌ 股票信息获取失败：{symbol} -> {exc}")

        return failure(
            symbol,
            "股票信息暂不可用",
        )


@app.get("/api/industry_category/{symbol}")
def get_industry_category(symbol: str):

    symbol = symbol.strip().upper()

    print(f"📊 获取行业分类信息：{symbol}")

    try:

        manager = require_data()

        industry = manager.get_industry(symbol)

        if industry is None:

            return failure(
                symbol,
                "未获取到行业信息",
            )
        else:
            print(industry)

        return success(
            symbol,
            {
                "symbol": industry.symbol,
                "name": industry.name,
                "l1": getattr(industry, "level_1", None),
                "l2": getattr(industry, "level_2", None),
                "l3": getattr(industry, "level_3", None),
                "l4": getattr(industry, "level_4", None),
            },
        )

    except NotImplementedError:

        return failure(
            symbol,
            "当前数据源暂未实现行业信息接口",
        )

    except Exception as exc:

        print(f"❌ 行业信息获取失败：{symbol} -> {exc}")

        return failure(
            symbol,
            "行业信息暂不可用",
        )


@app.get("/api/quote/{symbol}")
def get_quote(symbol: str):

    symbol = symbol.strip().upper()

    print(f"📈 获取行情：{symbol}")

    try:

        manager = require_data()

        quote = manager.get_quote(symbol)

        if quote is None:

            return failure(
                symbol,
                "未获取到行情数据",
            )
        else:
            print(quote)

        return success(
            symbol,
            {
                "symbol": quote.symbol,
                "name": getattr(quote, "name", None),
                "lastPrice": getattr(
                    quote,
                    "last_price",
                    None,
                ),
                "change": getattr(
                    quote,
                    "change",
                    None,
                ),
                "changePercent": getattr(
                    quote,
                    "change_percent",
                    None,
                ),
                "openPrice": getattr(
                    quote,
                    "open_price",
                    None,
                ),
                "highPrice": getattr(
                    quote,
                    "high_price",
                    None,
                ),
                "lowPrice": getattr(
                    quote,
                    "low_price",
                    None,
                ),
                "previousClose": getattr(
                    quote,
                    "previous_close",
                    None,
                ),
                "volume": getattr(
                    quote,
                    "volume",
                    None,
                ),
                "amount": getattr(
                    quote,
                    "amount",
                    None,
                ),
                "turnover": getattr(
                    quote,
                    "turnover",
                    None,
                ),
                "marketCap": getattr(
                    quote,
                    "market_cap",
                    None,
                ),
                "floatMarketCap": getattr(
                    quote,
                    "float_market_cap",
                    None,
                ),
            },
        )

    except NotImplementedError:

        return failure(
            symbol,
            "当前数据源暂未实现行情接口",
        )

    except Exception as exc:

        print(f"❌ 行情获取失败：{symbol} -> {exc}")

        return failure(
            symbol,
            "行情数据暂不可用",
        )


# =========================================================
# 2. K线
# =========================================================


@app.get("/api/kline/{symbol}")
def get_kline(
    symbol: str,
    interval: str = Query(
        "1d",
        description="K线周期：1m/5m/15m/30m/60m/1d/1w/1M",
    ),
    start_time: datetime | None = Query(
        None,
        description="开始时间",
    ),
    end_time: datetime | None = Query(
        None,
        description="结束时间",
    ),
    limit: int = Query(
        120,
        ge=1,
        le=5000,
        description="最多返回K线数量",
    ),
):

    symbol = symbol.strip().upper()

    print(
        f"📊 获取K线："
        f"{symbol} "
        f"interval={interval} "
        f"start={start_time} "
        f"end={end_time} "
        f"limit={limit}"
    )

    try:

        manager = require_data()

        if not hasattr(manager, "get_kline"):

            return failure(
                symbol,
                "K线接口暂未实现",
            )

        klines = manager.get_kline(
            symbol,
            interval=interval,
            start_time=start_time,
            end_time=end_time,
            limit=limit,
        )

        if not klines:

            return failure(
                symbol,
                "暂无K线数据",
            )

        print(f"  获取到 {len(klines)} 根K线")

        result = []

        for item in klines:

            result.append(
                {
                    "timestamp": (
                        item.timestamp.isoformat() if item.timestamp else None
                    ),
                    "open": item.open,
                    "high": item.high,
                    "low": item.low,
                    "close": item.close,
                    "volume": item.volume,
                    "amount": item.amount,
                }
            )

        return success(
            symbol,
            {
                "interval": interval,
                "start_time": (start_time.isoformat() if start_time else None),
                "end_time": (end_time.isoformat() if end_time else None),
                "data": result,
            },
        )

    except NotImplementedError:

        return failure(
            symbol,
            "K线接口暂未实现",
        )

    except Exception as exc:

        print(f"❌ K线获取失败：" f"{symbol} -> {exc}")

        return failure(
            symbol,
            "K线数据暂不可用",
        )


# =========================================================
# 3. 财务数据
# =========================================================


@app.get("/api/financial/{symbol}")
def get_financial(symbol: str):

    symbol = symbol.strip().upper()

    print(f"💰 获取财务数据：{symbol}")

    try:

        manager = require_data()

        if not hasattr(
            manager,
            "get_financial",
        ):

            return failure(
                symbol,
                "财务接口暂未实现",
            )

        result = manager.get_financial(symbol)

        if result is None:

            return failure(
                symbol,
                "暂无财务数据",
            )

        return success(
            symbol,
            result,
        )

    except NotImplementedError:

        return failure(
            symbol,
            "财务接口暂未实现",
        )

    except Exception as exc:

        print(f"❌ 财务数据获取失败：" f"{symbol} -> {exc}")

        return failure(
            symbol,
            "财务数据暂不可用",
        )


# =========================================================
# 4. 估值数据
# =========================================================


@app.get("/api/valuation/{symbol}")
def get_valuation(symbol: str):

    symbol = symbol.strip().upper()

    print(f"💎 获取估值数据：{symbol}")

    try:

        manager = require_data()

        if not hasattr(
            manager,
            "get_valuation",
        ):

            return failure(
                symbol,
                "估值接口暂未实现",
            )

        valuation = manager.get_valuation(symbol)

        if valuation is None:

            return failure(
                symbol,
                "暂无估值数据",
            )
        else:
            print(valuation)

        return success(
            symbol,
            {
                "pe": getattr(
                    valuation,
                    "pe",
                    None,
                ),
                "peTtm": getattr(
                    valuation,
                    "pe_ttm",
                    None,
                ),
                "pb": getattr(
                    valuation,
                    "pb",
                    None,
                ),
                "ps": getattr(
                    valuation,
                    "ps",
                    None,
                ),
                "marketCap": getattr(
                    valuation,
                    "market_cap",
                    None,
                ),
                "roe": getattr(
                    valuation,
                    "roe",
                    None,
                ),
            },
        )

    except NotImplementedError:

        return failure(
            symbol,
            "估值接口暂未实现",
        )

    except Exception as exc:

        print(f"❌ 估值获取失败：" f"{symbol} -> {exc}")

        return failure(
            symbol,
            "估值数据暂不可用",
        )


# =========================================================
# 5. 行业数据
# =========================================================


@app.get("/api/industry/{symbol}")
def get_industry(symbol: str):

    symbol = symbol.strip().upper()

    print(f"🏭 获取行业数据：{symbol}")

    try:

        manager = require_data()

        if not hasattr(
            manager,
            "get_industry",
        ):

            return failure(
                symbol,
                "行业接口暂未实现",
            )

        industry = manager.get_industry(symbol)

        if industry is None:

            return failure(
                symbol,
                "暂无行业数据",
            )

        return success(
            symbol,
            industry,
        )

    except NotImplementedError:

        return failure(
            symbol,
            "行业接口暂未实现",
        )

    except Exception as exc:

        print(f"❌ 行业数据获取失败：" f"{symbol} -> {exc}")

        return failure(
            symbol,
            "行业数据暂不可用",
        )


# =========================================================
# 6. 技术指标
# =========================================================


@app.get("/api/technical/{symbol}")
def get_technical(symbol: str):

    symbol = symbol.strip().upper()

    print(f"📐 获取技术指标：{symbol}")

    try:

        manager = require_data()

        if not hasattr(
            manager,
            "get_technical",
        ):

            return failure(
                symbol,
                "技术指标接口暂未实现",
            )

        technical = manager.get_technical(symbol)

        if technical is None:

            return failure(
                symbol,
                "暂无技术指标数据",
            )

        return success(
            symbol,
            technical,
        )

    except NotImplementedError:

        return failure(
            symbol,
            "技术指标接口暂未实现",
        )

    except Exception as exc:

        print(f"❌ 技术指标获取失败：" f"{symbol} -> {exc}")

        return failure(
            symbol,
            "技术指标暂不可用",
        )


# =========================================================
# 7. 新闻
# =========================================================


@app.get("/api/news/{symbol}")
def get_news(
    symbol: str,
    limit: int = Query(
        10,
        ge=1,
        le=100,
    ),
):

    symbol = symbol.strip().upper()

    print(f"📰 获取新闻：" f"{symbol} limit={limit}")

    try:

        manager = require_data()

        if not hasattr(
            manager,
            "get_news",
        ):

            return failure(
                symbol,
                "新闻接口暂未实现",
            )

        news = manager.get_news(
            symbol,
            limit=limit,
        )

        if not news:

            return failure(
                symbol,
                "暂无新闻",
            )

        return success(
            symbol,
            news,
        )

    except NotImplementedError:

        return failure(
            symbol,
            "新闻接口暂未实现",
        )

    except Exception as exc:

        print(f"❌ 新闻获取失败：" f"{symbol} -> {exc}")

        return failure(
            symbol,
            "新闻数据暂不可用",
        )


# =========================================================
# 8. 公告
# =========================================================


@app.get("/api/announcement/{symbol}")
def get_announcements(
    symbol: str,
    limit: int = Query(
        10,
        ge=1,
        le=100,
    ),
):

    symbol = symbol.strip().upper()

    print(f"📢 获取公告：" f"{symbol} limit={limit}")

    try:

        manager = require_data()

        if not hasattr(
            manager,
            "get_announcements",
        ):

            return failure(
                symbol,
                "公告接口暂未实现",
            )

        announcements = manager.get_announcements(
            symbol,
            limit=limit,
        )

        if not announcements:

            return failure(
                symbol,
                "暂无公告",
            )

        return success(
            symbol,
            announcements,
        )

    except NotImplementedError:

        return failure(
            symbol,
            "公告接口暂未实现",
        )

    except Exception as exc:

        print(f"❌ 公告获取失败：" f"{symbol} -> {exc}")

        return failure(
            symbol,
            "公告数据暂不可用",
        )


# =========================================================
# 9. AI研究
# =========================================================


@app.get("/api/ai/{symbol}")
def get_ai_research(symbol: str):

    symbol = symbol.strip().upper()

    print(f"🤖 获取AI研究：{symbol}")

    try:

        manager = require_data()

        if not hasattr(
            manager,
            "get_ai_research",
        ):

            return failure(
                symbol,
                "AI研究接口暂未实现",
            )

        result = manager.get_ai_research(symbol)

        if result is None:

            return failure(
                symbol,
                "暂无AI研究数据",
            )

        return success(
            symbol,
            result,
        )

    except NotImplementedError:

        return failure(
            symbol,
            "AI研究接口暂未实现",
        )

    except Exception as exc:

        print(f"❌ AI研究获取失败：" f"{symbol} -> {exc}")

        return failure(
            symbol,
            "AI研究数据暂不可用",
        )


# ============================================================
# 静态文件
# ============================================================

app.mount(
    "/css",
    StaticFiles(directory=FRONTEND_DIR / "css"),
    name="css",
)

app.mount(
    "/js",
    StaticFiles(directory=FRONTEND_DIR / "js"),
    name="js",
)

app.mount(
    "/market",
    StaticFiles(
        directory=FRONTEND_DIR / "market",
        html=True,
    ),
    name="market",
)


app.mount(
    "/stock",
    StaticFiles(
        directory=FRONTEND_DIR / "stock",
        html=True,
    ),
    name="stock",
)

app.mount(
    "/trade",
    StaticFiles(
        directory=FRONTEND_DIR / "trade",
        html=True,
    ),
    name="trade",
)

app.mount(
    "/document",
    StaticFiles(
        directory=FRONTEND_DIR / "document",
        html=True,
    ),
    name="document",
)

app.mount(
    "/tools",
    StaticFiles(
        directory=FRONTEND_DIR / "tools",
        html=True,
    ),
    name="tools",
)

app.mount(
    "/news",
    StaticFiles(
        directory=FRONTEND_DIR / "news",
        html=True,
    ),
    name="news",
)

app.mount(
    "/research",
    StaticFiles(
        directory=FRONTEND_DIR / "research",
        html=True,
    ),
    name="research",
)


# ============================================================
# 首页
# ============================================================


@app.get("/")
def index():
    """
    返回股票研究中心首页。
    """

    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/api/stock/{symbol}/financial")
def get_stock_financial(symbol: str):

    try:
        data = financial_service.get_financial_data(symbol)

        return {
            "success": True,
            "data": data,
        }

    except Exception as exc:

        print(f"❌ 获取财务数据失败: " f"{symbol} - {exc}")

        return {
            "success": False,
            "message": str(exc),
            "data": None,
        }


# =========================================================
# Crypto：加密货币行情
# =========================================================


@app.get("/api/crypto/quote/{symbol:path}")
def get_crypto_quote(symbol: str):
    """
    获取加密货币实时行情。

    示例：

        /api/crypto/quote/BTC/USDT

    或：

        /api/crypto/quote/BTC-USDT
    """

    symbol = symbol.strip().upper()

    print(f"₿ 获取加密货币行情：{symbol}")

    try:
        manager = require_data()

        quote = manager.get_crypto_quote(symbol)

        if quote is None:
            return failure(
                symbol,
                "未获取到加密货币行情",
            )
        else:
            print(quote)

        return success(
            symbol,
            {
                "symbol": quote.symbol,
                "exchange": quote.exchange,
                "lastPrice": quote.last_price,
                "prevClose": quote.prev_close,
                "openPrice": quote.open_price,
                "highPrice": quote.high_price,
                "lowPrice": quote.low_price,
                "change": quote.change,
                "changePercent": quote.change_percent,
                "volume": quote.volume,
                "amount": quote.amount,
                "tradeCount": quote.trade_count,
                "source": quote.source,
                "timestamp": quote.timestamp,
            },
        )

    except NotImplementedError:

        return failure(
            symbol,
            "当前数据源暂未实现加密货币行情接口",
        )

    except Exception as exc:

        print(f"❌ 加密货币行情获取失败：" f"{symbol} -> {exc}")

        return failure(
            symbol,
            "加密货币行情暂不可用",
        )


@app.get("/api/crypto/quotes")
def get_crypto_quotes(
    symbols: str = Query(
        ...,
        description="交易对，逗号分隔，例如 BTC/USDT,ETH/USDT,BNB/USDT",
    ),
):
    """
    批量获取加密货币行情。

    示例：

        /api/crypto/quotes?symbols=BTC/USDT,ETH/USDT,BNB/USDT
    """

    symbol_list = [item.strip().upper() for item in symbols.split(",") if item.strip()]

    if not symbol_list:
        return {
            "success": False,
            "message": "未指定交易对",
            "data": [],
        }

    print(f"₿ 批量获取加密货币行情：" f"{', '.join(symbol_list)}")

    try:
        manager = require_data()

        quotes = manager.get_crypto_quotes(symbol_list)

        result = []

        for quote in quotes:
            result.append(
                {
                    "symbol": quote.symbol,
                    "exchange": quote.exchange,
                    "lastPrice": quote.last_price,
                    "prevClose": quote.prev_close,
                    "openPrice": quote.open_price,
                    "highPrice": quote.high_price,
                    "lowPrice": quote.low_price,
                    "change": quote.change,
                    "changePercent": quote.change_percent,
                    "volume": quote.volume,
                    "amount": quote.amount,
                    "tradeCount": quote.trade_count,
                    "source": quote.source,
                    "timestamp": quote.timestamp,
                }
            )

        return {
            "success": True,
            "data": result,
        }

    except Exception as exc:

        print(f"❌ 批量获取加密货币行情失败：" f"{exc}")

        return {
            "success": False,
            "message": "获取加密货币行情失败",
            "data": [],
        }


# =========================================================
# Crypto：K线
# =========================================================


@app.get("/api/crypto/kline/{symbol:path}")
def get_crypto_kline(
    symbol: str,
    interval: str = Query(
        "1d",
        description="K线周期，例如 1m/5m/15m/30m/1h/4h/1d/1w",
    ),
    limit: int = Query(
        100,
        ge=1,
        le=1000,
        description="K线数量",
    ),
):
    """
    获取加密货币 K 线。
    """

    symbol = symbol.strip().upper()

    print(f"📊 获取加密货币K线：" f"{symbol} " f"interval={interval} " f"limit={limit}")

    try:
        manager = require_data()

        klines = manager.get_crypto_klines(
            symbol=symbol,
            interval=interval,
            limit=limit,
        )

        if not klines:
            return failure(
                symbol,
                "暂无加密货币K线数据",
            )

        result = []

        for item in klines:
            result.append(
                {
                    "timestamp": (
                        item.timestamp.isoformat() if item.timestamp else None
                    ),
                    "open": item.open,
                    "high": item.high,
                    "low": item.low,
                    "close": item.close,
                    "volume": item.volume,
                    "amount": item.amount,
                    "closeTime": (
                        item.close_time.isoformat() if item.close_time else None
                    ),
                    "tradeCount": item.trade_count,
                }
            )

        return success(
            symbol,
            {
                "interval": interval,
                "data": result,
            },
        )

    except Exception as exc:

        print(f"❌ 加密货币K线获取失败：" f"{symbol} -> {exc}")

        return failure(
            symbol,
            "加密货币K线数据暂不可用",
        )


# =========================================================
# Crypto：订单簿
# =========================================================


@app.get("/api/crypto/order-book/{symbol:path}")
def get_crypto_order_book(
    symbol: str,
    limit: int = Query(
        20,
        ge=1,
        le=100,
    ),
):
    """
    获取加密货币订单簿。
    """

    symbol = symbol.strip().upper()

    print(f"📖 获取加密货币订单簿：" f"{symbol} limit={limit}")

    try:
        manager = require_data()

        order_book = manager.get_crypto_order_book(
            symbol=symbol,
            limit=limit,
        )

        return success(
            symbol,
            order_book,
        )

    except Exception as exc:

        print(f"❌ 加密货币订单簿获取失败：" f"{symbol} -> {exc}")

        return failure(
            symbol,
            "加密货币订单簿暂不可用",
        )
