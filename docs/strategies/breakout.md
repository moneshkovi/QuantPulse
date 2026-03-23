# Strategy: Breakout with Volume Confirmation

## What It Is

A breakout strategy buys stocks the moment they close at a **new 52-week high** with **high volume**. The idea is that a new high is not the end of the move — it is often the beginning. You are buying strength at the point of maximum potential energy.

This runs counter to the instinct of most retail investors, who think "it's already gone up so much, I missed it." The data says the opposite.

---

## Why It Works

### The Market Mechanism

**Overhead supply** is the key concept. Imagine everyone who bought a stock at $50 over the past year. As the stock fell to $40, they were sitting on a loss. As it recovered to $50, every one of them was a seller — desperate to "get out at breakeven." This creates a wall of selling pressure at $50 called resistance.

When the stock breaks above $50 with high volume, something important has happened: **all of that overhead supply has been absorbed.** Every seller who wanted out has been matched with a buyer. Now there are no more trapped sellers above this price — the path of least resistance is upward.

High volume on the breakout confirms that institutional buyers — mutual funds, hedge funds — are driving the move. Retail can't push a stock to a 52-week high on meaningful volume. When volume is 1.5x or more above average, institutions are accumulating.

### Academic and Practical Foundation

- **Mark Minervini** — one of the most successful traders in US Investor Championship history, with returns of 220%+ in a single year. His SEPA (Specific Entry Point Analysis) methodology is built entirely on this principle.
- **William O'Neil** — founder of Investor's Business Daily. His CANSLIM system explicitly targets stocks breaking to new highs out of proper base formations with high volume.
- **George Soros** — famously described his approach as: "I buy when stocks break to new highs."

---

## Entry Rules (All Must Be True)

### 1. Today's Close is a New 52-Week Closing High
**Why closing price, not intraday?**
Intraday highs can be triggered by a single large order or a news spike that fades. A **closing** new high means buyers maintained control all day. The market "voted" at close — that's the most reliable signal.

**Why 52-week high specifically?**
52 weeks = one full year of market participants. Everyone who bought in the last year is now at breakeven or in profit — they have no incentive to sell at a loss. The stock is in "blue sky" territory with no overhead resistance.

### 2. Breakout Volume ≥ 1.5x 20-Day Average
**Why:** As explained above, high volume = institutional participation. Low volume breakouts are "false breakouts" — they fail because there isn't enough buying conviction behind them. The 1.5x threshold is the minimum to confirm meaningful participation.

In practice, the best breakouts often have 2x–5x normal volume. A breakout on 1.5x volume is the minimum bar.

### 3. Price Above 50-Day Moving Average
The stock must already be in an intermediate uptrend. The breakout should be the final push through resistance, not the first move off a bottom.

### 4. Relative Strength: Top 30% of Universe by 6-Month Return
A stock can break to a 52-week high but still be a weak stock relative to the market. We want breakouts happening in stocks that are already outperforming their peers — this is called Relative Strength (RS).

O'Neil's original IBD Relative Strength Rating used a similar concept. Stocks breaking out with high RS tend to continue outperforming. Stocks breaking out from weak RS positions often fail quickly.

### 5. Not Extended: Close Within 5% of 52-Week High
If the stock is already 15% above its previous 52-week high, you are chasing. The optimal entry is as close to the breakout point as possible — within 5% means you are buying the fresh breakout, not a stock that already ran without you.

---

## Exit Rules

### Take Profit: Entry + 3x ATR(14)
Breakouts that work tend to run significantly. The 3x ATR target (same as momentum) gives the trade room to develop. When a true breakout happens, the first move is often the beginning of a multi-week or multi-month trend.

### Stop Loss: Tighter of ATR-Based OR Below Breakout Candle Low
```
atr_stop  = entry - 1.5 × ATR(14)
candle_stop = breakout candle low - $0.01
stop = max(atr_stop, candle_stop)   ← whichever is tighter
```

**Why the breakout candle low?**
The low of the breakout candle is a natural support level. If price falls back below it, the breakout has failed — institutions that drove the breakout are no longer holding the stock up. Exiting there limits the loss to a clear technical failure point.

Using `max()` means we always take the tighter (higher) of the two stops — smaller risk per trade.

### Time Stop: 10 Days
Breakouts that don't follow through within 10 days are usually failed breakouts. Exit and redeploy.

---

## Signal Scoring

```
score = volume_ratio × (1 / (1 + extension × 10))
```

- Higher volume = stronger institutional conviction = higher score
- Closer to the breakout point (lower extension) = fresher = higher score
- A breakout on 3x volume right at the high scores much higher than one on 1.6x volume that's already 4% extended

---

## Risk / Reward

- ATR stop: 1.5x ATR (or tighter if candle low is closer)
- ATR target: 3.0x ATR
- Theoretical R:R: **≥ 2.0** (often better due to tighter candle stop)

---

## Why 0 Signals in Current Market (March 2026)

In a market correction, stocks are making 52-week lows, not 52-week highs. The breakout strategy correctly returns zero signals — there is nothing to break out when the tide is going out. This is the strategy's circuit breaker. It only fires when the market is producing genuine new leaders.

When the market recovers and a new uptrend begins, breakout signals will be among the first to appear — the leading stocks will break to new highs before the indices fully recover.

---

## Reference

- *Trade Like a Stock Market Wizard* — Mark Minervini
- *How to Make Money in Stocks* — William O'Neil
- *Momentum Masters* — Mark Minervini, David Ryan, Mark Ritchie II, Dan Zanger
