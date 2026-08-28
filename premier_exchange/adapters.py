from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import replace
from decimal import Decimal

from .models import Asset, Order, OrderStatus


class MarketDataAdapter(ABC):
    @abstractmethod
    def price(self, asset: Asset) -> Decimal: ...


class TradingAdapter(ABC):
    @abstractmethod
    def submit(self, order: Order) -> Order: ...

    @abstractmethod
    def cancel(self, order_id: str) -> None: ...


class PaperBroker(MarketDataAdapter, TradingAdapter):
    """Deterministic adapter for simulations and paper trading."""

    def __init__(self, prices: dict[str, Decimal]):
        self.prices = prices
        self.orders: dict[str, Order] = {}

    def price(self, asset: Asset) -> Decimal:
        try:
            return self.prices[asset.symbol]
        except KeyError as exc:
            raise ValueError(f"no market price for {asset.symbol}") from exc

    def submit(self, order: Order) -> Order:
        accepted = replace(order, status=OrderStatus.ACCEPTED)
        self.orders[accepted.id] = accepted
        return accepted

    def cancel(self, order_id: str) -> None:
        if order_id in self.orders:
            self.orders[order_id].status = OrderStatus.CANCELLED
