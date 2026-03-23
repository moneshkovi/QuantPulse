"""
AlphaLoop Daily Pre-Market Scanner
------------------------------------
Runs all 3 strategies in parallel, selects top 5 per strategy,
places bracket orders via Alpaca paper account.

Usage:
  python scanner/scan.py             # live — places real paper orders
  python scanner/scan.py --dry-run   # preview signals only, no orders placed
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import argparse
import logging
import pandas as pd
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

from data.universe import get_universe
from data.fetch import fetch_bars
from strategies import mean_reversion, momentum, breakout
from strategies.base import Signal
from broker.alpaca_client import AlpacaClient
from notifications.email_client import send_scan_complete, send_error
from journal import ledger
import config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("scanner.log")
    ]
)
logger = logging.getLogger(__name__)


def compute_universe_returns(bars: dict[str, pd.DataFrame]) -> dict[str, float]:
    """6-month returns for all symbols — used by breakout RS filter."""
    returns = {}
    for sym, df in bars.items():
        if len(df) >= 130:
            start = float(df["Close"].iloc[-126])
            end = float(df["Close"].iloc[-1])
            if start > 0:
                returns[sym] = (end - start) / start
    return returns


def log_signals_to_journal(signals: list[Signal], journal_path: str = "journal/trades.csv") -> None:
    rows = []
    today = datetime.now().strftime("%Y-%m-%d")
    for sig in signals:
        rows.append({
            "date": today,
            "symbol": sig.symbol,
            "strategy": sig.strategy,
            "entry_price": sig.entry_price,
            "stop_price": sig.stop_price,
            "target_price": sig.target_price,
            "qty": sig.qty,
            "atr": round(sig.atr, 4),
            "risk_reward": round(sig.risk_reward, 2),
            "entry_date": today,
            "exit_date": "",
            "exit_price": "",
            "result": "",
            "pnl": ""
        })
    if not rows:
        return
    df_new = pd.DataFrame(rows)
    df_new.to_csv(journal_path, mode="a", header=False, index=False)
    logger.info(f"Logged {len(rows)} new signals to journal")


def print_dry_run_table(all_signals: dict[str, list[Signal]], open_symbols: set[str], portfolio_value: float) -> None:
    """Print a formatted preview table of top signals per strategy."""
    print("\n" + "=" * 90)
    print(f"  DRY RUN PREVIEW — {datetime.now().strftime('%Y-%m-%d %H:%M')}  |  Portfolio: ${portfolio_value:,.2f}")
    print("=" * 90)

    for strategy_name in config.STRATEGIES:
        signals = all_signals.get(strategy_name, [])
        print(f"\n  [{strategy_name.upper()}]  —  {len(signals)} total signals, showing top {config.MAX_POSITIONS_PER_STRATEGY}")
        print(f"  {'SYMBOL':<8} {'ENTRY':>8} {'STOP':>8} {'TARGET':>8} {'R:R':>5} {'ATR':>7} {'SCORE':>8}  {'NOTE'}")
        print("  " + "-" * 80)

        shown = 0
        for sig in signals:
            if shown >= config.MAX_POSITIONS_PER_STRATEGY:
                break
            note = "SKIP — already open" if sig.symbol in open_symbols else ""
            # Estimate qty
            risk_per_share = sig.entry_price - sig.stop_price
            qty = max(1, int((portfolio_value * config.RISK_PER_TRADE) / risk_per_share)) if risk_per_share > 0 else 0
            max_qty = max(1, int((portfolio_value * 0.10) / sig.entry_price))
            qty = min(qty, max_qty)
            dollar_exposure = qty * sig.entry_price
            print(
                f"  {sig.symbol:<8} {sig.entry_price:>8.2f} {sig.stop_price:>8.2f} "
                f"{sig.target_price:>8.2f} {sig.risk_reward:>5.1f} {sig.atr:>7.4f} "
                f"{sig.score:>8.3f}  qty={qty} (~${dollar_exposure:,.0f})  {note}"
            )
            shown += 1

        if not signals:
            print("  (no signals)")

    print("\n" + "=" * 90)
    print("  No orders placed. Run without --dry-run to execute.\n")


def run_scan(dry_run: bool = False) -> None:
    mode = "DRY RUN" if dry_run else "LIVE"
    logger.info("=" * 60)
    logger.info(f"AlphaLoop Pre-Market Scan [{mode}] — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    logger.info("=" * 60)

    all_signals: dict[str, list[Signal]] = {}
    placed_orders: list[Signal] = []
    portfolio_value = 0.0
    buying_power = 0.0

    try:
        # Step 1: Broker connection + account info
        broker = AlpacaClient()
        portfolio_value = broker.get_portfolio_value()
        buying_power = broker.get_buying_power()
        logger.info(f"Portfolio: ${portfolio_value:,.2f} | Buying power: ${buying_power:,.2f}")

        # Step 2: Reconcile closed positions + enforce time stops (skip in dry run)
        if not dry_run:
            ledger.reconcile(broker)
            broker.enforce_time_stops()

        # Step 3: Get universe
        logger.info("Loading universe...")
        symbols = get_universe()
        logger.info(f"Universe: {len(symbols)} symbols")

        # Step 4: Download bars for universe
        logger.info("Downloading OHLCV data...")
        bars = fetch_bars(symbols, lookback_days=config.LOOKBACK_DAYS)
        logger.info(f"Data ready for {len(bars)} symbols")

        if not bars:
            raise RuntimeError("No OHLCV data fetched from yfinance — possible rate limit or network issue")

        # Step 5: Compute universe returns (used by breakout RS filter)
        universe_returns = compute_universe_returns(bars)
        breakout.set_universe_returns(universe_returns)

        # Step 6: Run all 3 strategies in parallel
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {
                executor.submit(mean_reversion.get_signals, bars): "mean_reversion",
                executor.submit(momentum.get_signals, bars): "momentum",
                executor.submit(breakout.get_signals, bars): "breakout",
            }
            for future in as_completed(futures):
                strategy_name = futures[future]
                try:
                    all_signals[strategy_name] = future.result()
                except Exception as e:
                    logger.error(f"{strategy_name} scan error: {e}")
                    send_error(f"Strategy scan failed: {strategy_name}", e)
                    all_signals[strategy_name] = []

        open_symbols = broker.get_open_symbols()

        # Step 7a: DRY RUN — print table, email summary, stop
        if dry_run:
            print_dry_run_table(all_signals, open_symbols, portfolio_value)
            send_scan_complete(all_signals, [], portfolio_value, buying_power, dry_run=True)
            return

        # Step 7b: LIVE — place bracket orders
        for strategy_name in config.STRATEGIES:
            signals = all_signals.get(strategy_name, [])
            current_count = broker.count_positions_for_strategy(strategy_name)
            slots_available = config.MAX_POSITIONS_PER_STRATEGY - current_count

            logger.info(f"\n[{strategy_name.upper()}] {len(signals)} signals | {current_count} open | {slots_available} slots")

            if slots_available <= 0:
                logger.info(f"  → At max positions, skipping")
                continue

            placed = 0
            for sig in signals:
                if placed >= slots_available:
                    break
                if sig.symbol in open_symbols:
                    logger.info(f"  → {sig.symbol} already in portfolio, skipping")
                    continue

                order = broker.place_bracket_order(sig, portfolio_value)
                if order:
                    sig.qty = order.qty if hasattr(order, 'qty') else 0
                    placed_orders.append(sig)
                    open_symbols.add(sig.symbol)
                    placed += 1

        # Step 8: Log to journal + email summary
        log_signals_to_journal(placed_orders)
        send_scan_complete(all_signals, placed_orders, portfolio_value, buying_power, dry_run=False)

        # Summary
        logger.info("\n" + "=" * 60)
        logger.info(f"SCAN COMPLETE — {len(placed_orders)} orders placed")
        for sig in placed_orders:
            logger.info(
                f"  {sig.strategy:<16} {sig.symbol:<8} "
                f"entry={sig.entry_price} stop={sig.stop_price} "
                f"target={sig.target_price} R:R={sig.risk_reward:.1f}"
            )
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Scan failed: {e}", exc_info=True)
        send_error("run_scan() top-level failure", e)
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Preview signals without placing orders")
    args = parser.parse_args()
    run_scan(dry_run=args.dry_run)
