from decimal import Decimal

from .adapters import MarketDataAdapter, TradingAdapter
from .config import PlatformConfig
from .models import Asset, AuditEvent, Order, OrderSide, OrderStatus, OrderType, Position, Signal
from .risk import RiskEngine

SIGNAL_CONFIDENCE_THRESHOLD = Decimal("0.5")


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
        self.daily_loss = Decimal("0")

    def execute(self, order: Order) -> Order:
        price = self.market.price(order.asset)
        self.risk.validate(
            order, price, self.positions, open_orders=len(self.open_orders), daily_loss=self.daily_loss
        )
        submitted = self.broker.submit(order)
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

    def execute_signal(self, signal: Signal, quantity: Decimal, asset: Asset) -> Order:
        if signal.confidence < Decimal("0") or signal.confidence > Decimal("1"):
            raise ValueError("signal confidence must be between 0 and 1")
        if signal.confidence < SIGNAL_CONFIDENCE_THRESHOLD:
            raise ValueError("signal confidence is below execution threshold")
        return self.execute(Order(asset, signal.side, quantity, OrderType.MARKET))

    def record_daily_loss(self, amount: Decimal) -> None:
        if amount < 0:
            raise ValueError("daily loss must not be negative")
        self.daily_loss = amount
