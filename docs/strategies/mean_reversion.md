# Strategy: Mean Reversion

## What It Is

Mean reversion is based on one core idea: **prices oscillate around a mean**. When a stock drops sharply and becomes statistically oversold, it tends to snap back. You are not predicting the future — you are exploiting a statistical tendency that has been tested across decades of market data.

This strategy specifically targets **short-term panic overselling** — usually caused by broad market selloffs, sector rotation, or news-driven fear — not fundamental deterioration.

---

## Why It Works

### The Academic Foundation
Mean reversion in equity prices was documented as early as the 1980s by DeBondt and Thaler (1985) who showed that stocks with extreme past losses tend to outperform over the next 3–5 years. Larry Connors later refined this into short-term (2–5 day) rules that are more tradeable.

### The Market Mechanism
When a stock sells off sharply:
1. **Retail investors panic** and sell at any price — this overshoots fair value
2. **Institutional funds** have mandate-driven rebalancing — if a stock drops too far, they are forced buyers to maintain target allocations
3. **Market makers** and arbitrageurs step in when the gap to intrinsic value is large enough

The result: extreme short-term moves tend to partially reverse within 3–5 days.

### Why S&P 500 / Large Caps Work Best
- More institutional ownership = more rebalancing flow
- More liquid = faster price discovery and recovery
- Less likely to be "fundamentally broken" — so the dip is likely technical, not structural

---

## Entry Rules (All Must Be True)

### 1. RSI(2) < 10
**What it is:** RSI stands for Relative Strength Index. It measures how fast and how much a stock has moved recently. RSI(2) uses only the last 2 days — making it hypersensitive to short-term moves.

**Why RSI(2) not RSI(14):**
The standard RSI(14) is too slow for mean reversion. By the time RSI(14) reaches 30, the stock has often already bounced. Larry Connors' research (published in *Short Term Trading Strategies That Work*) showed that RSI(2) < 10 is one of the strongest short-term mean reversion signals in US equities, with historically high win rates over 3–5 day holds.

**What < 10 means:** The stock has been dropping for at least 2 consecutive days with significant momentum. This is the "panic zone."

### 2. Price ≤ Lower Bollinger Band (20-period, 2 standard deviations)
**What it is:** Bollinger Bands draw a channel around a stock's 20-day moving average, using 2 standard deviations above and below as the upper and lower bands.

**Why:** Statistically, prices should stay within 2 standard deviations ~95% of the time. A close below the lower band means the stock has moved unusually far, unusually fast. Combined with RSI(2) < 10, this is a double-confirmation of extreme overselling.

### 3. Volume ≥ 1.5x 20-day Average
**What it is:** We compare today's volume to the stock's average daily volume over the last 20 days.

**Why:** Volume confirms whether the selloff is a "climax" or just quiet drift. High volume on a down day = fear-driven panic selling = higher probability of reversal. Low volume on a down day = just slow selling pressure with no urgency = no clear reversal catalyst.

### 4. Price > 50-day Moving Average
**What it is:** The 50-day MA is the medium-term trend direction.

**Why this filter exists:** Mean reversion only works when you are buying a dip within an uptrend, not catching a falling knife in a downtrend. If a stock is already below its 50MA, the dip may not be panic — it may be a real trend change. This filter eliminates stocks in structural downtrends.

---

## Exit Rules

### Take Profit: Entry + 2x ATR(14)
The ATR (Average True Range) measures how much a stock typically moves per day on average over 14 days. Setting the target at 2x ATR means: "I expect the stock to recover by twice its normal daily range."

This is adaptive — a volatile stock gets a wider target, a stable stock gets a tighter one.

### Stop Loss: Entry − 1.5x ATR(14)
If the trade goes wrong and the stock drops another 1.5x its normal daily range below entry, we exit. This means the bounce did not happen and we cut the loss before it compounds.

**Why ATR-based stops instead of fixed % (e.g. -2%):**
Fixed % stops get picked off. If a stock normally moves $3/day and you put a 2% stop on a $100 stock ($2), you will get stopped out by normal noise. ATR-based stops are calibrated to each stock's actual volatility — you only get stopped out by an abnormal move, not routine fluctuation.

### Time Stop: 10 Days
If neither stop nor target is hit within 10 trading days, exit anyway. Dead money is a real cost — capital tied up in a sideways position could be redeployed.

---

## Signal Scoring

Signals are ranked by score to select the strongest 5:

```
score = (10 - RSI2) × (1 + BB_deviation) × volume_ratio
```

- Lower RSI2 = more oversold = higher score
- Deeper below BB = more statistically extreme = higher score
- Higher volume ratio = more conviction in the sell = higher score

---

## Risk / Reward

- ATR stop: 1.5x ATR
- ATR target: 2.0x ATR
- Theoretical R:R: 2.0 / 1.5 = **1.33**

This is slightly below the ideal 1:2 R:R. However, mean reversion historically has a **higher win rate** (60–70% in backtests) which compensates. Expected value with 65% win rate at 1.33 R:R is still strongly positive.

---

## Reference

- *Short Term Trading Strategies That Work* — Larry Connors & Cesar Alvarez
- *Quantitative Trading* — Ernest Chan (Chapter 3: Mean Reversion)
- DeBondt & Thaler (1985), "Does the Stock Market Overreact?" — Journal of Finance
