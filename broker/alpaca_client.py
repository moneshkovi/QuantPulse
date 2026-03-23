"""
Alpaca Paper Trading Broker Layer
----------------------------------
Handles: bracket order placement, position tracking, time stop enforcement.
"""
import logging
from datetime import datetime, timezone
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import (
    LimitOrderRequest, GetOrdersRequest,
    ClosePositionRequest
)
from alpaca.trading.models import Order, Position
from alpaca.trading.enums import OrderSide, TimeInForce, OrderClass, QueryOrderStatus
from alpaca.trading.requests import TakeProfitRequest, StopLossRequest
import config
from strategies.base import Signal

logger = logging.getLogger(__name__)


class AlpacaClient:

    def __init__(self):
        self.client = TradingClient(
            api_key=config.ALPACA_API_KEY,
            secret_key=config.ALPACA_SECRET_KEY,
            paper=True
        )

    def get_account(self):
        return self.client.get_account()

    def get_buying_power(self) -> float:
        account = self.get_account()
        return float(account.buying_power)

    def get_portfolio_value(self) -> float:
        account = self.get_account()
        return float(account.portfolio_value)

    def get_open_positions(self) -> list[Position]:
        return self.client.get_all_positions()

    def get_open_symbols(self) -> set[str]:
        return {p.symbol for p in self.get_open_positions()}

    def get_positions_by_strategy(self) -> dict[str, list[str]]:
        """
        Returns dict of strategy -> [symbols] based on open orders.
        Tracks via order client_order_id prefix: 'mr_', 'mo_', 'bo_'
        """
        orders = self.client.get_orders(GetOrdersRequest(status=QueryOrderStatus.OPEN))
        strategy_map = {"mean_reversion": [], "momentum": [], "breakout": []}
        prefix_map = {"mr_": "mean_reversion", "mo_": "momentum", "bo_": "breakout"}
        for order in orders:
            cid = order.client_order_id or ""
            for prefix, strat in prefix_map.items():
                if cid.startswith(prefix):
                    strategy_map[strat].append(order.symbol)
        return strategy_map

    def count_positions_for_strategy(self, strategy: str) -> int:
        strategy_map = self.get_positions_by_strategy()
        return len(strategy_map.get(strategy, []))

    def place_bracket_order(self, signal: Signal, capital: float) -> Order | None:
        """
        Place a bracket limit order: entry limit + stop loss + take profit.
        Position sized by 1% risk of capital.
        """
        risk_per_share = signal.entry_price - signal.stop_price
        if risk_per_share <= 0:
            logger.warning(f"Invalid risk for {signal.symbol}: {risk_per_share}")
            return None

        dollar_risk = capital * config.RISK_PER_TRADE
        qty = max(1, int(dollar_risk / risk_per_share))

        # Don't put more than 10% of portfolio into a single position
        max_position_value = capital * 0.10
        max_qty_by_value = max(1, int(max_position_value / signal.entry_price))
        qty = min(qty, max_qty_by_value)

        prefix = {"mean_reversion": "mr_", "momentum": "mo_", "breakout": "bo_"}
        client_order_id = f"{prefix.get(signal.strategy, 'xx_')}{signal.symbol}_{datetime.now().strftime('%Y%m%d%H%M%S')}"

        order_data = LimitOrderRequest(
            symbol=signal.symbol,
            qty=qty,
            side=OrderSide.BUY,
            time_in_force=TimeInForce.DAY,
            limit_price=signal.entry_price,
            order_class=OrderClass.BRACKET,
            take_profit=TakeProfitRequest(limit_price=signal.target_price),
            stop_loss=StopLossRequest(stop_price=signal.stop_price),
            client_order_id=client_order_id
        )

        try:
            order = self.client.submit_order(order_data)
            logger.info(
                f"ORDER PLACED [{signal.strategy}] {signal.symbol} "
                f"qty={qty} entry={signal.entry_price} "
                f"stop={signal.stop_price} target={signal.target_price} "
                f"R:R={signal.risk_reward:.1f}"
            )
            return order
        except Exception as e:
            logger.error(f"Failed to place order for {signal.symbol}: {e}")
            return None

    def get_closed_orders(self, after: datetime = None) -> list:
        """Return all closed/filled orders, optionally after a given datetime."""
        from alpaca.trading.requests import GetOrdersRequest
        params = GetOrdersRequest(status=QueryOrderStatus.CLOSED, limit=500)
        if after:
            params.after = after
        try:
            return self.client.get_orders(params)
        except Exception as e:
            logger.warning(f"Could not fetch closed orders: {e}")
            return []

    def enforce_time_stops(self, journal_path: str = "journal/trades.csv") -> None:
        """
        Close positions that have been open for TIME_STOP_DAYS or more.
        Reads entry dates from journal CSV.
        """
        import pandas as pd
        import os

        if not os.path.exists(journal_path):
            return

        journal = pd.read_csv(journal_path)
        if journal.empty or "entry_date" not in journal.columns:
            return

        open_trades = journal[journal["exit_date"].isna()]
        if open_trades.empty:
            return

        today = datetime.now(timezone.utc).date()
        open_positions = self.get_open_symbols()

        for _, row in open_trades.iterrows():
            symbol = row["symbol"]
            entry_date = pd.to_datetime(row["entry_date"]).date()
            days_open = (today - entry_date).days

            if days_open >= config.TIME_STOP_DAYS and symbol in open_positions:
                try:
                    self.client.close_position(symbol)
                    logger.info(f"TIME STOP: Closed {symbol} after {days_open} days")
                except Exception as e:
                    logger.error(f"Failed to close {symbol} on time stop: {e}")
