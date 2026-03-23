# Strategy: Momentum / Trend Following

## What It Is

Momentum is the observation that **stocks which have gone up over the past 3–12 months tend to keep going up**, and stocks that have gone down tend to keep going down. You are not buying cheap stocks — you are buying strong stocks that are getting stronger.

This is the opposite of mean reversion. Where mean reversion buys weakness, momentum buys strength.

---

## Why It Works

### The Academic Foundation
Momentum is one of the most replicated findings in all of financial economics:

- **Jegadeesh & Titman (1993)** — the original momentum paper. Showed that buying past 6–12 month winners and selling losers generates significant abnormal returns. Published in the Journal of Finance.
- **Fama & French (1996)** — even Eugene Fama (the father of the Efficient Market Hypothesis) acknowledged momentum as the "premier anomaly" that his model could not explain.
- **AQR Capital (Asness et al.)** — confirmed momentum works across asset classes: equities, bonds, currencies, commodities.

It has worked for 200+ years of documented market history across 40+ countries.

### The Market Mechanism
Why does momentum persist if markets are "efficient"?

1. **Under-reaction to news:** When a company reports strong earnings, investors don't immediately bid the price to fair value. They are cautious, conservative, disbelieving. Price drifts up slowly as more investors become convinced — this is the momentum effect.

2. **Herding behavior:** As a stock rises, more investors notice it. Fund managers face career risk from missing a rising stock. Buying pressure compounds.

3. **Trend-following capital:** Systematic funds (CTAs, trend followers) explicitly buy rising assets, creating self-reinforcing trends.

4. **Narrative compounding:** Strong stocks attract media coverage, analyst upgrades, and retail interest — all of which drive further buying.

### Why It Has Risks
Momentum also has the sharpest crashes of any factor. When market conditions reverse suddenly (e.g., March 2020 COVID crash), momentum stocks crash harder than everything else because everyone is holding the same crowded positions. This is called a **momentum crash** and is why we use:
- ADX filter (only trade stocks with confirmed trend strength)
- Hard stop (1.5x ATR below entry)
- 200MA filter (avoid holding through major trend breaks)

---

## Entry Rules (All Must Be True)

### 1. Top 10% by 6-Month Return
We rank every stock in our universe by its total return over the last 126 trading days (~6 months). Only stocks in the top 10% (90th percentile and above) qualify.

**Why 6 months, not 12?**
Academic research shows the strongest momentum signal comes from 3–12 months. 6 months is the sweet spot — long enough to filter out noise, short enough to catch stocks still in their upswing. The most recent 1 month is deliberately excluded (some implementations do 12-1 momentum) because very short-term momentum actually reverses.

**Why top 10%?**
The momentum premium concentrates in the top decile. Owning the top 30% dilutes the effect significantly. We want the strongest of the strong.

### 2. Price Above 200-Day Moving Average
**What it is:** The 200-day MA is the long-term trend indicator. Every institutional investor watches it.

**Why:** A stock can have strong 6-month momentum but still be in a long-term downtrend (e.g., a dead-cat bounce). The 200MA filter ensures we are only trading stocks in confirmed long-term uptrends. When price is above 200MA, the trend is your friend. When it's below, you're fighting the trend.

### 3. Price Above 50-Day Moving Average
The 50MA is the medium-term trend. This filters out stocks that are fading from their 6-month highs. We want stocks that are still rising, not ones that peaked 3 months ago.

### 4. ADX(14) > 25
**What it is:** ADX stands for Average Directional Index. It measures trend **strength** on a scale of 0–100, regardless of direction.

- ADX < 20: no trend, choppy/ranging market
- ADX 20–25: weak trend forming
- ADX > 25: confirmed trend
- ADX > 40: strong trend

**Why this matters:** A stock can be up 40% over 6 months but if it got there in a jagged, choppy way, the trend is weak and likely to reverse. ADX > 25 means the stock is trending cleanly and consistently — exactly the kind of move that persists.

### 5. Volume ≥ 1.0x 20-Day Average
Normal volume confirms the trend has broad participation. We don't require elevated volume for momentum (unlike mean reversion) — just that volume isn't collapsing, which would suggest distribution (smart money selling into retail buying).

---

## Exit Rules

### Take Profit: Entry + 3x ATR(14)
Momentum targets are wider than mean reversion because trends run further. A mean reversion trade lasts 2–5 days. A momentum trade can run for weeks. 3x ATR gives the trade room to develop.

### Stop Loss: Entry − 1.5x ATR(14)
Same ATR-based logic as mean reversion — calibrated to actual volatility, not arbitrary %.

### Soft Trigger: Price Crosses Below 21-Day EMA
The 21-day EMA (Exponential Moving Average) is a common institutional trailing stop. When price breaks below it, the short-term trend has turned. This is logged but doesn't override the hard bracket — it's a warning signal to monitor.

### Time Stop: 10 Days
Exits any position that hasn't moved within 10 trading days.

---

## Signal Scoring

Signals are ranked by their 6-month return percentile score (0.90 to 1.00). The highest percentile rank = strongest momentum = placed first.

---

## Risk / Reward

- ATR stop: 1.5x ATR
- ATR target: 3.0x ATR
- Theoretical R:R: 3.0 / 1.5 = **2.0**

This meets the 1:2 R:R target. Momentum has a lower win rate than mean reversion (~45–55%) but the larger winners compensate — when momentum works, it really works.

---

## Why 0 Signals in Current Market (March 2026)

The ADX > 25 filter is doing its job. During broad market corrections, fewer stocks have clean, strong uptrends. ADX drops across the board as price action becomes choppy. When the market stabilizes and uptrends re-establish, momentum signals will return. This is expected and correct behaviour — momentum should not fire during corrections.

---

## Reference

- *Dual Momentum Investing* — Gary Antonacci
- *Quantitative Momentum* — Wesley Gray & Jack Vogel
- Jegadeesh & Titman (1993), "Returns to Buying Winners and Selling Losers" — Journal of Finance
- AQR Capital: "Fact, Fiction and Momentum Investing" (freely available)
