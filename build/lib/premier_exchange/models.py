from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from uuid import uuid4


class AssetClass(str, Enum):
    CRYPTO = "crypto"
    EQUITY = "equity"
    ETF = "etf"


class OrderSide(str, Enum):
    BUY = "buy"
    SELL = "sell"


class OrderType(str, Enum):
    MARKET = "market"
    LIMIT = "limit"


class OrderStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    FILLED = "filled"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class Asset:
    symbol: str
    asset_class: AssetClass
    jurisdiction: str
    exchange: str


@dataclass
class Order:
    asset: Asset
    side: OrderSide
    quantity: Decimal
    order_type: OrderType
    limit_price: Decimal | None = None
    id: str = field(default_factory=lambda: str(uuid4()))
    status: OrderStatus = OrderStatus.PENDING
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if self.quantity <= 0:
            raise ValueError("quantity must be positive")
        if self.order_type is OrderType.LIMIT and (self.limit_price is None or self.limit_price <= 0):
            raise ValueError("limit orders require a positive limit_price")


@dataclass(frozen=True)
class Position:
    symbol: str
    quantity: Decimal
    average_price: Decimal


@dataclass(frozen=True)
class Signal:
    symbol: str
    side: OrderSide
    confidence: Decimal
    rationale: str = ""


@dataclass(frozen=True)
class AuditEvent:
    event_type: str
    payload: dict
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
