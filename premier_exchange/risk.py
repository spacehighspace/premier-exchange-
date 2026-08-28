from decimal import Decimal

from .config import RiskLimits
from .models import Order, OrderSide, Position


class RiskEngine:
    def __init__(self, limits: RiskLimits):
        self.limits = limits
        self.kill_switch = False

    def halt(self) -> None:
        self.kill_switch = True

    def resume(self) -> None:
        self.kill_switch = False

    def validate(
        self,
        order: Order,
        price: Decimal,
        positions: dict[str, Position],
        open_orders: int = 0,
        daily_loss: Decimal = Decimal("0"),
    ) -> None:
        if self.kill_switch:
            raise ValueError("trading halted by kill switch")
        notional = order.quantity * price
        if notional > self.limits.max_order_notional:
            raise ValueError("order exceeds max order notional")
        if open_orders >= self.limits.max_open_orders:
            raise ValueError("open order limit reached")
        if daily_loss >= self.limits.max_daily_loss:
            raise ValueError("daily loss limit reached")
        current = positions.get(order.asset.symbol)
        quantity = (current.quantity if current else Decimal("0"))
        projected = quantity + order.quantity if order.side is OrderSide.BUY else quantity - order.quantity
        if projected * price > self.limits.max_position_notional:
            raise ValueError("position limit exceeded")
        if projected < 0:
            raise ValueError("cannot sell more than the current position")
