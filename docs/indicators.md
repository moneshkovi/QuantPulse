# Technical Indicators Reference

A plain-English explanation of every indicator used in AlphaLoop, what it measures, and why we use it.

---

## RSI — Relative Strength Index

**Formula:**
```
RS  = Average Gain over N days / Average Loss over N days
RSI = 100 - (100 / (1 + RS))
```

**Output range:** 0 to 100

**What it measures:** The speed and magnitude of recent price moves. High RSI = stock has been going up a lot recently. Low RSI = stock has been going down a lot recently.

**Standard interpretation:**
- RSI > 70: overbought (may be due for a pullback)
- RSI < 30: oversold (may be due for a bounce)

**How we use it — RSI(2) for mean reversion:**
We use window=2 (only last 2 days), not the standard 14. This makes it extremely sensitive to short-term moves.

- RSI(2) < 10 means the stock has dropped hard in the last 2 days
- At this level, the probability of at least a 1–2 day bounce is historically very high (Larry Connors' research shows 65–70%+ win rate)
- RSI(14) < 30 is too slow — by the time it hits 30, the opportunity is often over

**Analogy:** RSI(14) is a monthly mood tracker. RSI(2) is checking how you feel right now.

---

## Bollinger Bands

**Formula:**
```
Middle Band = 20-day Simple Moving Average (SMA)
Upper Band  = 20-day SMA + (2 × 20-day Standard Deviation)
Lower Band  = 20-day SMA - (2 × 20-day Standard Deviation)
```

**What it measures:** The "normal range" of price movement for a stock. The bands expand when volatility is high and contract when it's low.

**Key statistical fact:** If price moves were normally distributed, price should stay within the bands ~95% of the time (2 standard deviations). A close below the lower band is a statistically rare event.

**How we use it:**
- Price ≤ lower Bollinger Band = the stock has moved unusually far down
- Combined with RSI(2) < 10, this is double confirmation: both the speed and the distance of the drop are extreme
- We measure how far below the band the price is (`BB_deviation`) as part of the signal score

**Analogy:** Bollinger Bands are like the normal range of a person's body temperature. 97–99°F is normal. Below 95°F is a rare and meaningful signal that something unusual is happening.

---

## ATR — Average True Range

**Formula:**
```
True Range = max(
    High - Low,
    abs(High - Previous Close),
    abs(Low  - Previous Close)
)
ATR(14) = 14-day rolling average of True Range
```

**What it measures:** How much a stock typically moves per day, accounting for overnight gaps. It is a pure volatility measure — it doesn't tell you direction, just magnitude.

**Examples:**
- AAPL ATR ≈ $3–5 on a normal day
- A small-cap biotech ATR might be $2 on a $10 stock (20% daily moves)

**How we use it — everywhere:**
ATR is the foundation of all our stops and targets:

```
Stop loss   = entry - 1.5 × ATR   (adapts to volatility)
MR target   = entry + 2.0 × ATR
Mo/BO target = entry + 3.0 × ATR
```

**Why ATR over fixed %:**
A 2% stop on AAPL = $4. If ATR = $3, that stop is within normal noise. You'll get stopped out randomly.
A 1.5× ATR stop = $4.50. Now you only get stopped if AAPL moves 1.5× its normal daily range — a genuinely bad day.

ATR also sets position size: the higher the ATR (more volatile stock), the fewer shares you buy to keep the dollar risk at exactly 1% of portfolio.

---

## Moving Averages: SMA, EMA

**SMA (Simple Moving Average):**
```
SMA(20) = sum of last 20 closing prices / 20
```
Each day gets equal weight. Smooth but slow to react.

**EMA (Exponential Moving Average):**
```
EMA today = (Close × multiplier) + (EMA yesterday × (1 - multiplier))
multiplier = 2 / (span + 1)
```
Recent days get more weight. Faster to react than SMA.

**How we use each:**

| MA | Period | Strategy | Purpose |
|---|---|---|---|
| SMA | 50-day | All | Medium-term trend filter. Price must be above it to enter. |
| SMA | 200-day | Momentum | Long-term trend filter. Only trade confirmed uptrends. |
| EMA | 21-day | Momentum | Soft exit signal — when price crosses below, trend weakening. |
| SMA | 20-day | Mean Reversion | Middle line of Bollinger Bands |

**The 200MA rule:**
The 200-day moving average is watched by every institutional investor on the planet. When price is above it, the long-term trend is up — you have the market's momentum behind you. When price is below it, you are fighting the trend. We only take long positions (buys) on stocks above their 200MA.

---

## ADX — Average Directional Index

**What it measures:** Trend **strength**, not direction. Scale of 0–100.

```
ADX < 20  → no trend, ranging/choppy
ADX 20–25 → weak trend forming
ADX > 25  → confirmed trend
ADX > 40  → strong trend
ADX > 50  → very strong trend (rare)
```

**Key insight:** ADX tells you IF there's a trend but not which way. A stock falling hard also has high ADX. We combine ADX with price being above moving averages to confirm uptrend strength.

**How we use it:**
- Momentum strategy requires ADX(14) > 25 at entry
- This filters out stocks that are technically in the top decile by return but got there in a choppy, unreliable way
- A smooth, consistent uptrend has high ADX; a jagged, volatile one does not

---

## Volume Ratio

**Formula:**
```
volume_ratio = today's volume / 20-day average daily volume
```

**What it measures:** Whether today's trading activity is above or below normal.

**How we use it:**

| Strategy | Threshold | Why |
|---|---|---|
| Mean Reversion | ≥ 1.5x | High volume on down day = climactic selling = reversal more likely |
| Breakout | ≥ 1.5x | High volume on breakout = institutional buying = real move |
| Momentum | ≥ 1.0x | Just confirm normal participation, trend doesn't need volume spike |

**The logic:**
Volume is the footprint of institutional money. Retail investors don't move stocks on their own — the float is too large. When you see volume 2x or 3x above average, a mutual fund or hedge fund is making a large position change. That's the information you want to trade with.

---

## 52-Week High

**Formula:**
```
52_week_high = max(closing prices over last 252 trading days, excluding today)
Signal fires if: today's close > 52_week_high
```

**What it measures:** Whether today's closing price is the highest it has been in a full year.

**Why it matters:**
- All buyers from the past year are at breakeven or in profit — no "trapped" sellers above this level
- Overhead supply (resistance) has been cleared
- The stock is in "price discovery" — no prior reference point for sellers

**Common misconception:** "It's already up so much, it must come down." Research shows the opposite — stocks making new 52-week highs dramatically outperform over the next 6–12 months compared to the broad market. New highs breed new highs.
