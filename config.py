import os
from dotenv import load_dotenv

load_dotenv()

# Alpaca credentials — loaded from .env only
ALPACA_API_KEY = os.getenv("ALPACA_API_KEY")
ALPACA_SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")
ALPACA_BASE_URL = os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets/v2")

# Risk management
RISK_PER_TRADE = 0.01          # 1% of capital per trade
MAX_POSITIONS_PER_STRATEGY = 5 # max concurrent positions per strategy
TIME_STOP_DAYS = 10            # force exit after N days

# ATR multipliers
ATR_STOP_MULTIPLIER = 1.5      # stop loss = entry - 1.5x ATR(14)
ATR_TARGET_MR = 2.0            # mean reversion take profit = entry + 2x ATR
ATR_TARGET_BREAKOUT = 3.0      # breakout take profit = entry + 3x ATR

# Universe filters
MIN_PRICE = 5.0                # exclude stocks below $5
MIN_AVG_VOLUME = 500_000       # exclude illiquid stocks

# Data
LOOKBACK_DAYS = 252            # 1 year of daily bars for signal computation
UNIVERSE_CACHE_FILE = "data/cache/universe.csv"
UNIVERSE_REFRESH_DAYS = 7      # refresh universe list weekly

# Email notifications
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_APP_PASSWORD = os.getenv("EMAIL_APP_PASSWORD")

# Strategy labels
STRATEGIES = ["mean_reversion", "momentum", "breakout"]
