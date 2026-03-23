"""
Universe builder — all US-listed equities filtered by price and volume.
Cached weekly to avoid hammering APIs on every daily scan.
"""
import os
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import GetAssetsRequest
from alpaca.trading.enums import AssetClass, AssetStatus
import config
import logging

logger = logging.getLogger(__name__)


def _is_cache_fresh() -> bool:
    if not os.path.exists(config.UNIVERSE_CACHE_FILE):
        return False
    age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(config.UNIVERSE_CACHE_FILE))
    return age.days < config.UNIVERSE_REFRESH_DAYS


def _fetch_from_alpaca() -> list[str]:
    """Pull all active, tradeable US equity symbols from Alpaca."""
    client = TradingClient(config.ALPACA_API_KEY, config.ALPACA_SECRET_KEY, paper=True)
    assets = client.get_all_assets(GetAssetsRequest(
        asset_class=AssetClass.US_EQUITY,
        status=AssetStatus.ACTIVE
    ))
    symbols = [
        a.symbol for a in assets
        if a.tradable and a.fractionable is not False
        and "." not in a.symbol  # exclude ADRs with dots
        and "/" not in a.symbol  # exclude warrants/rights
    ]
    logger.info(f"Alpaca returned {len(symbols)} tradeable US equities")
    return symbols


def _filter_by_liquidity(symbols: list[str]) -> pd.DataFrame:
    """
    Download last 20 days of data in batches and filter by price + volume.
    Returns DataFrame with columns: symbol, last_price, avg_volume
    """
    results = []
    batch_size = 200
    end = datetime.now()
    start = end - timedelta(days=30)

    for i in range(0, len(symbols), batch_size):
        batch = symbols[i:i + batch_size]
        logger.info(f"Filtering batch {i // batch_size + 1}/{(len(symbols) // batch_size) + 1}")
        try:
            data = yf.download(
                batch,
                start=start.strftime("%Y-%m-%d"),
                end=end.strftime("%Y-%m-%d"),
                progress=False,
                threads=True,
                auto_adjust=True
            )
            if data.empty:
                continue

            closes = data["Close"]
            volumes = data["Volume"]

            for sym in batch:
                try:
                    if sym not in closes.columns:
                        continue
                    sym_close = closes[sym].dropna()
                    sym_vol = volumes[sym].dropna()
                    if len(sym_close) < 5:
                        continue
                    last_price = float(sym_close.iloc[-1])
                    avg_volume = float(sym_vol.tail(20).mean())
                    if last_price >= config.MIN_PRICE and avg_volume >= config.MIN_AVG_VOLUME:
                        results.append({"symbol": sym, "last_price": last_price, "avg_volume": avg_volume})
                except Exception:
                    continue
        except Exception as e:
            logger.warning(f"Batch {i} failed: {e}")
            continue

    df = pd.DataFrame(results)
    logger.info(f"Universe filtered to {len(df)} symbols (price ≥ ${config.MIN_PRICE}, vol ≥ {config.MIN_AVG_VOLUME:,})")
    return df


def get_universe(force_refresh: bool = False) -> list[str]:
    """
    Return list of filtered US equity symbols.
    Uses cached file if fresh, otherwise rebuilds from scratch.
    """
    if not force_refresh and _is_cache_fresh():
        df = pd.read_csv(config.UNIVERSE_CACHE_FILE)
        logger.info(f"Loaded universe from cache: {len(df)} symbols")
        return df["symbol"].tolist()

    logger.info("Building universe from scratch...")
    raw_symbols = _fetch_from_alpaca()
    filtered_df = _filter_by_liquidity(raw_symbols)

    os.makedirs(os.path.dirname(config.UNIVERSE_CACHE_FILE), exist_ok=True)
    filtered_df.to_csv(config.UNIVERSE_CACHE_FILE, index=False)
    logger.info(f"Universe cached: {len(filtered_df)} symbols")

    return filtered_df["symbol"].tolist()
