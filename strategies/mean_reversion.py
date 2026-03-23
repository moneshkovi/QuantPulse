"""
Mean Reversion Strategy
-----------------------
Edge: Stocks that panic-sell beyond 2 std devs below their mean revert.
Institutional rebalancing + retail overshooting = temporary mispricing.

Entry conditions:
  - RSI(2) < 10  [using RSI(2) not RSI(14) — Larry Connors' proven short-term variant]
  - Price ≤ lower Bollinger Band (20MA, 2 std)
  - Volume ≥ 1.5x 20-day average (confirms climactic selling, not just drift)
  - Price > 50-day MA (in uptrend — avoid catching falling knives)

Exit:
  - Take profit: entry + 2x ATR(14)
  - Stop loss: entry - 1.5x ATR(14)
  - Time stop: 10 days (handled by broker layer)

Signal score: inversely proportional to RSI(2) + BB deviation depth
"""
import pandas as pd
import numpy as np
import ta as ta_lib
import logging
from data.fetch import compute_atr
from strategies.base import Signal
import config

logger = logging.getLogger(__name__)


def _compute_signals(symbol: str, df: pd.DataFrame) -> Signal | None:
    try:
        close = df["Close"]
        volume = df["Volume"]

        # RSI(2) — short-term mean reversion indicator (Connors Research)
        rsi2 = ta_lib.momentum.RSIIndicator(close, window=2).rsi()
        if rsi2 is None or rsi2.isna().all():
            return None

        # Bollinger Bands (20, 2)
        bb = ta_lib.volatility.BollingerBands(close, window=20, window_dev=2)
        lower_band = bb.bollinger_lband()

        # 50-day MA filter — only trade in uptrends
        ma50 = close.rolling(50).mean()

        # Volume ratio
        avg_vol_20 = volume.rolling(20).mean()
        vol_ratio = volume / avg_vol_20

        # ATR(14)
        atr = compute_atr(df, 14)

        # Latest values
        idx = -1
        last_close = float(close.iloc[idx])
        last_rsi2 = float(rsi2.iloc[idx])
        last_lower_bb = float(lower_band.iloc[idx])
        last_ma50 = float(ma50.iloc[idx])
        last_vol_ratio = float(vol_ratio.iloc[idx])
        last_atr = float(atr.iloc[idx])

        if any(np.isnan([last_rsi2, last_lower_bb, last_ma50, last_vol_ratio, last_atr])):
            return None

        # Entry conditions
        if last_rsi2 >= 10:
            return None
        if last_close > last_lower_bb:
            return None
        if last_vol_ratio < 1.5:
            return None
        if last_close < last_ma50:  # don't catch falling knives
            return None

        entry = round(last_close, 2)
        stop = round(entry - config.ATR_STOP_MULTIPLIER * last_atr, 2)
        target = round(entry + config.ATR_TARGET_MR * last_atr, 2)

        if stop >= entry or target <= entry:
            return None

        # Position sizing: risk 1% of capital
        risk_per_share = entry - stop
        capital_at_risk = config.RISK_PER_TRADE  # fraction, e.g. 0.01
        # Qty computed in scanner once capital is known
        qty = 0  # placeholder

        # Score: lower RSI2 = stronger signal; deeper below BB = better
        bb_deviation = (last_lower_bb - last_close) / last_lower_bb
        score = (10 - last_rsi2) * (1 + bb_deviation) * last_vol_ratio

        return Signal(
            symbol=symbol,
            strategy="mean_reversion",
            entry_price=entry,
            stop_price=stop,
            target_price=target,
            score=score,
            atr=last_atr,
            qty=qty
        )

    except Exception as e:
        logger.debug(f"mean_reversion signal failed for {symbol}: {e}")
        return None


def get_signals(bars: dict[str, pd.DataFrame]) -> list[Signal]:
    """Run mean reversion scan across all symbols. Returns ranked list."""
    signals = []
    for symbol, df in bars.items():
        sig = _compute_signals(symbol, df)
        if sig:
            signals.append(sig)
    signals.sort(key=lambda s: s.score, reverse=True)
    logger.info(f"Mean reversion: {len(signals)} signals found")
    return signals
