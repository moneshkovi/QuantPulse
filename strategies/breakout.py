"""
Breakout with Volume Confirmation Strategy
------------------------------------------
Edge: A 52-week high close clears all overhead supply — every prior seller
is now profitable or flat. High-volume breaks confirm institutional accumulation,
not retail noise. Mark Minervini / O'Neil CANSLIM core principle.

Entry conditions:
  - Today's close is a new 52-week closing high (not intraday — closing price matters)
  - Breakout volume ≥ 1.5x 20-day average (institutional footprint)
  - Price > 50-day MA (stock must already be in a base or uptrend)
  - RS Rank: stock's 6M return must be in top 30% of universe [relative strength]
  - Not extended: close within 5% of the 52-week high (not chasing a 20% breakout)

Exit:
  - Target: entry + 3x ATR(14) [1:3 R:R — breakouts that work go far]
  - Stop: entry - 1.5x ATR(14) OR below breakout candle low, whichever is tighter
  - Time stop: 10 days (handled by broker layer)

Signal score: volume ratio × proximity to fresh high
"""
import pandas as pd
import numpy as np
import logging
from data.fetch import compute_atr
from strategies.base import Signal
import config

logger = logging.getLogger(__name__)

# Pre-computed universe 6M returns for RS filter (injected by scanner)
_universe_returns: dict[str, float] = {}

def set_universe_returns(returns: dict[str, float]) -> None:
    global _universe_returns
    _universe_returns = returns


def _compute_signals(symbol: str, df: pd.DataFrame) -> Signal | None:
    try:
        close = df["Close"]
        high = df["High"]
        low = df["Low"]
        volume = df["Volume"]

        # Need at least 252 days for 52-week high
        if len(close) < 252:
            return None

        ma50 = close.rolling(50).mean()
        avg_vol_20 = volume.rolling(20).mean()
        atr = compute_atr(df, 14)

        idx = -1
        last_close = float(close.iloc[idx])
        last_high = float(high.iloc[idx])
        last_low = float(low.iloc[idx])
        last_ma50 = float(ma50.iloc[idx])
        last_vol_ratio = float(volume.iloc[idx] / avg_vol_20.iloc[idx])
        last_atr = float(atr.iloc[idx])

        if any(np.isnan([last_ma50, last_vol_ratio, last_atr])):
            return None

        # 52-week high (closing price, last 252 bars excluding today)
        prior_closes = close.iloc[-252:-1]
        week52_high = float(prior_closes.max())

        # Must close at a new 52-week high
        if last_close <= week52_high:
            return None

        # Must be above 50MA
        if last_close < last_ma50:
            return None

        # Volume confirmation
        if last_vol_ratio < 1.5:
            return None

        # Not extended — within 5% of 52-week high (fresh breakout, not chasing)
        extension_pct = (last_close - week52_high) / week52_high
        if extension_pct > 0.05:
            return None

        # Relative strength filter — top 30% of universe
        if _universe_returns:
            sym_6m_return = _universe_returns.get(symbol)
            if sym_6m_return is not None:
                threshold = np.percentile(list(_universe_returns.values()), 70)
                if sym_6m_return < threshold:
                    return None

        entry = round(last_close, 2)

        # Stop: tighter of ATR-based or below breakout candle low
        atr_stop = entry - config.ATR_STOP_MULTIPLIER * last_atr
        candle_stop = last_low - 0.01  # 1 cent below breakout candle low
        stop = round(max(atr_stop, candle_stop), 2)  # tighter stop

        target = round(entry + config.ATR_TARGET_BREAKOUT * last_atr, 2)

        if stop >= entry or target <= entry:
            return None

        # Score: vol ratio × inverse of extension (fresher = better)
        score = last_vol_ratio * (1 / (1 + extension_pct * 10))

        return Signal(
            symbol=symbol,
            strategy="breakout",
            entry_price=entry,
            stop_price=stop,
            target_price=target,
            score=score,
            atr=last_atr,
            qty=0
        )

    except Exception as e:
        logger.debug(f"breakout signal failed for {symbol}: {e}")
        return None


def get_signals(bars: dict[str, pd.DataFrame]) -> list[Signal]:
    """Run breakout scan across all symbols. Returns ranked list."""
    signals = []
    for symbol, df in bars.items():
        sig = _compute_signals(symbol, df)
        if sig:
            signals.append(sig)
    signals.sort(key=lambda s: s.score, reverse=True)
    logger.info(f"Breakout: {len(signals)} signals found")
    return signals
