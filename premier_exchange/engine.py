from decimal import Decimal

from .adapters import MarketDataAdapter, TradingAdapter
from .config import PlatformConfig
from .models import AuditEvent, Order, OrderSide, OrderType, Position, Signal, OrderStatus
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
        self.open_orders: set[str] = set()

    def execute(self, order: Order):
        price = self.market.price(order.asset)
        self.risk.validate(order, price, self.positions, open_orders=len(self.open_orders))
        submitted = self.broker.submit(order)
        self.open_orders.discard(submitted.id)
        if submitted.status is OrderStatus.FILLED:
            current = self.positions.get(order.asset.symbol)
            old_quantity = current.quantity if current else Decimal("0")
            signed_quantity = order.quantity if order.side is OrderSide.BUY else -order.quantity
            new_quantity = old_quantity + signed_quantity
            if new_quantity:
                if current and signed_quantity > 0:
                    total_cost = current.quantity * current.average_price + order.quantity * price
                    average_price = total_cost / new_quantity
                else:
                    average_price = current.average_price if current else price
                self.positions[order.asset.symbol] = Position(order.asset.symbol, new_quantity, average_price)
            else:
                self.positions.pop(order.asset.symbol, None)
        else:
            self.open_orders.add(submitted.id)
        self.audit_log.append(AuditEvent("order_submitted", {"order_id": order.id, "symbol": order.asset.symbol}))
        return submitted

    def execute_signal(self, signal: Signal, quantity: Decimal, asset):
        if signal.confidence < Decimal("0") or signal.confidence > Decimal("1"):
            raise ValueError("signal confidence must be between 0 and 1")
        if signal.confidence < Decimal("0.5"):
            raise ValueError("signal confidence is below execution threshold")
        return self.execute(Order(asset, signal.side, quantity, OrderType.MARKET))
