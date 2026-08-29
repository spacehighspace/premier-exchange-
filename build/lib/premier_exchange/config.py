from dataclasses import dataclass, field
from decimal import Decimal

from .models import Asset


@dataclass(frozen=True)
class RiskLimits:
    max_order_notional: Decimal = Decimal("1000")
    max_position_notional: Decimal = Decimal("5000")
    max_daily_loss: Decimal = Decimal("250")
    max_open_orders: int = 5


@dataclass
class PlatformConfig:
    """Explicit operating boundary; live trading remains opt-in and disabled by default."""

    supported_assets: tuple[Asset, ...] = ()
    jurisdictions: tuple[str, ...] = ()
    allowed_exchanges: tuple[str, ...] = ()
    risk_limits: RiskLimits = field(default_factory=RiskLimits)
    portfolio_objective: str = "capital preservation with bounded risk"
    paper_trading: bool = True
    live_trading_enabled: bool = False

    def validate(self) -> None:
        if self.live_trading_enabled and self.paper_trading:
            raise ValueError("paper_trading and live_trading_enabled cannot both be true")
        if self.live_trading_enabled:
            raise ValueError("live trading requires an explicit production deployment review")
        for asset in self.supported_assets:
            if self.jurisdictions and asset.jurisdiction not in self.jurisdictions:
                raise ValueError(f"{asset.symbol} is outside configured jurisdictions")
            if self.allowed_exchanges and asset.exchange not in self.allowed_exchanges:
                raise ValueError(f"{asset.symbol} is on an unsupported exchange")
