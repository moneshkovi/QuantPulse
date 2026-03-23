"""
Email notification client.
Sends scan summaries and error alerts to the configured address.
"""
import smtplib
import traceback
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import logging
import config
from strategies.base import Signal
from journal import ledger

logger = logging.getLogger(__name__)

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587


def _send(subject: str, body_html: str) -> None:
    if not config.EMAIL_ADDRESS or not config.EMAIL_APP_PASSWORD:
        logger.warning("Email credentials not set — skipping notification")
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = config.EMAIL_ADDRESS
    msg["To"] = config.EMAIL_ADDRESS
    msg.attach(MIMEText(body_html, "html"))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(config.EMAIL_ADDRESS, config.EMAIL_APP_PASSWORD)
            server.sendmail(config.EMAIL_ADDRESS, config.EMAIL_ADDRESS, msg.as_string())
        logger.info(f"Email sent: {subject}")
    except Exception as e:
        logger.error(f"Failed to send email: {e}")


def send_scan_complete(
    all_signals: dict[str, list[Signal]],
    placed_orders: list[Signal],
    portfolio_value: float,
    buying_power: float,
    dry_run: bool = False
) -> None:
    mode_badge = (
        '<span style="background:#f59e0b;color:white;padding:2px 8px;border-radius:4px;font-size:12px;">DRY RUN</span>'
        if dry_run else
        '<span style="background:#10b981;color:white;padding:2px 8px;border-radius:4px;font-size:12px;">LIVE</span>'
    )
    subject = f"[AlphaLoop] Scan Complete {'(Dry Run)' if dry_run else ''} — {datetime.now().strftime('%Y-%m-%d %H:%M')}"

    # Build signals table per strategy
    strategy_sections = ""
    for strat in config.STRATEGIES:
        sigs = all_signals.get(strat, [])
        top = sigs[:config.MAX_POSITIONS_PER_STRATEGY]
        rows = ""
        for s in top:
            placed_mark = "✅" if any(p.symbol == s.symbol and p.strategy == s.strategy for p in placed_orders) else "—"
            rows += f"""
            <tr>
              <td style="padding:6px 12px;">{s.symbol}</td>
              <td style="padding:6px 12px;">${s.entry_price:.2f}</td>
              <td style="padding:6px 12px;color:#ef4444;">${s.stop_price:.2f}</td>
              <td style="padding:6px 12px;color:#10b981;">${s.target_price:.2f}</td>
              <td style="padding:6px 12px;">{s.risk_reward:.1f}x</td>
              <td style="padding:6px 12px;">{s.atr:.4f}</td>
              <td style="padding:6px 12px;text-align:center;">{placed_mark}</td>
            </tr>"""
        if not rows:
            rows = '<tr><td colspan="7" style="padding:6px 12px;color:#9ca3af;">No signals today</td></tr>'

        label = strat.replace("_", " ").title()
        strategy_sections += f"""
        <h3 style="color:#1e293b;margin-top:24px;">{label} <span style="font-size:13px;color:#64748b;">({len(sigs)} signals)</span></h3>
        <table width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse;font-size:14px;">
          <thead>
            <tr style="background:#f1f5f9;color:#64748b;text-align:left;">
              <th style="padding:6px 12px;">Symbol</th>
              <th style="padding:6px 12px;">Entry</th>
              <th style="padding:6px 12px;">Stop</th>
              <th style="padding:6px 12px;">Target</th>
              <th style="padding:6px 12px;">R:R</th>
              <th style="padding:6px 12px;">ATR</th>
              <th style="padding:6px 12px;">Placed</th>
            </tr>
          </thead>
          <tbody>{rows}</tbody>
        </table>"""

    # Ledger performance stats section
    stats = ledger.get_stats()
    ledger_section = ""
    if stats["has_data"]:
        ov = stats["overall"]
        win_color = "#10b981" if ov.get("win_rate", 0) >= 55 else "#f59e0b"
        pnl_color = "#10b981" if ov.get("total_pnl", 0) >= 0 else "#ef4444"
        pnl_sign  = "+" if ov.get("total_pnl", 0) >= 0 else ""

        strat_rows = ""
        for strat, s in stats["strategies"].items():
            label = strat.replace("_", " ").title()
            wr_color = "#10b981" if s["win_rate"] >= 55 else "#f59e0b"
            sp = "+" if s["total_pnl"] >= 0 else ""
            strat_rows += f"""
            <tr>
              <td style="padding:6px 12px;">{label}</td>
              <td style="padding:6px 12px;">{s['total_closed']}</td>
              <td style="padding:6px 12px;color:{wr_color};font-weight:bold;">{s['win_rate']}%</td>
              <td style="padding:6px 12px;">{s['winners']} / {s['losers']}</td>
              <td style="padding:6px 12px;">{s['profit_factor']}</td>
              <td style="padding:6px 12px;color:#10b981;">${s['avg_win_pnl']:+.2f}</td>
              <td style="padding:6px 12px;color:#ef4444;">${s['avg_loss_pnl']:+.2f}</td>
              <td style="padding:6px 12px;">{s['exits']['TAKE_PROFIT']} TP / {s['exits']['STOP_LOSS']} SL / {s['exits']['TIME_STOP']} TS</td>
              <td style="padding:6px 12px;font-weight:bold;">{sp}${s['total_pnl']:,.2f}</td>
            </tr>"""

        ledger_section = f"""
        <h3 style="color:#1e293b;margin-top:28px;border-top:2px solid #e2e8f0;padding-top:20px;">
          Performance Ledger
          <span style="font-size:13px;color:#64748b;font-weight:normal;">
            {ov['total_closed']} closed · {ov['open_trades']} open
          </span>
        </h3>
        <table width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse;font-size:13px;margin-bottom:12px;">
          <tr style="background:#0f172a;color:white;">
            <td colspan="9" style="padding:10px 12px;font-size:15px;">
              Overall &nbsp;
              <span style="color:{win_color};font-weight:bold;">{ov['win_rate']}% win rate</span>
              &nbsp;·&nbsp;
              <span style="color:{pnl_color};font-weight:bold;">{pnl_sign}${ov['total_pnl']:,.2f} P&amp;L</span>
              &nbsp;·&nbsp; Profit factor: {ov['profit_factor']}
              &nbsp;·&nbsp; Avg hold: {ov['avg_hold_days']}d
            </td>
          </tr>
        </table>
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

    body_html = f"""
    <div style="font-family:Arial,sans-serif;max-width:760px;margin:0 auto;color:#1e293b;">
      <div style="background:#0f172a;padding:20px 24px;border-radius:8px 8px 0 0;">
        <h1 style="color:white;margin:0;font-size:20px;">AlphaLoop {mode_badge}</h1>
        <p style="color:#94a3b8;margin:4px 0 0;">{datetime.now().strftime('%A, %B %d %Y — %H:%M')}</p>
      </div>
      <div style="background:#f8fafc;padding:16px 24px;border-bottom:1px solid #e2e8f0;">
        <table width="100%">
          <tr>
            <td><strong>Portfolio</strong><br><span style="font-size:20px;color:#0f172a;">${portfolio_value:,.2f}</span></td>
            <td><strong>Buying Power</strong><br><span style="font-size:20px;color:#0f172a;">${buying_power:,.2f}</span></td>
            <td><strong>Orders Placed</strong><br><span style="font-size:20px;color:#10b981;">{len(placed_orders)}</span></td>
          </tr>
        </table>
      </div>
      <div style="padding:16px 24px;">
        {strategy_sections}
        {ledger_section}
      </div>
      <div style="padding:12px 24px;background:#f1f5f9;border-radius:0 0 8px 8px;font-size:12px;color:#94a3b8;">
        AlphaLoop · Paper Trading · Time stop: {config.TIME_STOP_DAYS} days · Risk per trade: {config.RISK_PER_TRADE*100:.0f}%
      </div>
    </div>"""

    _send(subject, body_html)


def send_error(context: str, error: Exception) -> None:
    subject = f"[AlphaLoop] ERROR — {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    tb = traceback.format_exc()
    body_html = f"""
    <div style="font-family:Arial,sans-serif;max-width:700px;margin:0 auto;color:#1e293b;">
      <div style="background:#ef4444;padding:20px 24px;border-radius:8px 8px 0 0;">
        <h1 style="color:white;margin:0;font-size:20px;">AlphaLoop Error</h1>
        <p style="color:#fecaca;margin:4px 0 0;">{datetime.now().strftime('%A, %B %d %Y — %H:%M')}</p>
      </div>
      <div style="padding:20px 24px;">
        <p><strong>Context:</strong> {context}</p>
        <p><strong>Error:</strong> <span style="color:#ef4444;">{type(error).__name__}: {error}</span></p>
        <pre style="background:#f8fafc;padding:16px;border-radius:6px;font-size:12px;overflow-x:auto;border-left:4px solid #ef4444;">{tb}</pre>
      </div>
    </div>"""
    _send(subject, body_html)
