"""
OHLCV data fetcher using yfinance.
Downloads daily bars in batches of 500 to avoid rate limiting.
"""
import time
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

BATCH_SIZE = 500
BATCH_DELAY_SECONDS = 3  # pause between batches to respect rate limits


def _download_batch(batch: list[str], start: str, end: str) -> dict[str, pd.DataFrame]:
    """Download one batch and return parsed symbol -> DataFrame dict."""
    result = {}
    try:
        raw = yf.download(
            batch,
            start=start,
            end=end,
            progress=False,
            threads=True,
            auto_adjust=True,
            group_by="ticker"
        )
        if raw.empty:
            return result

        if len(batch) == 1:
            sym = batch[0]
            df = raw.dropna()
            if len(df) >= 50:
                result[sym] = df
            return result

        for sym in batch:
            try:
                df = raw[sym].dropna()
                if len(df) >= 50:
                    result[sym] = df
            except Exception:
                continue

    except Exception as e:
        logger.warning(f"Batch download error: {e}")

    return result


def fetch_bars(symbols: list[str], lookback_days: int = 252) -> dict[str, pd.DataFrame]:
    """
    Download daily OHLCV bars for symbols in batches of 500.
    Returns dict: {symbol: DataFrame with columns Open, High, Low, Close, Volume}
    """
    end = datetime.now()
    start = end - timedelta(days=lookback_days + 10)
    start_str = start.strftime("%Y-%m-%d")
    end_str = end.strftime("%Y-%m-%d")

    total = len(symbols)
    logger.info(f"Downloading {total} symbols in batches of {BATCH_SIZE}, {lookback_days}d lookback")

    result = {}
    batches = [symbols[i:i + BATCH_SIZE] for i in range(0, total, BATCH_SIZE)]

    for i, batch in enumerate(batches, 1):
        logger.info(f"  Batch {i}/{len(batches)} ({len(batch)} symbols)...")
        batch_result = _download_batch(batch, start_str, end_str)
        result.update(batch_result)
        if i < len(batches):
            time.sleep(BATCH_DELAY_SECONDS)

    logger.info(f"Successfully fetched data for {len(result)}/{total} symbols")
    return result


def compute_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """ATR(n) — average true range over n periods."""
    high = df["High"]
    low = df["Low"]
    prev_close = df["Close"].shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs()
    ], axis=1).max(axis=1)
    return tr.rolling(period).mean()
