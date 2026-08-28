# premier-exchange-

Paper-first foundation for a monitored, automated trading platform.

## Safety boundary

This project is not financial advice and does not promise profit. It defaults to
paper trading, has no live broker integration, and rejects enabling live trading
from application configuration. Production use requires reviewed broker and
custody controls, jurisdiction and tax review, and operational approval.

The package provides explicit asset/exchange/jurisdiction configuration,
encrypted API-secret storage, common market-data and trading adapter interfaces,
a deterministic paper broker, order/risk validation, audit events, a kill switch,
and bounded signal execution.

## Development

```bash
python -m pip install -e . pytest
pytest
```

Before live use, add backtesting with fees/slippage, reconciliation, monitoring
and alerts, immutable audit persistence, access controls, failure-recovery tests,
regulatory/tax/custody review, and a staged paper-to-limited-funds rollout.

## Paper portfolio dashboard

The dependency-free dashboard can be mounted on a configured `TradingEngine`:

```python
from premier_exchange.dashboard import serve

serve(engine)  # open http://127.0.0.1:8080
```

To run the default paper-trading app directly:

```bash
python -m premier_exchange
# or, after installation:
premier-exchange
```

It refreshes portfolio prices and P&L every five seconds and supports paper orders
and the risk kill switch. It intentionally binds to localhost and never enables
live trading.