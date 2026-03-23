# Tools & Libraries

## Alpaca Markets

**What it is:** A commission-free brokerage with a full REST API for automated trading. Used for both paper trading (simulated) and live trading.

**Why we use it:**
- Free paper trading account with real-time market data
- Supports bracket orders natively — one API call places the entry, stop loss, and take profit simultaneously
- The same code works for paper and live trading (just change the base URL)
- No Pattern Day Trader (PDT) restrictions on paper accounts
- Python SDK (`alpaca-py`) is well-maintained

**How we use it:**
- `TradingClient` — place orders, check positions, close positions
- `GetAssetsRequest` — fetch the full list of tradeable US equities for universe building
- Bracket orders with `OrderClass.BRACKET` — entry limit + stop + target in one atomic call
- `client_order_id` prefix (`mr_`, `mo_`, `bo_`) — track which orders belong to which strategy

**Key concept — Bracket Orders:**
```
Entry limit order at $50.00
  ├── Stop loss: sell if price drops to $47.50
  └── Take profit: sell if price rises to $56.00
```
Once placed, the broker manages both exits. You don't need to monitor the position.

**Paper vs Live:** Controlled by the base URL in `.env`:
- Paper: `https://paper-api.alpaca.markets/v2`
- Live: `https://api.alpaca.markets/v2`

---

## yfinance

**What it is:** A Python library that downloads historical market data from Yahoo Finance. Free, no API key required.

**Why we use it:**
- Free unlimited historical daily OHLCV (Open, High, Low, Close, Volume) data
- Covers all US-listed equities going back 10+ years
- Simple batch download — pass a list of 500 symbols and get all their data in one call
- Good enough for daily signal computation

**How we use it:**
- `yf.download(symbols, start, end)` — bulk download daily bars
- Used in `data/fetch.py` in batches of 500 with a 3-second delay between batches to avoid rate limiting

**Limitations:**
- Rate limits at ~500 symbols per request before Yahoo throttles
- Slight data delays — not suitable for intraday or real-time signals
- Occasionally missing data for thinly traded stocks

**When to upgrade:** When moving to live trading with real capital, consider **Polygon.io** ($29/month) for clean, institutional-grade data with no rate limits.

---

## ta (Technical Analysis Library)

**What it is:** A Python library (`pip install ta`) that computes technical indicators from OHLCV DataFrames.

**Why we use it:**
- Clean pandas-native API — accepts Series, returns Series
- Well-maintained and compatible with pandas 3.x
- Covers all indicators we need: RSI, Bollinger Bands, ADX

**How we use it:**

| Indicator | Class | Used In |
|---|---|---|
| RSI(2) | `ta.momentum.RSIIndicator(close, window=2)` | Mean Reversion |
| Bollinger Bands | `ta.volatility.BollingerBands(close, window=20, window_dev=2)` | Mean Reversion |
| ADX(14) | `ta.trend.ADXIndicator(high, low, close, window=14)` | Momentum |

**ATR** is computed manually in `data/fetch.py` using the standard formula rather than the library, for direct control over the calculation.

---

## pandas & numpy

**What they are:** The foundation of Python data science.
- `pandas` — DataFrames for tabular data, time series operations
- `numpy` — numerical operations, NaN handling, percentile calculations

**How we use them:**
- All OHLCV data is stored as pandas DataFrames
- Rolling averages (`rolling(20).mean()`), EWM (`ewm(span=21)`), rank (`rank(pct=True)`)
- numpy for NaN checks (`np.isnan()`), percentile filtering (`np.percentile()`)

---

## python-dotenv

**What it is:** Loads environment variables from a `.env` file into `os.environ`.

**Why:** All secrets (API keys, passwords) live in `.env` which is gitignored. The code reads them via `os.getenv()`. This means secrets never appear in source code or version control.

---

## smtplib (Standard Library)

**What it is:** Python's built-in SMTP email library — no external package needed.

**How we use it:**
- Gmail SMTP over TLS (port 587)
- HTML emails for scan summaries (styled table with signals)
- Plain traceback emails for errors
- Uses Gmail App Password (not account password) for authentication

**Two email types:**
1. **Scan complete** — sent at end of every scan (dry run or live). Shows all signals per strategy, which were placed, portfolio value.
2. **Error alert** — sent immediately when any exception is caught. Includes full Python traceback.

---

## claude-agent-sdk

**What it is:** The official Claude Code Agent SDK — lets Python scripts spawn a Claude agent that uses your existing Claude Code subscription to do real work (read files, write files, run edits). No separate Anthropic API key or billing needed.

**Why we use it (and not the `anthropic` SDK):**
- The `anthropic` SDK requires an `ANTHROPIC_API_KEY` and bills per token — every doc update would cost money
- `claude-agent-sdk` routes through your Claude Code CLI session — same model, zero extra cost
- It gives the agent full access to built-in tools: `Read`, `Write`, `Edit`

**How we use it:**
- `agents/docs_agent.py` uses `query()` from `claude_agent_sdk` to run an agent with `permission_mode="acceptEdits"` that reads changed source files (via git diff) and rewrites the relevant `docs/` files
- The agent is invoked with `allowed_tools=["Read", "Write", "Edit"]` so it can only touch files — no shell access
- Can also invoke the same logic as the `/update-docs` slash command directly inside Claude Code

**Usage:**
```bash
# Auto-detect changes since last commit
python agents/docs_agent.py

# Only staged changes
python agents/docs_agent.py --staged

# Specific files
python agents/docs_agent.py --files strategies/mean_reversion.py
```

---

## Architecture: How Everything Connects

```
scanner/scan.py          ← entry point, run daily pre-market (7:30 AM CDT)
       │
       ├── data/universe.py      ← get list of ~2,856 liquid US stocks (cached weekly)
       ├── data/fetch.py         ← download 1yr of daily OHLCV in batches of 500
       │
       ├── strategies/
       │   ├── mean_reversion.py ← RSI(2) + BB + volume + 50MA filter
       │   ├── momentum.py       ← 6M return rank + ADX + 200MA filter
       │   └── breakout.py       ← 52-week high + volume + RS filter
       │
       ├── broker/alpaca_client.py  ← place bracket orders, enforce time stops
       ├── journal/ledger.py        ← reconcile exits, compute win rate / P&L stats
       ├── notifications/email_client.py  ← send summary + error emails
       └── journal/trades.csv    ← append every placed order for win rate tracking

scanner/eod.py           ← run after market close (3:30 PM CDT)
       │
       ├── broker/alpaca_client.py  ← pull open positions + closed orders
       ├── journal/ledger.py        ← reconcile exits into trades.csv
       └── notifications/email_client.py  ← send EOD report email

agents/docs_agent.py     ← run after code changes to keep docs/ current
       └── claude-agent-sdk         ← Claude agent with Read/Write/Edit tools
```

**Daily workflow:**
1. **Pre-market (7:30 AM CDT):** `python scanner/scan.py`
   - Universe loaded from cache (or rebuilt if > 7 days old)
   - OHLCV data downloaded for all symbols
   - Open positions ≥ 10 days closed (time stop enforcement)
   - All 3 strategies run in parallel (ThreadPoolExecutor)
   - Top 5 signals per strategy selected
   - Bracket orders placed via Alpaca — broker handles all exits
   - Results emailed to `monesh.kovi1@gmail.com`
   - Trades logged to `journal/trades.csv`

2. **After market close (3:30 PM CDT):** `python scanner/eod.py`
   - Closed orders pulled from Alpaca and reconciled into ledger
   - Exit type determined from order type (LIMIT→TAKE_PROFIT, STOP→STOP_LOSS, MARKET→TIME_STOP)
   - EOD report emailed: today's closed trades, open positions with unrealized P&L, running win rate/P&L by strategy

**Time stop enforcement:**
Each morning before placing new orders, the scanner checks `journal/trades.csv` for any positions open ≥ 10 days and closes them via Alpaca before scanning for new signals.
