"""
AlphaLoop Trade Ledger
-----------------------
Reconciles closed positions from Alpaca against trades.csv.
Determines exit type (TAKE_PROFIT, STOP_LOSS, TIME_STOP), calculates P&L,
and produces per-strategy performance statistics.

Runs automatically at the start of each daily scan.
Does NOT modify any existing functionality — purely additive.
"""
import os
import logging
import pandas as pd
from datetime import datetime, timezone
from alpaca.trading.enums import OrderStatus, OrderSide, OrderType

logger = logging.getLogger(__name__)

JOURNAL_PATH = "journal/trades.csv"

COLUMNS = [
    "date", "symbol", "strategy",
    "entry_price", "stop_price", "target_price",
    "qty", "atr", "risk_reward",
    "entry_date", "exit_date", "exit_price",
    "exit_type", "result", "pnl", "pnl_pct", "hold_days"
]


def _load_journal() -> pd.DataFrame:
    if not os.path.exists(JOURNAL_PATH):
        return pd.DataFrame(columns=COLUMNS)
    df = pd.read_csv(JOURNAL_PATH)
    # Add new columns if journal predates them
    for col in ["exit_type", "pnl_pct", "hold_days"]:
        if col not in df.columns:
            df[col] = ""
    return df


def _save_journal(df: pd.DataFrame) -> None:
    df.to_csv(JOURNAL_PATH, index=False)


def _determine_exit_type(symbol: str, entry_date_str: str, broker_client) -> tuple[str, float, str]:
    """
    Query Alpaca closed orders for this symbol after entry_date.
    Returns (exit_type, exit_price, exit_date_str).
    exit_type: TAKE_PROFIT | STOP_LOSS | TIME_STOP | UNKNOWN
    """
    try:
        from alpaca.trading.requests import GetOrdersRequest
        from alpaca.trading.enums import QueryOrderStatus
        from datetime import timedelta

        entry_dt = pd.to_datetime(entry_date_str).to_pydatetime()
        # Add timezone if missing
        if entry_dt.tzinfo is None:
            entry_dt = entry_dt.replace(tzinfo=timezone.utc)

        orders = broker_client.client.get_orders(GetOrdersRequest(
            status=QueryOrderStatus.CLOSED,
            after=entry_dt - timedelta(days=1),  # slight buffer
            symbols=[symbol],
            limit=50
        ))

        # Find filled SELL orders after entry date
        for order in orders:
            if order.side != OrderSide.SELL:
                continue
            if order.status != OrderStatus.FILLED:
                continue
            if order.filled_at and order.filled_at < entry_dt:
                continue

            exit_price = float(order.filled_avg_price or 0)
            exit_date = order.filled_at.strftime("%Y-%m-%d") if order.filled_at else ""

            order_type = str(order.order_type).upper() if order.order_type else ""

            if "LIMIT" in order_type and "STOP" not in order_type:
                return "TAKE_PROFIT", exit_price, exit_date
            elif "STOP" in order_type:
                return "STOP_LOSS", exit_price, exit_date
            elif "MARKET" in order_type:
                return "TIME_STOP", exit_price, exit_date
            else:
                return "UNKNOWN", exit_price, exit_date

    except Exception as e:
        logger.warning(f"Could not determine exit type for {symbol}: {e}")

    return "UNKNOWN", 0.0, ""


def reconcile(broker_client) -> int:
    """
    Check all open trades in the journal against live Alpaca positions.
    For any position that is now closed on Alpaca, record:
      - exit_type (TAKE_PROFIT / STOP_LOSS / TIME_STOP)
      - exit_price, exit_date, P&L, hold_days

    Returns number of trades reconciled.
    """
    df = _load_journal()
    if df.empty:
        return 0

    open_mask = df["exit_date"].isna() | (df["exit_date"] == "")
    open_trades = df[open_mask]
    if open_trades.empty:
        return 0

    open_on_alpaca = broker_client.get_open_symbols()
    reconciled = 0

    for idx, row in open_trades.iterrows():
        symbol = row["symbol"]

        # Still open on Alpaca — nothing to do
        if symbol in open_on_alpaca:
            continue

        # Position closed — find out how and at what price
        exit_type, exit_price, exit_date = _determine_exit_type(
            symbol, str(row["entry_date"]), broker_client
        )

        if exit_price == 0.0:
            logger.warning(f"Could not get exit price for {symbol} — skipping reconcile")
            continue

        entry_price = float(row["entry_price"])
        qty = int(row["qty"])
        pnl = round((exit_price - entry_price) * qty, 2)
        pnl_pct = round(((exit_price - entry_price) / entry_price) * 100, 2)
        result = "WIN" if pnl > 0 else "LOSS" if pnl < 0 else "BREAKEVEN"

        entry_dt = pd.to_datetime(row["entry_date"])
        exit_dt = pd.to_datetime(exit_date) if exit_date else pd.Timestamp.now()
        hold_days = max(0, (exit_dt - entry_dt).days)

        df.at[idx, "exit_date"]  = exit_date
        df.at[idx, "exit_price"] = exit_price
        df.at[idx, "exit_type"]  = exit_type
        df.at[idx, "result"]     = result
        df.at[idx, "pnl"]        = pnl
        df.at[idx, "pnl_pct"]    = pnl_pct
        df.at[idx, "hold_days"]  = hold_days

        reconciled += 1
        logger.info(
            f"RECONCILED {symbol} [{row['strategy']}] "
            f"exit={exit_type} price={exit_price} "
            f"P&L=${pnl:+.2f} ({pnl_pct:+.2f}%) hold={hold_days}d"
        )

    if reconciled > 0:
        _save_journal(df)
        logger.info(f"Ledger updated — {reconciled} trade(s) reconciled")

    return reconciled


def get_stats() -> dict:
    """
    Compute per-strategy and overall performance statistics from closed trades.
    Returns dict with stats per strategy + overall summary.
    """
    df = _load_journal()
    closed = df[df["exit_date"].notna() & (df["exit_date"] != "")].copy()

    if closed.empty:
        return {"strategies": {}, "overall": {}, "has_data": False}

    closed["pnl"] = pd.to_numeric(closed["pnl"], errors="coerce").fillna(0)
    closed["pnl_pct"] = pd.to_numeric(closed["pnl_pct"], errors="coerce").fillna(0)
    closed["hold_days"] = pd.to_numeric(closed["hold_days"], errors="coerce").fillna(0)

    def _strategy_stats(grp: pd.DataFrame) -> dict:
        total = len(grp)
        winners = grp[grp["pnl"] > 0]
        losers = grp[grp["pnl"] < 0]
        gross_wins = winners["pnl"].sum()
        gross_losses = abs(losers["pnl"].sum())
        profit_factor = round(gross_wins / gross_losses, 2) if gross_losses > 0 else float("inf")

        exit_counts = grp["exit_type"].value_counts().to_dict()

        return {
            "total_closed": total,
            "winners": len(winners),
            "losers": len(losers),
            "win_rate": round(len(winners) / total * 100, 1) if total > 0 else 0,
            "total_pnl": round(grp["pnl"].sum(), 2),
            "avg_win_pnl": round(winners["pnl"].mean(), 2) if not winners.empty else 0,
            "avg_loss_pnl": round(losers["pnl"].mean(), 2) if not losers.empty else 0,
            "avg_win_pct": round(winners["pnl_pct"].mean(), 2) if not winners.empty else 0,
            "avg_loss_pct": round(losers["pnl_pct"].mean(), 2) if not losers.empty else 0,
            "profit_factor": profit_factor,
            "avg_hold_days": round(grp["hold_days"].mean(), 1),
            "exits": {
                "TAKE_PROFIT": exit_counts.get("TAKE_PROFIT", 0),
                "STOP_LOSS":   exit_counts.get("STOP_LOSS", 0),
                "TIME_STOP":   exit_counts.get("TIME_STOP", 0),
                "UNKNOWN":     exit_counts.get("UNKNOWN", 0),
            }
        }

    strategy_stats = {}
    for strat in closed["strategy"].unique():
        strategy_stats[strat] = _strategy_stats(closed[closed["strategy"] == strat])

    overall = _strategy_stats(closed)
    overall["open_trades"] = int((df["exit_date"].isna() | (df["exit_date"] == "")).sum())

    return {
        "strategies": strategy_stats,
        "overall": overall,
        "has_data": True
    }
