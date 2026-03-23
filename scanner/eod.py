"""
AlphaLoop End-of-Day Reconciliation
--------------------------------------
Run this after market close: 3:30 PM CDT / 4:30 PM EDT daily.

What it does:
  1. Pulls all current open positions + today's closed orders from Alpaca
  2. Reconciles exits in the ledger (TAKE_PROFIT / STOP_LOSS / TIME_STOP)
  3. Computes updated performance stats per strategy
  4. Emails a full daily report: what closed today, P&L, running ledger

Usage:
  python scanner/eod.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
import pandas as pd
from datetime import datetime, timezone

from broker.alpaca_client import AlpacaClient
from journal import ledger
from notifications.email_client import send_error, _send
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


def _build_eod_email(
    reconciled_count: int,
    today_closed: list[dict],
    open_positions: list[dict],
    stats: dict,
    portfolio_value: float
) -> str:

    today_str = datetime.now().strftime("%A, %B %d %Y")

    # Today's closed trades table
    if today_closed:
        closed_rows = ""
        for t in today_closed:
            pnl_color = "#10b981" if t["pnl"] >= 0 else "#ef4444"
            exit_badge_colors = {
                "TAKE_PROFIT": "#10b981",
                "STOP_LOSS":   "#ef4444",
                "TIME_STOP":   "#f59e0b",
                "UNKNOWN":     "#94a3b8"
            }
            badge_color = exit_badge_colors.get(t["exit_type"], "#94a3b8")
            closed_rows += f"""
            <tr>
              <td style="padding:7px 12px;font-weight:bold;">{t['symbol']}</td>
              <td style="padding:7px 12px;color:#64748b;">{t['strategy'].replace('_',' ').title()}</td>
              <td style="padding:7px 12px;">${t['entry_price']:.2f}</td>
              <td style="padding:7px 12px;">${t['exit_price']:.2f}</td>
              <td style="padding:7px 12px;">
                <span style="background:{badge_color};color:white;padding:2px 7px;border-radius:4px;font-size:11px;">
                  {t['exit_type'].replace('_',' ')}
                </span>
              </td>
              <td style="padding:7px 12px;">{t['hold_days']}d</td>
              <td style="padding:7px 12px;font-weight:bold;color:{pnl_color};">${t['pnl']:+.2f} ({t['pnl_pct']:+.1f}%)</td>
            </tr>"""
        closed_section = f"""
        <h3 style="color:#1e293b;margin-top:20px;">Closed Today ({len(today_closed)} trade{"s" if len(today_closed)!=1 else ""})</h3>
        <table width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse;font-size:14px;">
          <thead>
            <tr style="background:#f1f5f9;color:#64748b;text-align:left;">
              <th style="padding:7px 12px;">Symbol</th>
              <th style="padding:7px 12px;">Strategy</th>
              <th style="padding:7px 12px;">Entry</th>
              <th style="padding:7px 12px;">Exit</th>
              <th style="padding:7px 12px;">Exit Type</th>
              <th style="padding:7px 12px;">Hold</th>
              <th style="padding:7px 12px;">P&amp;L</th>
            </tr>
          </thead>
          <tbody>{closed_rows}</tbody>
        </table>"""
    else:
        closed_section = """
        <h3 style="color:#1e293b;margin-top:20px;">Closed Today</h3>
        <p style="color:#94a3b8;">No positions closed today.</p>"""

    # Open positions table
    if open_positions:
        open_rows = ""
        for p in open_positions:
            unr_color = "#10b981" if p["unrealized_pnl"] >= 0 else "#ef4444"
            open_rows += f"""
            <tr>
              <td style="padding:7px 12px;font-weight:bold;">{p['symbol']}</td>
              <td style="padding:7px 12px;color:#64748b;">{p['strategy']}</td>
              <td style="padding:7px 12px;">{p['qty']}</td>
              <td style="padding:7px 12px;">${p['entry_price']:.2f}</td>
              <td style="padding:7px 12px;">${p['current_price']:.2f}</td>
              <td style="padding:7px 12px;color:#ef4444;">${p['stop_price']:.2f}</td>
              <td style="padding:7px 12px;color:#10b981;">${p['target_price']:.2f}</td>
              <td style="padding:7px 12px;">{p['days_open']}d</td>
              <td style="padding:7px 12px;font-weight:bold;color:{unr_color};">${p['unrealized_pnl']:+.2f} ({p['unrealized_pct']:+.1f}%)</td>
            </tr>"""
        open_section = f"""
        <h3 style="color:#1e293b;margin-top:24px;">Open Positions ({len(open_positions)})</h3>
        <table width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse;font-size:14px;">
          <thead>
            <tr style="background:#f1f5f9;color:#64748b;text-align:left;">
              <th style="padding:7px 12px;">Symbol</th>
              <th style="padding:7px 12px;">Strategy</th>
              <th style="padding:7px 12px;">Qty</th>
              <th style="padding:7px 12px;">Entry</th>
              <th style="padding:7px 12px;">Current</th>
              <th style="padding:7px 12px;">Stop</th>
              <th style="padding:7px 12px;">Target</th>
              <th style="padding:7px 12px;">Days</th>
              <th style="padding:7px 12px;">Unrealized P&amp;L</th>
            </tr>
          </thead>
          <tbody>{open_rows}</tbody>
        </table>"""
    else:
        open_section = """
        <h3 style="color:#1e293b;margin-top:24px;">Open Positions</h3>
        <p style="color:#94a3b8;">No open positions.</p>"""

    # Ledger stats
    ledger_section = ""
    if stats["has_data"]:
        ov = stats["overall"]
        win_color = "#10b981" if ov.get("win_rate", 0) >= 55 else "#f59e0b"
        pnl_color = "#10b981" if ov.get("total_pnl", 0) >= 0 else "#ef4444"

        strat_rows = ""
        for strat, s in stats["strategies"].items():
            label = strat.replace("_", " ").title()
            wr_color = "#10b981" if s["win_rate"] >= 55 else "#f59e0b"
            strat_rows += f"""
            <tr>
              <td style="padding:6px 12px;">{label}</td>
              <td style="padding:6px 12px;">{s['total_closed']}</td>
              <td style="padding:6px 12px;color:{wr_color};font-weight:bold;">{s['win_rate']}%</td>
              <td style="padding:6px 12px;">{s['winners']} W / {s['losers']} L</td>
              <td style="padding:6px 12px;">{s['profit_factor']}</td>
              <td style="padding:6px 12px;color:#10b981;">${s['avg_win_pnl']:+.2f}</td>
              <td style="padding:6px 12px;color:#ef4444;">${s['avg_loss_pnl']:+.2f}</td>
              <td style="padding:6px 12px;">{s['exits']['TAKE_PROFIT']} TP / {s['exits']['STOP_LOSS']} SL / {s['exits']['TIME_STOP']} TS</td>
              <td style="padding:6px 12px;font-weight:bold;">${s['total_pnl']:+,.2f}</td>
            </tr>"""

        ledger_section = f"""
        <h3 style="color:#1e293b;margin-top:24px;border-top:2px solid #e2e8f0;padding-top:20px;">
          Running Ledger — All Time
        </h3>
        <div style="background:#0f172a;padding:12px 16px;border-radius:6px;margin-bottom:12px;color:white;font-size:14px;">
          {ov['total_closed']} closed trades &nbsp;·&nbsp;
          <span style="color:{win_color};font-weight:bold;">{ov['win_rate']}% win rate</span>
          &nbsp;·&nbsp;
          <span style="color:{pnl_color};font-weight:bold;">${ov['total_pnl']:+,.2f} total P&amp;L</span>
          &nbsp;·&nbsp; Profit factor: {ov['profit_factor']}
          &nbsp;·&nbsp; Avg hold: {ov['avg_hold_days']} days
        </div>
        <table width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse;font-size:13px;">
          <thead>
            <tr style="background:#f1f5f9;color:#64748b;text-align:left;">
              <th style="padding:6px 12px;">Strategy</th>
              <th style="padding:6px 12px;">Trades</th>
              <th style="padding:6px 12px;">Win Rate</th>
              <th style="padding:6px 12px;">W / L</th>
              <th style="padding:6px 12px;">Prof. Factor</th>
              <th style="padding:6px 12px;">Avg Win</th>
              <th style="padding:6px 12px;">Avg Loss</th>
              <th style="padding:6px 12px;">Exits</th>
              <th style="padding:6px 12px;">Total P&amp;L</th>
            </tr>
          </thead>
          <tbody>{strat_rows}</tbody>
        </table>"""

    return f"""
    <div style="font-family:Arial,sans-serif;max-width:800px;margin:0 auto;color:#1e293b;">
      <div style="background:#1e293b;padding:20px 24px;border-radius:8px 8px 0 0;">
        <h1 style="color:white;margin:0;font-size:20px;">AlphaLoop — End of Day</h1>
        <p style="color:#94a3b8;margin:4px 0 0;">{today_str}</p>
      </div>
      <div style="background:#f8fafc;padding:14px 24px;border-bottom:1px solid #e2e8f0;">
        <table width="100%">
          <tr>
            <td><strong>Portfolio Value</strong><br>
              <span style="font-size:20px;color:#0f172a;">${portfolio_value:,.2f}</span></td>
            <td><strong>Closed Today</strong><br>
              <span style="font-size:20px;color:#0f172a;">{len(today_closed)}</span></td>
            <td><strong>Still Open</strong><br>
              <span style="font-size:20px;color:#0f172a;">{len(open_positions)}</span></td>
            <td><strong>Today's P&amp;L</strong><br>
              <span style="font-size:20px;color:{'#10b981' if sum(t['pnl'] for t in today_closed) >= 0 else '#ef4444'};">
                ${sum(t['pnl'] for t in today_closed):+,.2f}
              </span>
            </td>
          </tr>
        </table>
      </div>
      <div style="padding:16px 24px;">
        {closed_section}
        {open_section}
        {ledger_section}
      </div>
      <div style="padding:12px 24px;background:#f1f5f9;border-radius:0 0 8px 8px;font-size:12px;color:#94a3b8;">
        AlphaLoop · End of Day Report · {datetime.now().strftime('%Y-%m-%d %H:%M')}
      </div>
    </div>"""


def run_eod() -> None:
    logger.info("=" * 60)
    logger.info(f"AlphaLoop EOD Reconciliation — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    logger.info("=" * 60)

    try:
        broker = AlpacaClient()
        portfolio_value = broker.get_portfolio_value()
        logger.info(f"Portfolio: ${portfolio_value:,.2f}")

        # Step 1: Reconcile any closed positions
        reconciled = ledger.reconcile(broker)
        logger.info(f"Reconciled {reconciled} position(s)")

        # Step 2: Get today's closed trades from journal
        today_str = datetime.now().strftime("%Y-%m-%d")
        df = pd.read_csv(ledger.JOURNAL_PATH) if os.path.exists(ledger.JOURNAL_PATH) else pd.DataFrame()

        today_closed = []
        if not df.empty and "exit_date" in df.columns:
            today_exits = df[df["exit_date"] == today_str]
            for _, row in today_exits.iterrows():
                today_closed.append({
                    "symbol":       row["symbol"],
                    "strategy":     row["strategy"],
                    "entry_price":  float(row["entry_price"]),
                    "exit_price":   float(row.get("exit_price", 0) or 0),
                    "exit_type":    str(row.get("exit_type", "UNKNOWN") or "UNKNOWN"),
                    "pnl":          float(row.get("pnl", 0) or 0),
                    "pnl_pct":      float(row.get("pnl_pct", 0) or 0),
                    "hold_days":    int(row.get("hold_days", 0) or 0),
                })

        # Step 3: Get current open positions with unrealized P&L
        alpaca_positions = broker.get_open_positions()
        open_df = pd.read_csv(ledger.JOURNAL_PATH) if os.path.exists(ledger.JOURNAL_PATH) else pd.DataFrame()
        open_journal = {}
        if not open_df.empty:
            open_rows = open_df[open_df["exit_date"].isna() | (open_df["exit_date"] == "")]
            for _, row in open_rows.iterrows():
                open_journal[row["symbol"]] = row

        open_positions = []
        today_date = datetime.now(timezone.utc).date()
        for pos in alpaca_positions:
            sym = pos.symbol
            entry_price = float(pos.avg_entry_price or 0)
            current_price = float(pos.current_price or 0)
            qty = int(float(pos.qty or 0))
            unrealized_pnl = float(pos.unrealized_pl or 0)
            unrealized_pct = float(pos.unrealized_plpc or 0) * 100

            # Get strategy + stop/target from journal
            j = open_journal.get(sym, {})
            strategy = str(j.get("strategy", "unknown")) if hasattr(j, 'get') else "unknown"
            stop_price = float(j.get("stop_price", 0)) if hasattr(j, 'get') else 0
            target_price = float(j.get("target_price", 0)) if hasattr(j, 'get') else 0
            entry_date_str = str(j.get("entry_date", "")) if hasattr(j, 'get') else ""
            try:
                days_open = (today_date - pd.to_datetime(entry_date_str).date()).days if entry_date_str else 0
            except Exception:
                days_open = 0

            open_positions.append({
                "symbol": sym,
                "strategy": strategy.replace("_", " ").title(),
                "qty": qty,
                "entry_price": entry_price,
                "current_price": current_price,
                "stop_price": stop_price,
                "target_price": target_price,
                "unrealized_pnl": unrealized_pnl,
                "unrealized_pct": unrealized_pct,
                "days_open": days_open,
            })

        # Step 4: Get updated stats
        stats = ledger.get_stats()

        # Step 5: Build and send email
        body_html = _build_eod_email(reconciled, today_closed, open_positions, stats, portfolio_value)
        subject = f"[AlphaLoop] EOD Report — {today_str}"
        _send(subject, body_html)

        logger.info(f"EOD complete — {len(today_closed)} closed today, {len(open_positions)} still open")

    except Exception as e:
        logger.error(f"EOD failed: {e}", exc_info=True)
        send_error("EOD reconciliation failure", e)
        raise


if __name__ == "__main__":
    run_eod()
