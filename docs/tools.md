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

## Architecture: How Everything Connects

```
scanner/scan.py          ← entry point, run this daily pre-market
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
       ├── notifications/email_client.py  ← send summary + error emails
       └── journal/trades.csv    ← append every placed order for win rate tracking
```

**Daily workflow:**
1. Run `python scanner/scan.py` pre-market (8:00–9:15 AM ET)
2. Universe loaded from cache (or rebuilt if > 7 days old)
3. OHLCV data downloaded for all symbols
4. All 3 strategies run in parallel (ThreadPoolExecutor)
5. Top 5 signals per strategy selected
6. Bracket orders placed via Alpaca — broker handles all exits
7. Results emailed to `monesh.kovi1@gmail.com`
8. Trades logged to `journal/trades.csv`

**Time stop enforcement:**
Each morning before placing new orders, the scanner checks `journal/trades.csv` for any positions open ≥ 10 days and closes them via Alpaca before scanning for new signals.
