"""Small local web dashboard for monitoring and controlling a paper engine."""

from __future__ import annotations

import json
from decimal import Decimal, InvalidOperation
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from .engine import TradingEngine
from .models import Order, OrderSide, OrderType


class Dashboard:
    """Expose a paper engine through a deliberately local, dependency-free UI."""

    def __init__(self, engine: TradingEngine, cash: Decimal = Decimal("100000")):
        self.engine = engine
        self.cash = cash
        self.started_value = cash

    def portfolio(self) -> dict[str, Any]:
        positions = []
        invested = Decimal("0")
        market_value = Decimal("0")
        for symbol, position in self.engine.positions.items():
            price = self.engine.market.price(next(a for a in self.engine.config.supported_assets if a.symbol == symbol))
            value = position.quantity * price
            cost = position.quantity * position.average_price
            invested += cost
            market_value += value
            positions.append({
                "symbol": symbol,
                "quantity": str(position.quantity),
                "average_price": str(position.average_price),
                "price": str(price),
                "value": str(value),
                "pnl": str(value - cost),
            })
        equity = self.cash + market_value
        return {
            "cash": str(self.cash),
            "equity": str(equity),
            "market_value": str(market_value),
            "invested": str(invested),
            "pnl": str(equity - self.started_value),
            "kill_switch": self.engine.risk.kill_switch,
            "open_orders": len(self.engine.open_orders),
            "positions": positions,
            "prices": {asset.symbol: str(self.engine.market.price(asset)) for asset in self.engine.config.supported_assets},
        }

    def submit_order(self, payload: dict[str, Any]) -> dict[str, Any]:
        symbol = str(payload.get("symbol", "")).upper()
        asset = next((a for a in self.engine.config.supported_assets if a.symbol == symbol), None)
        if asset is None:
            raise ValueError(f"unsupported asset: {symbol}")
        try:
            quantity = Decimal(str(payload["quantity"]))
        except (KeyError, InvalidOperation) as exc:
            raise ValueError("quantity must be a positive number") from exc
        side = OrderSide(str(payload.get("side", "")).lower())
        order = self.engine.execute(Order(asset, side, quantity, OrderType.MARKET))
        return {"id": order.id, "symbol": symbol, "side": side.value, "quantity": str(quantity), "status": order.status.value}


def make_handler(dashboard: Dashboard, static_file: Path):
    class Handler(BaseHTTPRequestHandler):
        def _send(self, status: int, body: str, content_type: str = "application/json") -> None:
            encoded = body.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", f"{content_type}; charset=utf-8")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)

        def do_GET(self) -> None:
            path = urlparse(self.path).path
            if path == "/api/portfolio":
                self._send(200, json.dumps(dashboard.portfolio()))
            elif path == "/" or path == "/dashboard.html":
                self._send(200, static_file.read_text(), "text/html")
            else:
                self._send(404, json.dumps({"error": "not found"}))

        def do_POST(self) -> None:
            path = urlparse(self.path).path
            try:
                length = int(self.headers.get("Content-Length", "0"))
                payload = json.loads(self.rfile.read(length) or b"{}")
                if path == "/api/orders":
                    result = dashboard.submit_order(payload)
                elif path == "/api/kill-switch":
                    if bool(payload.get("halt")):
                        dashboard.engine.risk.halt()
                    else:
                        dashboard.engine.risk.resume()
                    result = {"kill_switch": dashboard.engine.risk.kill_switch}
                else:
                    self._send(404, json.dumps({"error": "not found"}))
                    return
                self._send(200, json.dumps(result))
            except (ValueError, json.JSONDecodeError) as exc:
                self._send(400, json.dumps({"error": str(exc)}))

        def log_message(self, *_args: Any) -> None:
            return

    return Handler


def serve(engine: TradingEngine, host: str = "127.0.0.1", port: int = 8080) -> None:
    """Serve the dashboard until interrupted."""
    static_file = Path(__file__).with_name("dashboard.html")
    server = ThreadingHTTPServer((host, port), make_handler(Dashboard(engine), static_file))
    print(f"Dashboard available at http://{host}:{port}")
    try:
        server.serve_forever()
    finally:
        server.server_close()
