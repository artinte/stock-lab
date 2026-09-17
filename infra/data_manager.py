from __future__ import annotations

from typing import Optional

from infra.registry import GatewayRegistry
from infra.gateways.crypto_data import CryptoDataGateway
from infra.gateways.forex_data import ForexDataGateway
from infra.gateways.stock_data import StockDataGateway
from infra.managers.stock_manager import StockManager
from infra.managers.crypto_manager import CryptoManager
from infra.managers.forex_manager import ForexManager
from infra.service.industry_service import IndustryService


class DataManager:
    """
    统一数据管理器。

    DataManager 只负责：

    - 创建各类数据 Gateway
    - 创建各领域 Manager
    - 管理数据源生命周期
    - 对外提供各领域 Manager

    具体业务方法由对应的 Manager 负责。
    """

    DEFAULT_STOCK_PROVIDER = "yinhe"
    DEFAULT_CRYPTO_PROVIDER = "binance"

    def __init__(
        self,
        provider_name: str = DEFAULT_STOCK_PROVIDER,
        config: Optional[dict] = None,
        crypto_provider_name: str = DEFAULT_CRYPTO_PROVIDER,
        forex_provider_name: str | None = None,
    ) -> None:
        self.config = config or {}

        # --------------------------------------------------
        # 股票
        # --------------------------------------------------

        self.stock_provider = provider_name.strip().lower()

        stock_gateway: StockDataGateway = GatewayRegistry.create(
            self.stock_provider,
            self.config,
        )

        self.stock = StockManager(stock_gateway)

        # --------------------------------------------------
        # 加密货币
        # --------------------------------------------------

        self.crypto_provider = crypto_provider_name.strip().lower()

        crypto_gateway: CryptoDataGateway = GatewayRegistry.create(
            self.crypto_provider,
            self.config,
        )

        self.crypto = CryptoManager(crypto_gateway)

        # --------------------------------------------------
        # 外汇
        # --------------------------------------------------

        self.forex = None

        if forex_provider_name:
            self.forex_provider = forex_provider_name.strip().lower()

            forex_gateway: ForexDataGateway = GatewayRegistry.create(
                self.forex_provider,
                self.config,
            )

            self.forex = ForexManager(forex_gateway)

        # --------------------------------------------------
        # 行业服务
        # --------------------------------------------------

        self.industry = IndustryService()

    # ======================================================
    # 生命周期管理
    # ======================================================

    def start(self) -> bool:
        """启动所有已配置的数据源。"""

        results: list[bool] = []

        gateways = [
            self.stock.gateway,
            self.crypto.gateway,
        ]

        if self.forex is not None:
            gateways.append(self.forex.gateway)

        for gateway in gateways:
            login_method = getattr(gateway, "login", None)

            if callable(login_method):
                results.append(bool(login_method(self.config)))
            else:
                results.append(True)

        return all(results)

    def stop(self) -> None:
        """停止所有已配置的数据源。"""

        gateways = [
            self.stock.gateway,
            self.crypto.gateway,
        ]

        if self.forex is not None:
            gateways.append(self.forex.gateway)

        for gateway in gateways:
            logout_method = getattr(gateway, "logout", None)

            if callable(logout_method):
                logout_method()

    def health_check(self) -> bool:
        """检查所有已配置的数据源。"""

        gateways = [
            self.stock.gateway,
            self.crypto.gateway,
        ]

        if self.forex is not None:
            gateways.append(self.forex.gateway)

        results: list[bool] = []

        for gateway in gateways:
            health_method = getattr(gateway, "health_check", None)

            if callable(health_method):
                results.append(bool(health_method()))
            else:
                results.append(True)

        return all(results)

    @classmethod
    def available_providers(cls) -> list[str]:
        """返回已注册的数据源名称。"""

        return GatewayRegistry.names()
