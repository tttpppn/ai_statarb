# Ed Thorp-Based Statistical Arbitrage Configuration
# All parameters based on Thorp's principles: Risk of Ruin, Kelly Criterion, Edge Testing

import os

# ============================================================================
# PORTFOLIO & CAPITAL MANAGEMENT (Risk of Ruin Protection)
# ============================================================================

STARTING_CAPITAL = 100_000  # Starting bankroll ($100k simulated on AI4Trade)
MAX_LEVERAGE = 3.0  # Thorp recommended 2-3x max (we use 3x conservative)
MAX_DRAWDOWN_PERCENT = 0.20  # Stop trading if 20% loss (Thorp's cardinal rule)
MIN_KELLY_FRACTION = 0.25  # Use quarter-Kelly (0.25) for safety (vs full Kelly)
REBALANCE_FREQUENCY = "daily"  # Daily: keep portfolio delta ~0

# ============================================================================
# TRADING EDGE & KELLY CRITERION
# ============================================================================

MIN_EDGE_THRESHOLD = 0.02  # Only trade if EV > 2% of position
MIN_WIN_RATE = 0.50  # Must have >50% historical win rate
MIN_AVG_WIN_VS_LOSS = 1.1  # Avg win must be 1.1x avg loss (11% edge)
MIN_INFORMATION_RATIO = 0.5  # Target: IR > 0.5 (excess return per risk unit)

# ============================================================================
# PAIRS TRADING (Mean Reversion Parameters)
# ============================================================================

CORRELATION_THRESHOLD = 0.70  # Only pairs with >70% historical correlation
DEVIATION_THRESHOLD = 1.5  # Trade when price ratio deviates >1.5σ from mean
LOOKBACK_WINDOW = 252  # 1-year historical data for correlations
REVERSION_DAYS = 30  # Expected reversion within 30 days (Thorp's typical holding)

# ============================================================================
# POSITION SIZING & RISK
# ============================================================================

MAX_POSITION_PERCENT = 0.15  # No single pair > 15% of portfolio
MAX_CONCURRENT_PAIRS = 10  # Trade max 10 pairs simultaneously
RISK_PER_PAIR = STARTING_CAPITAL * MIN_KELLY_FRACTION / MAX_CONCURRENT_PAIRS

# ============================================================================
# DATA & UNIVERSE
# ============================================================================

# AI Stock Universe: 30-50 AI-focused US stocks (mix of sectors)
# Will be populated from stocks_universe.py

DATA_CACHE_DAYS = 1  # Refresh data daily
DATA_SOURCES = ["alpha_vantage", "polygon", "fmp"]  # Primary, fallback, fallback

# ============================================================================
# BACKTESTING & VALIDATION
# ============================================================================

BACKTEST_START_DATE = "2023-01-01"  # 3 years of historical data
BACKTEST_TRADES_MIN = 50  # Need at least 50 trades to validate edge
SUCCESS_ANNUAL_SHARPE = 1.0  # Target: Sharpe > 1.0
SUCCESS_MAX_DRAWDOWN = 0.15  # Target: Max DD < 15%
SUCCESS_WIN_RATE = 0.52  # Target: >52% win rate

# ============================================================================
# MONITORING & ALERTS
# ============================================================================

ALERT_PORTFOLIO_DELTA_THRESHOLD = 0.10  # Alert if delta > ±0.10
ALERT_CORRELATION_BREAKDOWN = 0.50  # Alert if correlation drops below 50%
ALERT_VOLATILITY_SPIKE = 0.03  # Alert if daily vol > 3%
DAILY_REPORT_TIME = "16:00"  # 4 PM ET (after market close)

# ============================================================================
# AI4TRADE API CONFIGURATION
# ============================================================================

AI4TRADE_API_TOKEN = os.getenv('AI4TRADE_API_TOKEN', '')
AI4TRADE_API_URL = os.getenv('AI4TRADE_API_URL', 'https://ai4trade.ai/api')
AI4TRADE_AGENT_ID = os.getenv('AI4TRADE_AGENT_ID', 'thorp-statarb-agent')

# ============================================================================
# LOGGING & AUDIT
# ============================================================================

LOG_LEVEL = "INFO"
LOG_TRADES = True  # Audit trail of all trades
LOG_POSITION_CHANGES = True
LOG_REBALANCES = True
