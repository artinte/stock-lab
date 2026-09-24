import os
import sys
import pytest
from fastapi.testclient import TestClient

"""
python -m tests.service.test_fastapi
"""

# ============================================================
# 1. 添加项目根目录
# ============================================================

CURRENT_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

PROJECT_ROOT = os.path.abspath(
    os.path.join(CURRENT_DIR, "..")
)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


# ============================================================
# 2. 导入 FastAPI
# ============================================================

from infra.service.api import app


# ============================================================
# 3. 一次启动 FastAPI
# ============================================================

@pytest.fixture(scope="module")
def client():

    print("\n")
    print("=" * 60)
    print("🚀 开始启动真实 FastAPI 测试服务")
    print("=" * 60)

    with TestClient(app) as client:

        print("✅ FastAPI + DataManager 启动成功")
        print()

        yield client

    print()
    print("=" * 60)
    print("🛑 FastAPI 测试服务已关闭")
    print("=" * 60)


# ============================================================
# 4. 健康检查
# ============================================================

def test_health(client):

    response = client.get(
        "/api/health"
    )

    print("📡 /api/health")
    print(response.json())

    assert response.status_code == 200


# ============================================================
# 5. 股票行情
# ============================================================


def test_stock(client):
    response = client.get(
        "/api/stock/600519"
    )

    print("\n📈 /api/stock/600519")
    print(response.json())

    assert response.status_code == 200

def test_quote(client):

    response = client.get(
        "/api/quote/600519"
    )

    print("\n📈 /api/quote/600519")
    print(response.json())

    assert response.status_code == 200


# ============================================================
# 6. K线
# ============================================================

def test_kline(client):

    response = client.get(
        "/api/kline/600519"
        "?interval=1d&limit=10"
    )

    print("\n📊 /api/kline/600519")
    print(response.json())

    assert response.status_code == 200


# ============================================================
# 7. 财务
# ============================================================

def test_financial(client):

    response = client.get(
        "/api/financial/600519"
    )

    print("\n💰 /api/financial/600519")
    print(response.json())

    assert response.status_code == 200


# ============================================================
# 8. 估值
# ============================================================

def test_valuation(client):

    response = client.get(
        "/api/valuation/600519"
    )

    print("\n💎 /api/valuation/600519")
    print(response.json())

    assert response.status_code == 200


# ============================================================
# 9. 行业
# ============================================================

def test_industry(client):

    response = client.get(
        "/api/industry/600519"
    )

    print("\n🏭 /api/industry/600519")
    print(response.json())

    assert response.status_code == 200


# ============================================================
# 10. 技术指标
# ============================================================

def test_technical(client):

    response = client.get(
        "/api/technical/600519"
    )

    print("\n📐 /api/technical/600519")
    print(response.json())

    assert response.status_code == 200


# ============================================================
# 11. 新闻
# ============================================================

def test_news(client):

    response = client.get(
        "/api/news/600519?limit=10"
    )

    print("\n📰 /api/news/600519")
    print(response.json())

    assert response.status_code == 200


# ============================================================
# 12. 公告
# ============================================================

def test_announcement(client):

    response = client.get(
        "/api/announcement/600519?limit=10"
    )

    print("\n📢 /api/announcement/600519")
    print(response.json())

    assert response.status_code == 200


# ============================================================
# 13. AI研究
# ============================================================

def test_ai(client):

    response = client.get(
        "/api/ai/600519"
    )

    print("\n🤖 /api/ai/600519")
    print(response.json())

    assert response.status_code == 200


# ============================================================
# 14. 指数
# ============================================================

def test_indices(client):

    response = client.get(
        "/api/indices"
        "?indices=000001,399001,399006,000688"
    )

    print("\n📊 /api/indices")
    print(response.json())

    assert response.status_code == 200


# ============================================================
# 15. 直接运行
# ============================================================

if __name__ == "__main__":

    print("🚀 开始运行真实接口测试...\n")

    exit_code = pytest.main(
        [
            "-v",
            "-s",
            __file__,
        ]
    )

    if exit_code == 0:
        print("\n✅ 所有测试通过！")
    else:
        print("\n❌ 测试失败！")
