# AlphaLoop Documentation

Reference material for understanding how the system works, why each decision was made, and the academic/practical foundation behind every rule.

## Contents

| File | What It Covers |
|---|---|
| `strategies/mean_reversion.md` | RSI(2) + Bollinger Band strategy — full explanation of logic, entry rules, exits, why it works |
| `strategies/momentum.md` | 6-month momentum ranking strategy — academic foundation, filters, why 0 signals in corrections |
| `strategies/breakout.md` | 52-week high breakout strategy — overhead supply theory, volume confirmation, Minervini method |
| `indicators.md` | Plain-English explanation of every indicator: RSI, ATR, Bollinger Bands, ADX, Moving Averages, Volume Ratio |
| `risk_management.md` | Position sizing (1% rule), ATR stops, time stops, max positions — the math behind staying solvent |
| `tools.md` | Every library and API used: Alpaca, yfinance, ta, pandas — what each does and why we chose it |

## How to Use This

**If you want to understand a signal you received in an email** — read the relevant strategy doc. It will explain exactly why that stock qualified and what we expect to happen.

**If you want to understand a number in the output** (ATR, score, R:R) — read `indicators.md`.

**If you want to understand why a position was sized the way it was** — read `risk_management.md`.

**If you want to add a new strategy** — follow the pattern in `strategies/mean_reversion.py`. The `get_signals(bars)` interface is the contract: take a dict of DataFrames, return a sorted list of `Signal` objects.
