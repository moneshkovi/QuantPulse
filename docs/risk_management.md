# Risk Management

## Philosophy

Risk management is not optional — it is the only reason systematic traders survive long enough to profit. A single unmanaged loss can wipe out weeks of gains. The rules below are non-negotiable and built into every trade.

> "The first rule of trading is don't lose money. The second rule is don't forget the first rule." — Warren Buffett

---

## Position Sizing: The 1% Rule

**Rule:** Never risk more than 1% of total portfolio value on a single trade.

**How it's calculated:**

```
dollar_risk    = portfolio_value × 0.01
risk_per_share = entry_price - stop_price  (= 1.5 × ATR)
quantity       = dollar_risk / risk_per_share
```

**Example:**
- Portfolio: $100,000
- Dollar risk per trade: $1,000
- Stock entry: $50.00, stop: $47.50 → risk per share = $2.50
- Quantity = $1,000 / $2.50 = **400 shares**

This means a position size is determined by the stock's volatility, not a fixed dollar amount. A volatile stock (large ATR) gets fewer shares. A stable stock (small ATR) gets more shares. In both cases, the maximum dollar loss if stopped out is identical: $1,000 (1% of portfolio).

**Why 1% not 2%?**
With 15 simultaneous positions (5 per strategy × 3 strategies), 2% risk per trade means 30% of your portfolio is theoretically at risk if everything goes wrong at once. 1% caps total simultaneous risk at 15%. This is the institutional standard for systematic traders.

**Position value cap:** No single position can exceed 10% of portfolio value, regardless of what the sizing formula produces.

---

## Stop Loss: ATR-Based (Not Fixed %)

**Rule:** Stop loss is always placed at `entry - 1.5 × ATR(14)`.

### What is ATR?

ATR stands for **Average True Range**. It measures how much a stock typically moves per day, accounting for gaps.

```
True Range = max(
    High - Low,              ← intraday range
    |High - Previous Close|, ← gap up
    |Low  - Previous Close|  ← gap down
)
ATR(14) = 14-day rolling average of True Range
```

A stock with ATR = $3.00 typically moves $3 per day. A stock with ATR = $0.50 moves $0.50 per day.

### Why ATR Stops Beat Fixed % Stops

Fixed 2% stop on a $100 stock = $2.00 stop. If that stock's ATR is $4.00, the stop is inside normal daily noise — you will be stopped out by random fluctuation, not by the trade going wrong.

ATR stop = 1.5 × $4.00 = $6.00 stop. Now the stop is only triggered if the stock moves 1.5× its normal daily range in the wrong direction — a genuine adverse move, not noise.

**Result:** ATR stops dramatically reduce premature stop-outs while still cutting losses when the trade is genuinely wrong.

---

## Take Profit: Strategy-Specific ATR Multiples

| Strategy | Target | Why |
|---|---|---|
| Mean Reversion | Entry + 2.0x ATR | Short hold, quick bounce expected (2–5 days) |
| Momentum | Entry + 3.0x ATR | Trends run further, give room |
| Breakout | Entry + 3.0x ATR | True breakouts lead to extended moves |

The target is also ATR-based — it adapts to each stock's volatility. A stock that moves $5/day gets a wider absolute target than one that moves $0.50/day, but the R:R ratio stays consistent.

---

## Time Stop: 10 Trading Days

**Rule:** Any position open for 10 trading days that has not hit stop or target is closed at market.

**Why:**
Capital has an opportunity cost. A trade that goes sideways for 10 days is not making money and is blocking a slot that could hold a better trade. Professional traders call this "dead money" — it's a real loss even if the P&L shows breakeven.

10 days = 2 trading weeks. Mean reversion targets 2–5 day holds. Momentum and breakout can run longer, but if they haven't moved in 10 days the thesis has not materialised.

---

## Maximum Positions

| Scope | Limit |
|---|---|
| Per strategy | 5 positions |
| Total simultaneous | 15 positions |

**Why per-strategy limits?**
Each strategy has a different market regime. During corrections, mean reversion fires but momentum doesn't. Capping each at 5 prevents over-concentration in one strategy's signals while still allowing full deployment when all 3 are active.

---

## Expected Value: Why This Math Works

With 1% risk per trade and ~1.3–2.0 R:R:

| Scenario | Win Rate | R:R | EV per trade (% of portfolio) |
|---|---|---|---|
| Mean Reversion (conservative) | 60% | 1.33 | +0.40% |
| Momentum | 50% | 2.00 | +0.50% |
| Breakout | 50% | 2.00 | +0.50% |

Over 100 trades, even the most conservative scenario compounds significantly. The key is consistency — never deviate from the stop, never skip the time stop, never "average down" on a losing position.

---

## What We Never Do

- **Average down** — adding to a losing position hoping it recovers. This is how small losses become catastrophic ones.
- **Move stops further away** — if the trade is going wrong, the stop is there for a reason.
- **Override the time stop** — "it will come back" is the most expensive phrase in trading.
- **Risk more than 1%** — no matter how confident the signal looks.
- **Hold through earnings** — earnings can gap a stock 20% against you overnight. The ATR stop won't protect you. If a position has an earnings event within the hold period, consider closing before the announcement.
