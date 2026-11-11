# Ed Thorp's Kelly Criterion Implementation
#
# The Kelly Criterion is the mathematical formula for optimal bet sizing.
# It maximizes long-term wealth growth while minimizing risk of ruin.
#
# Formula: f* = (bp - q) / b
# Where:
#   f* = fraction of bankroll to bet
#   b  = odds received (payout / cost)
#   p  = probability of winning
#   q  = probability of losing (1-p)

import numpy as np
from dataclasses import dataclass
from typing import List, Tuple

@dataclass
class TradeStatistics:
    """Historical statistics for a trade/pair."""
    win_rate: float  # Probability of winning (0-1)
    avg_win: float  # Average profit when trade wins
    avg_loss: float  # Average loss when trade loses
    num_trades: int  # Number of historical trades

    @property
    def expected_value(self):
        """Expected value of one trade."""
        return (self.win_rate * self.avg_win) - ((1 - self.win_rate) * self.avg_loss)

    @property
    def odds_ratio(self):
        """Payout odds (average win / average loss)."""
        if self.avg_loss <= 0:
            return 1.0
        return self.avg_win / self.avg_loss


class KellyCriterion:
    """
    Thorp's Kelly Criterion implementation for optimal position sizing.

    Key principles:
    1. Use Kelly fraction to maximize log wealth growth
    2. Apply safety margin (half-Kelly, quarter-Kelly) to reduce variance
    3. Diversify across multiple bets (don't put all in one position)
    4. Rebalance when leverage drifts
    """

    @staticmethod
    def compute_kelly_fraction(trade_stats: TradeStatistics) -> float:
        """
        Compute Kelly Criterion fraction.

        Formula: f* = (bp - q) / b

        Where:
            b = odds ratio (avg_win / avg_loss)
            p = win rate
            q = 1 - p

        Args:
            trade_stats: Statistics of the trade

        Returns:
            Kelly fraction (0-1 scale, can be > 1 for high-confidence trades)
        """
        if trade_stats.avg_loss <= 0:
            return 0.0

        b = trade_stats.odds_ratio  # avg_win / avg_loss
        p = trade_stats.win_rate
        q = 1 - p

        # Kelly formula
        f_kelly = (b * p - q) / b

        # Ensure non-negative
        f_kelly = max(f_kelly, 0.0)

        return f_kelly

    @staticmethod
    def compute_fractional_kelly(f_kelly: float, kelly_fraction: float = 0.25) -> float:
        """
        Apply fractional Kelly for safety.

        Full Kelly is optimal mathematically but too volatile in practice.
        Use fractional Kelly (e.g., 0.25 = quarter-Kelly) for:
        - Reduced drawdowns
        - Smoother equity curves
        - Protection against estimation errors

        Args:
            f_kelly: Full Kelly fraction
            kelly_fraction: Fraction to use (0.25 = quarter-Kelly, 0.5 = half-Kelly)

        Returns:
            Conservative Kelly fraction
        """
        return f_kelly * kelly_fraction

    @staticmethod
    def compute_position_size(bankroll: float, kelly_fraction: float,
                             num_concurrent_trades: int) -> float:
        """
        Compute position size for a single trade using Kelly.

        Thorp's diversification principle: spread Kelly-sized bets across many trades.

        Args:
            bankroll: Current portfolio value
            kelly_fraction: Kelly fraction to use (e.g., 0.025 for quarter-Kelly)
            num_concurrent_trades: Number of concurrent bets

        Returns:
            Position size in dollars
        """
        if num_concurrent_trades <= 0:
            return 0.0

        # Total risk = bankroll * kelly_fraction
        # Spread across num_concurrent_trades
        position_size = (bankroll * kelly_fraction) / num_concurrent_trades

        return position_size

    @staticmethod
    def compute_leverage(position_size: float, bankroll: float) -> float:
        """
        Compute effective leverage.

        Leverage = total_position_value / bankroll

        Args:
            position_size: Size of one position
            bankroll: Total capital

        Returns:
            Leverage multiplier (e.g., 2.0 = 2x leverage)
        """
        if bankroll <= 0:
            return 0.0

        return position_size / bankroll

    @staticmethod
    def validate_kelly_parameters(trade_stats: TradeStatistics,
                                 min_win_rate: float = 0.50,
                                 min_edge: float = 0.02) -> Tuple[bool, str]:
        """
        Validate that trade has sufficient edge to trade.

        Thorp's rule: "Only place a bet if expected value is positive."

        Args:
            trade_stats: Trade statistics
            min_win_rate: Minimum win rate threshold
            min_edge: Minimum edge (as % of position)

        Returns:
            (is_valid, reason)
        """
        if trade_stats.win_rate < min_win_rate:
            return False, f"Win rate {trade_stats.win_rate:.1%} < {min_win_rate:.1%}"

        ev = trade_stats.expected_value
        if ev <= 0:
            return False, f"Expected value ${ev:.2f} <= $0"

        if ev < min_edge:
            return False, f"Edge {ev / (trade_stats.avg_win + trade_stats.avg_loss):.1%} < {min_edge:.1%}"

        return True, "Valid trade"


class PortfolioKellySizing:
    """Portfolio-level Kelly sizing for multiple concurrent pairs."""

    def __init__(self, bankroll: float, kelly_fraction: float = 0.25,
                 max_leverage: float = 3.0):
        """
        Args:
            bankroll: Total capital
            kelly_fraction: Fractional Kelly to use (0.25 = quarter-Kelly)
            max_leverage: Maximum allowed leverage (e.g., 3.0 = 3x)
        """
        self.bankroll = bankroll
        self.kelly_fraction = kelly_fraction
        self.max_leverage = max_leverage

    def compute_pair_positions(self, pairs_stats: List[TradeStatistics]) -> dict:
        """
        Compute position sizes for all pairs.

        Args:
            pairs_stats: List of TradeStatistics for each pair

        Returns:
            {pair_index: position_size}
        """
        num_pairs = len(pairs_stats)
        if num_pairs == 0:
            return {}

        kelly = KellyCriterion()
        positions = {}
        total_kelly_capital = 0

        # Compute Kelly fractions for each pair
        kelly_fractions = []
        for i, stats in enumerate(pairs_stats):
            f = kelly.compute_kelly_fraction(stats)
            f_frac = kelly.compute_fractional_kelly(f, self.kelly_fraction)
            kelly_fractions.append(f_frac)
            total_kelly_capital += f_frac * self.bankroll

        # Normalize if total exceeds max leverage
        effective_leverage = total_kelly_capital / self.bankroll
        if effective_leverage > self.max_leverage:
            scale_factor = self.max_leverage / effective_leverage
            kelly_fractions = [f * scale_factor for f in kelly_fractions]

        # Compute final positions
        for i, f in enumerate(kelly_fractions):
            position = f * self.bankroll
            positions[i] = position

        return positions

    def compute_hedge_ratio(self, long_position: float, short_stock_beta: float,
                           long_stock_beta: float) -> float:
        """
        Compute hedge ratio for a pair trade.

        Thorp's delta concept: adjust position sizes for different betas.

        Args:
            long_position: Dollar size of long leg
            short_stock_beta: Beta of short stock
            long_stock_beta: Beta of long stock

        Returns:
            Short position size in dollars
        """
        if long_stock_beta <= 0:
            return 0.0

        # Hedge ratio = beta_short / beta_long
        hedge_ratio = short_stock_beta / long_stock_beta

        short_position = long_position * hedge_ratio

        return short_position

    def get_leverage(self, total_position_value: float) -> float:
        """Get effective portfolio leverage."""
        if self.bankroll <= 0:
            return 0.0
        return total_position_value / self.bankroll
