"""
Momentum / Trend Following Strategy
-------------------------------------
Edge: Stocks with strong 6-month price momentum continue outperforming.
Fama-French momentum factor — one of the most replicated anomalies in finance.
Institutional under-reaction to earnings + news creates persistent trends.

Entry conditions:
  - Top decile (10%) by 6-month total return across universe
  - Price above 200-day MA (only trade confirmed uptrends)
  - Price above 50-day MA (intermediate trend intact)
  - Volume ≥ 1.0x 20-day average (avoid illiquid entries)
  - ADX(14) > 25 (trend strength filter — avoid choppy stocks)

Exit:
  - Target: entry + 3x ATR(14)  [momentum targets are wider — trends run further]
  - Stop: entry - 1.5x ATR(14)
  - Soft exit trigger: price crosses below 21-day EMA (logged, not hard bracket)
  - Time stop: 10 days (handled by broker layer)

Signal score: 6-month return percentile rank
"""
import pandas as pd
import numpy as np
import ta as ta_lib
import logging
from data.fetch import compute_atr
from strategies.base import Signal
import config

logger = logging.getLogger(__name__)


def _six_month_return(close: pd.Series) -> float | None:
    """Total return over last ~126 trading days (6 months)."""
    if len(close) < 130:
        return None
    start_price = float(close.iloc[-126])
    end_price = float(close.iloc[-1])
    if start_price <= 0:
        return None
    return (end_price - start_price) / start_price


def _compute_metrics(symbol: str, df: pd.DataFrame) -> dict | None:
    try:
        close = df["Close"]
        volume = df["Volume"]

        ret_6m = _six_month_return(close)
        if ret_6m is None:
            return None

        ma200 = close.rolling(200).mean()
        ma50 = close.rolling(50).mean()
        ema21 = close.ewm(span=21, adjust=False).mean()
        avg_vol_20 = volume.rolling(20).mean()
        atr = compute_atr(df, 14)

        # ADX for trend strength
        adx = ta_lib.trend.ADXIndicator(df["High"], df["Low"], close, window=14).adx()

        idx = -1
        last_close = float(close.iloc[idx])
        last_ma200 = float(ma200.iloc[idx])
        last_ma50 = float(ma50.iloc[idx])
        last_vol_ratio = float(volume.iloc[idx] / avg_vol_20.iloc[idx])
        last_atr = float(atr.iloc[idx])
        last_adx = float(adx.iloc[idx])

        if any(np.isnan([last_ma200, last_ma50, last_vol_ratio, last_atr, last_adx])):
            return None

        # Filters
        if last_close <= last_ma200:
            return None
        if last_close <= last_ma50:
            return None
        if last_vol_ratio < 1.0:
            return None
        if last_adx < 25:
            return None

        return {
            "symbol": symbol,
            "last_close": last_close,
            "ret_6m": ret_6m,
            "atr": last_atr,
        }

    except Exception as e:
        logger.debug(f"momentum metrics failed for {symbol}: {e}")
        return None


def get_signals(bars: dict[str, pd.DataFrame]) -> list[Signal]:
    """Run momentum scan. Rank by 6M return, return top signals."""
    metrics = []
    for symbol, df in bars.items():
        m = _compute_metrics(symbol, df)
        if m:
            metrics.append(m)

    if not metrics:
        return []

    df_metrics = pd.DataFrame(metrics)
    # Percentile rank of 6M return across the scanned universe
    df_metrics["score"] = df_metrics["ret_6m"].rank(pct=True)
    # Only top decile
    df_metrics = df_metrics[df_metrics["score"] >= 0.90].sort_values("score", ascending=False)

    signals = []
    for _, row in df_metrics.iterrows():
        entry = round(float(row["last_close"]), 2)
        atr = float(row["atr"])
        stop = round(entry - config.ATR_STOP_MULTIPLIER * atr, 2)
        target = round(entry + 3.0 * atr, 2)  # momentum runs wider

        if stop >= entry or target <= entry:
            continue

        signals.append(Signal(
            symbol=row["symbol"],
            strategy="momentum",
            entry_price=entry,
            stop_price=stop,
            target_price=target,
            score=float(row["score"]),
            atr=atr,
            qty=0
        ))

    logger.info(f"Momentum: {len(signals)} top-decile signals found")
    return signals
