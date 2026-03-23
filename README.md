# AlphaLoop 📈
### Algorithmic Trading System — Project Plan & Implementation Guide

> **Philosophy:** Find repeatable statistical edge. Validate before scaling. Strategy first, AI second.

---

## Table of Contents
1. [What This Is](#what-this-is)
2. [Goals](#goals)
3. [Budget & Scaling Plan](#budget--scaling-plan)
4. [Project Phases](#project-phases)
5. [Trading Strategies](#trading-strategies)
6. [Tech Stack](#tech-stack)
7. [Win Rate Math](#win-rate-math)
8. [Essential Books & References](#essential-books--references)
9. [Folder Structure](#folder-structure)
10. [Getting Started](#getting-started)

---

## What This Is

AlphaLoop is a personal algorithmic trading system for **US equities**. It is designed for someone who:

- Cannot watch markets daily
- Wants automated entry, stop loss, and take profit execution
- Wants to validate a strategy with paper trading before using real money
- Plans to scale capital progressively based on measured win rate

The system outputs **buy price, stop loss price, and take profit price** for each trade, and places bracket orders automatically via the Alpaca API. You review results weekly, not daily.

---

## Goals

### Primary Goals
- [ ] Build and backtest 1–2 rule-based strategies on US equities
- [ ] Achieve **55%+ win rate** with **1:2 risk/reward** over 50+ paper trades
- [ ] Deploy automated paper trading via Alpaca with bracket orders
- [ ] Measure real performance metrics: win rate, profit factor, max drawdown
- [ ] Add ML classification layer to improve signal quality

### Secondary Goals
- [ ] Scale real capital from $1,000 → $10,000+ based on verified win rate
- [ ] Run fully automated — scan on weekends, orders placed for the week
- [ ] Keep max risk per trade at 1–2% of total capital

---

## Budget & Scaling Plan

| Stage | Capital | Condition to Advance |
|---|---|---|
| Phase 1: Backtesting | $0 | Historical win rate ≥ 55% over 100+ trades |
| Phase 2: Paper Trading | $0 | Simulated win rate ≥ 55% over 50+ trades |
| Phase 3: Real Money (Start) | $1,000 | 2+ months of consistent paper results |
| Phase 4: Scale Up | $10,000+ | Real win rate ≥ 55%, max drawdown ≤ 15% |

> At $1,000 capital: risk $10–20 per trade (1–2%). Run max 1–3 positions at a time.

---

## Project Phases

### Phase 1 — Strategy Research & Backtesting (Weeks 1–4)

Validate your strategy on historical data **before** writing a single live trade. This is non-negotiable.

**Tools:**
```
yfinance       — free historical OHLCV data for US stocks
Backtrader     — Python backtesting framework
QuantStats     — auto-generates win rate, Sharpe, drawdown reports
```

**Install:**
```bash
pip install backtrader yfinance quantstats pandas numpy
```

**Metrics to target:**

| Metric | Definition | Target |
|---|---|---|
| Win Rate | % of trades that are profitable | ≥ 55% |
| Profit Factor | Gross wins ÷ gross losses | ≥ 1.5 |
| Sharpe Ratio | Return per unit of risk | ≥ 1.0 (2.0 ideal) |
| Max Drawdown | Largest peak-to-trough loss | ≤ 20% |
| Avg Risk/Reward | Avg win size vs avg loss size | ≥ 1:2 |

**Steps:**
1. Pull 5–10 years of daily OHLCV data using `yfinance`
2. Code your strategy rules (entry, stop, target) in Backtrader
3. Run backtest across S&P 500 universe
4. Generate QuantStats report — if metrics don't meet targets, tweak and re-run
5. Only move to Phase 2 when backtested metrics are satisfactory

---

### Phase 2 — Paper Trading (Weeks 4–8)

Deploy your backtested strategy on live market data with **zero real money**.

**Platform: Alpaca Markets** (`alpaca.markets`)
- Free paper trading API with real-time market data
- Python SDK — same code works for live trading later
- Supports bracket orders (entry + stop loss + take profit in one call)
- No Pattern Day Trader (PDT) restrictions on paper accounts

**Install:**
```bash
pip install alpaca-trade-api
```

**How a bracket order works:**
```python
api.submit_order(
    symbol='AAPL',
    qty=10,
    side='buy',
    type='limit',
    time_in_force='day',
    limit_price=150.00,
    order_class='bracket',
    stop_loss={'stop_price': 147.00},     # -2% stop
    take_profit={'limit_price': 156.00}   # +4% target → 1:2 R:R
)
```

> Once placed, the broker handles both exits automatically. You don't need to watch.

**Workflow:**
1. Run scanner every Sunday evening
2. AlphaLoop outputs a list of stocks with entry, stop, and target prices
3. Bracket orders are placed before market open Monday
4. Check results once a week — log win/loss in a spreadsheet
5. After 50+ trades, calculate real win rate and profit factor

---

### Phase 3 — ML Signal Layer (Weeks 8–12)

Add machine learning on top of the rule-based strategy to filter weak signals.

> **Important:** Don't start here. ML without a rule-based baseline first is a common and expensive mistake.

**Feature Engineering (inputs to the model):**
- RSI, MACD, Bollinger Band position
- ATR (volatility measure)
- Volume ratio (today vs. 20-day average)
- Distance from 200-day moving average
- Sector momentum score

**Model:**
```
XGBoost or Random Forest
— fast, interpretable, works well on tabular financial data
— avoid LSTMs/deep learning early: they overfit badly on small datasets
```

**Label (what you're predicting):**
```
"Did this stock go up ≥ 3% within 5 days?" → 1 (yes) or 0 (no)
```

**Install:**
```bash
pip install xgboost scikit-learn shap
```

Use **SHAP** to understand which features are driving predictions — critical for trust and debugging.

**Reference:** *Advances in Financial Machine Learning* — Marcos López de Prado

---

### Phase 4 — Live Trading with Real Capital

Only reached after Phases 1–3 show consistent, measurable results.

- Start with **$1,000**, risk 1–2% per trade ($10–20 risk per trade)
- Run **1–3 positions max** at a time
- Review weekly — not daily
- Keep a trading journal: log every entry, exit, reason, and outcome
- Scale to $10,000+ **only** when live win rate ≥ 55% over 50+ real trades

---

## Trading Strategies

Three strategies are included. **Start with Strategy 1** — best fit for low-attention, automated trading.

---

### Strategy 1 — Mean Reversion ⭐ (Recommended Start)

**Idea:** Stocks that drop sharply tend to bounce back. Panic selling and institutional rebalancing create temporary mispricings that correct within days.

**Entry rules:**
- RSI < 30 on daily chart (oversold)
- Price at or below lower Bollinger Band (2 std devs)
- Volume ≥ 1.5x the 20-day average (confirms selling climax)
- Stock is in S&P 500 (liquid, less manipulation)

**Exit rules:**
- Take profit: RSI crosses back above 50, or +4% gain (whichever first)
- Stop loss: -2% below entry price
- Time stop: exit after 5 trading days regardless

**Why it works:**
Institutional funds rebalance regularly, creating forced buyers after drops. Retail panic selling overshoots fair value. The edge is in buying temporary fear.

**References:**
- *Short Term Trading Strategies That Work* — Larry Connors & Cesar Alvarez
- *Quantitative Trading* — Ernest Chan (Chapter on mean reversion)

---

### Strategy 2 — Momentum / Trend Following

**Idea:** Stocks that have been going up for 3–12 months tend to keep going up. Investors underreact to good news; the trend persists until it doesn't.

**Entry rules:**
- Rank all S&P 500 stocks by 6-month total return
- Buy the top 10% (strongest momentum)
- Only enter stocks trading above their 200-day moving average
- Rebalance monthly — sell what falls out of top 10%, replace with new entries

**Exit rules:**
- Monthly rebalance triggers exit
- Hard stop: stock falls below 200-day MA

**Why it works:**
Decades of academic research confirm momentum is one of the most robust anomalies in financial markets. Institutional under-reaction to earnings and news creates persistent price trends.

**References:**
- *Dual Momentum Investing* — Gary Antonacci (the definitive book on this)
- Fama & French momentum factor research (freely available)

---

### Strategy 3 — Breakout with Volume Confirmation

**Idea:** When price breaks a key resistance level with high volume, it signals institutional buying and tends to continue higher.

**Entry rules:**
- Price closes above 52-week high
- Breakout day volume ≥ 1.5x 20-day average
- Enter on next day's open

**Exit rules:**
- Stop loss: 2% below the breakout candle's low
- Take profit: 1:2 or 1:3 risk/reward

**Why it works:**
52-week highs clear out all sellers who bought below that level. High volume confirms institutions are driving the move, not retail noise.

**References:**
- *How to Make Money in Stocks* — William O'Neil (CANSLIM system)
- *Trade Like a Stock Market Wizard* — Mark Minervini

---

## Tech Stack

| Tool | Purpose | Cost |
|---|---|---|
| **Alpaca Markets** | Broker + paper/live trading API | Free |
| **yfinance** | Historical OHLCV market data | Free |
| **Polygon.io** | Real-time data feed (upgrade when live) | $29/month |
| **Backtrader** | Backtesting framework | Free |
| **QuantStats** | Performance reports | Free |
| **XGBoost + scikit-learn** | ML signal classification | Free |
| **SHAP** | ML model explainability | Free |
| **pandas / numpy** | Data manipulation | Free |
| **GitHub** | Version control | Free |
| **AWS / GCP Free Tier** | Run scanner in cloud (always-on) | Free |

> **Total cost at start: $0.** Upgrade to Polygon.io only when moving to live trading.

---

## Win Rate Math

Why 55% win rate with 1:2 risk/reward is enough to be consistently profitable:

| Win Rate | Risk/Reward | Expected Value per $100 risked | Verdict |
|---|---|---|---|
| 50% | 1:1 | $0 | Break even |
| 55% | 1:2 | +$65 | ✅ Profitable |
| 60% | 1:2 | +$80 | ✅ Strong |
| 55% | 1:3 | +$110 | ✅ Very strong |
| 45% | 1:2 | +$35 | ✅ Still profitable |

**Formula:**
```
Expected Value = (Win Rate × Avg Win) - (Loss Rate × Avg Loss)
Example: (0.55 × $200) - (0.45 × $100) = $110 - $45 = +$65 per trade
```

This is why risk/reward ratio matters as much as win rate. A 45% win rate with 1:3 R:R still makes money.

---

## Essential Books & References

| Book | Author | Why It Matters |
|---|---|---|
| *Quantitative Trading* | Ernest Chan | Best beginner quant book. Practical, Python examples. Covers both mean reversion and momentum. |
| *Algorithmic Trading* | Ernest Chan | Deeper follow-up. Real strategy implementations with live data. |
| *Advances in Financial Machine Learning* | Marcos López de Prado | Industry standard for ML on price data. Prevents backtest overfitting, data leakage, and wrong labels. |
| *Dual Momentum Investing* | Gary Antonacci | Definitive book on momentum. Decades of empirical evidence, simple to implement. |
| *Short Term Trading Strategies That Work* | Larry Connors | Empirically tested mean reversion setups. Rules are specific and backtestable. |
| *How to Make Money in Stocks* | William O'Neil | CANSLIM breakout methodology. Foundation of breakout strategy. |
| *Trade Like a Stock Market Wizard* | Mark Minervini | Advanced breakout and momentum. Real trading performance, not theory. |

---

## Folder Structure

```
alphaloop/
│
├── data/
│   ├── fetch.py              # Download historical data via yfinance
│   └── universe.py           # Define S&P 500 stock universe
│
├── strategies/
│   ├── mean_reversion.py     # RSI + Bollinger Band strategy
│   ├── momentum.py           # 6-month momentum ranking strategy
│   └── breakout.py           # 52-week high + volume strategy
│
├── backtest/
│   ├── run_backtest.py       # Run Backtrader simulation
│   └── report.py             # Generate QuantStats report
│
├── scanner/
│   └── scan.py               # Weekly scanner — outputs trade signals
│
├── broker/
│   └── alpaca.py             # Alpaca API wrapper — place bracket orders
│
├── ml/
│   ├── features.py           # Feature engineering (RSI, MACD, volume ratio, etc.)
│   ├── train.py              # Train XGBoost classifier
│   └── predict.py            # Generate ML signal scores
│
├── journal/
│   └── trades.csv            # Manual log: entry, exit, P&L, reason
│
├── config.py                 # API keys, risk settings, universe
├── requirements.txt
└── README.md
```

---

## Getting Started

### Step 1 — Set up environment
```bash
git clone https://github.com/yourusername/alphaloop.git
cd alphaloop
pip install -r requirements.txt
```

### Step 2 — Configure API keys
```python
# config.py
ALPACA_API_KEY = "your_key_here"
ALPACA_SECRET_KEY = "your_secret_here"
ALPACA_BASE_URL = "https://paper-api.alpaca.markets"  # paper trading URL
RISK_PER_TRADE = 0.02  # 2% of capital per trade
CAPITAL = 1000
```

### Step 3 — Run a backtest
```bash
python backtest/run_backtest.py --strategy mean_reversion --start 2018-01-01 --end 2024-01-01
```

### Step 4 — Run the weekly scanner
```bash
python scanner/scan.py
# Outputs: ticker, entry_price, stop_loss, take_profit, signal_score
```

### Step 5 — Place paper trades
```bash
python broker/alpaca.py --mode paper
```

---

## Key Rules

1. **Never skip backtesting.** If it doesn't work in history, it won't work live.
2. **Paper trade for at least 50 trades** before touching real money.
3. **Risk 1–2% max per trade.** At $1,000 that's $10–20 per trade.
4. **Let bracket orders do the work.** Don't manually override stops.
5. **Log every trade.** Win rate means nothing without data.
6. **Don't add ML until the rule-based strategy is proven.**
7. **Scale only on verified results, not gut feeling.**

---

*AlphaLoop — Find the edge. Prove the edge. Scale the edge.*
