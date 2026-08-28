from decimal import Decimal

from .adapters import MarketDataAdapter, TradingAdapter
from .config import PlatformConfig
from .models import AuditEvent, Order, Signal
from .risk import RiskEngine


class TradingEngine:
    def __init__(self, config: PlatformConfig, market: MarketDataAdapter, broker: TradingAdapter):
        config.validate()
        self.config = config
        self.market = market
        self.broker = broker
        self.risk = RiskEngine(config.risk_limits)
        self.audit_log: list[AuditEvent] = []
        self.positions = {}

    def execute(self, order: Order):
        price = self.market.price(order.asset)
        self.risk.validate(order, price, self.positions)
        submitted = self.broker.submit(order)
        self.audit_log.append(AuditEvent("order_submitted", {"order_id": order.id, "symbol": order.asset.symbol}))
        return submitted

    def execute_signal(self, signal: Signal, quantity: Decimal, asset):
        if not Decimal("0") <= signal.confidence <= Decimal("1"):
            raise ValueError("signal confidence must be between 0 and 1")
        if signal.confidence < Decimal("0.5"):
            raise ValueError("signal confidence is below execution threshold")
        from .models import OrderSide, OrderType
        return self.execute(Order(asset, signal.side, quantity, OrderType.MARKET))
