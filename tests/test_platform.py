from decimal import Decimal

import pytest
from cryptography.fernet import Fernet

from premier_exchange.adapters import PaperBroker
from premier_exchange.config import PlatformConfig, RiskLimits
from premier_exchange.engine import TradingEngine
from premier_exchange.models import Asset, AssetClass, Order, OrderSide, OrderType, Signal
from premier_exchange.security import SecretStore


def asset():
    return Asset("BTC-USD", AssetClass.CRYPTO, "US", "paper")


def test_secret_store_round_trips():
    store = SecretStore(Fernet.generate_key())
    store.put("broker-key", "not-a-loggable-secret")
    assert store.get("broker-key") == "not-a-loggable-secret"


def test_engine_rejects_order_over_limit():
    broker = PaperBroker({"BTC-USD": Decimal("100")})
    config = PlatformConfig(
        supported_assets=(asset(),),
        jurisdictions=("US",),
        allowed_exchanges=("paper",),
        risk_limits=RiskLimits(max_order_notional=Decimal("50")),
    )
    engine = TradingEngine(config, broker, broker)
    with pytest.raises(ValueError, match="max order notional"):
        engine.execute(Order(asset(), OrderSide.BUY, Decimal("1"), OrderType.MARKET))


def test_low_confidence_signal_is_not_executed():
    broker = PaperBroker({"BTC-USD": Decimal("100")})
    engine = TradingEngine(PlatformConfig(supported_assets=(asset(),)), broker, broker)
    with pytest.raises(ValueError, match="confidence"):
        engine.execute_signal(
            Signal("BTC-USD", OrderSide.BUY, Decimal("0.49")), Decimal("0.1"), asset()
        )


def test_kill_switch_halts_orders():
    broker = PaperBroker({"BTC-USD": Decimal("100")})
    engine = TradingEngine(PlatformConfig(supported_assets=(asset(),)), broker, broker)
    engine.risk.halt()
    with pytest.raises(ValueError, match="kill switch"):
        engine.execute(Order(asset(), OrderSide.BUY, Decimal("0.1"), OrderType.MARKET))
