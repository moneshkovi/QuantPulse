"""Base signal dataclass shared across all strategies."""
from dataclasses import dataclass


@dataclass
class Signal:
    symbol: str
    strategy: str
    entry_price: float
    stop_price: float
    target_price: float
    score: float        # higher = stronger signal, used for ranking top 5
    atr: float
    qty: int

    @property
    def risk_per_share(self) -> float:
        return self.entry_price - self.stop_price

    @property
    def reward_per_share(self) -> float:
        return self.target_price - self.entry_price

    @property
    def risk_reward(self) -> float:
        if self.risk_per_share <= 0:
            return 0
        return self.reward_per_share / self.risk_per_share
