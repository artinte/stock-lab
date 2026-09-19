from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from infra.data_manager import DataManager
from infra.service.stock_financial_service import StockFinancialService
from infra.service.youtube_service import YouTubeService

from infra.service import app_state

from infra.service.routers.system import router as system_router
from infra.service.routers.stock import router as stock_router
from infra.service.routers.crypto import router as crypto_router
from infra.service.routers.youtube import router as youtube_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("=" * 60)
    print("正在启动 STOCK LAB 服务...")
    print("=" * 60)

    try:
        # ====================================================
        # 股票 / Crypto 数据服务
        # ====================================================

        app_state.data = DataManager("yinhe")
        app_state.data.start()

        app_state.financial_service = StockFinancialService(
            app_state.data
        )

        print("✅ 股票 / Crypto 数据服务启动成功")

        # ====================================================
        # YouTube 信息流服务
        # ====================================================

        app_state.youtube_service = YouTubeService()

        print("✅ YouTube 信息流服务启动成功")

        yield

    finally:
        print("=" * 60)
        print("正在关闭 STOCK LAB 服务...")
        print("=" * 60)

        # ====================================================
        # YouTube
        # ====================================================

        if app_state.youtube_service is not None:
            try:
                app_state.youtube_service.stop()
            except Exception as exc:
                print(f"⚠️ YouTube 服务关闭失败：{exc}")
            finally:
                app_state.youtube_service = None

        # ====================================================
        # 数据服务
        # ====================================================

        if app_state.data is not None:
            try:
                app_state.data.stop()
            except Exception as exc:
                print(f"⚠️ 数据服务关闭失败：{exc}")
            finally:
                app_state.data = None

        app_state.financial_service = None


app = FastAPI(
    title="STOCK LAB API",
    description="股票、加密货币与信息流研究 API",
    version="1.0.0",
    lifespan=lifespan,
)


# ============================================================
# API Routers
# ============================================================

app.include_router(system_router)
app.include_router(stock_router)
app.include_router(crypto_router)
app.include_router(youtube_router)


# ============================================================
# Static Files
# ============================================================

FRONTEND_DIR = Path("docs")


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
# Root
# ============================================================

@app.get("/")
def index():
    return FileResponse(
        FRONTEND_DIR / "index.html"
    )