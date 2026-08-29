"""Command-line entry point for the local paper trading dashboard."""

from __future__ import annotations

import argparse
from decimal import Decimal
from typing import Sequence

from .adapters import PaperBroker
from .config import PlatformConfig
from .dashboard import serve
from .engine import TradingEngine
from .models import Asset, AssetClass


def build_engine() -> TradingEngine:
    """Build the default paper-trading engine used by the local app."""
    asset = Asset("BTC-USD", AssetClass.CRYPTO, "US", "paper")
    broker = PaperBroker({asset.symbol: Decimal("100")})
    return TradingEngine(PlatformConfig(supported_assets=(asset,)), broker, broker)


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run the local paper trading dashboard.")
    parser.add_argument("--host", default="127.0.0.1", help="interface to bind (default: 127.0.0.1)")
    parser.add_argument("--port", default=8080, type=int, help="port to bind (default: 8080)")
    args = parser.parse_args(argv)
    serve(build_engine(), host=args.host, port=args.port)
