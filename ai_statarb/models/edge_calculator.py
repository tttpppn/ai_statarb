# Ed Thorp's Mathematical Edge Testing
#
# Core principle: "Only place a bet if expected value is positive."
# Before trading any pair, we validate that it has a mathematical edge.

import numpy as np
from typing import Tuple

class EdgeCalculator:
    """
    Calculate and validate trading edge for pairs.

    A trade has an "edge" if:
    1. Win rate > 50%
    2. Average win > Average loss
    3. Expected value > 0
    """

    @staticmethod
    def calculate_expected_value(win_rate: float, avg_win: float, avg_loss: float) -> float:
        """
        Calculate expected value of a trade.

        EV = (win_rate × avg_win) - ((1 - win_rate) × avg_loss)

        Returns:
            Expected value in dollars
        """
        ev = (win_rate * avg_win) - ((1 - win_rate) * avg_loss)
        return ev

    @staticmethod
    def calculate_win_rate(num_wins: int, num_trades: int) -> float:
        """Calculate win rate from historical trades."""
        if num_trades <= 0:
            return 0.0
        return num_wins / num_trades

    @staticmethod
    def validate_edge(win_rate: float, avg_win: float, avg_loss: float,
                     min_win_rate: float = 0.50,
                     min_ev_ratio: float = 0.02) -> Tuple[bool, str, float]:
        """
        Validate that a trade has sufficient edge.

        Args:
            win_rate: Probability of winning
            avg_win: Average profit when winning
            avg_loss: Average loss when losing
            min_win_rate: Minimum win rate threshold (default 50%)
            min_ev_ratio: Minimum EV as % of position size

        Returns:
            (is_valid, reason, expected_value)
        """
        ev = EdgeCalculator.calculate_expected_value(win_rate, avg_win, avg_loss)
        total_stake = avg_win + avg_loss
        ev_ratio = ev / total_stake if total_stake > 0 else 0

        # Check 1: Win rate must be > 50%
        if win_rate < min_win_rate:
            return False, f"Win rate {win_rate:.1%} < {min_win_rate:.1%}", ev

        # Check 2: Expected value must be positive
        if ev <= 0:
            return False, f"Negative EV: ${ev:.2f}", ev

        # Check 3: EV ratio must be > min_ev_ratio (2% default)
        if ev_ratio < min_ev_ratio:
            return False, f"EV ratio {ev_ratio:.1%} < {min_ev_ratio:.1%}", ev

        return True, "Valid edge", ev

    @staticmethod
    def estimate_historical_edge(prices: np.ndarray, holding_period: int = 30,
                                entry_threshold: float = 1.5) -> Tuple[float, float, float, int]:
        """
        Backtest a mean-reversion pair trade to estimate edge.

        Simulates: Long when price is 1.5σ below mean, short when 1.5σ above mean.
        Exit after holding_period days or on mean reversion (±0.2σ).

        Args:
            prices: Array of historical prices
            holding_period: Days to hold trade
            entry_threshold: Entry when deviation > entry_threshold σ

        Returns:
            (win_rate, avg_win_pct, avg_loss_pct, num_trades)
        """
        if len(prices) < holding_period * 2:
            return 0.0, 0.0, 0.0, 0

        window = 252  # 1-year lookback for mean/std
        trades = []

        for i in range(window, len(prices) - holding_period):
            # Calculate rolling mean and std
            recent_prices = prices[i-window:i]
            mean = np.mean(recent_prices)
            std = np.std(recent_prices)

            if std <= 0:
                continue

            # Calculate deviation
            deviation = (prices[i] - mean) / std

            # Entry signal: price deviates > 1.5σ
            if abs(deviation) < entry_threshold:
                continue

            # Direction: mean-reversion (bet price will return to mean)
            entry_price = prices[i]
            is_long = deviation < 0  # Long if below mean

            # Exit conditions
            exit_price = entry_price
            exit_day = i

            for j in range(i + 1, min(i + holding_period, len(prices))):
                current_price = prices[j]
                current_dev = (current_price - mean) / std

                # Exit 1: Mean reversion (within 0.2σ of mean)
                if abs(current_dev) < 0.2:
                    exit_price = current_price
                    exit_day = j
                    break

                # Exit 2: Stop loss (5% move in wrong direction)
                if is_long and current_price < entry_price * 0.95:
                    exit_price = entry_price * 0.95
                    exit_day = j
                    break
                if not is_long and current_price > entry_price * 1.05:
                    exit_price = entry_price * 1.05
                    exit_day = j
                    break

            # Calculate P&L
            pnl_pct = (exit_price - entry_price) / entry_price if is_long else (entry_price - exit_price) / entry_price
            trades.append(pnl_pct)

        if not trades:
            return 0.0, 0.0, 0.0, 0

        # Calculate statistics
        wins = [t for t in trades if t > 0.001]  # Minimum 0.1% profit
        losses = [t for t in trades if t <= 0.001]

        win_rate = len(wins) / len(trades) if trades else 0.0
        avg_win = np.mean(wins) if wins else 0.0
        avg_loss = abs(np.mean(losses)) if losses else 0.0  # Take absolute value

        return win_rate, avg_win, avg_loss, len(trades)


class PairsEdgeAnalyzer:
    """Analyze edge for stock pairs."""

    def __init__(self, min_win_rate: float = 0.50, min_ev_ratio: float = 0.02):
        """
        Args:
            min_win_rate: Minimum required win rate
            min_ev_ratio: Minimum required EV as fraction of stake
        """
        self.min_win_rate = min_win_rate
        self.min_ev_ratio = min_ev_ratio
        self.edge_calc = EdgeCalculator()

    def analyze_pair_edge(self, stock_a_prices: np.ndarray, stock_b_prices: np.ndarray,
                         holding_period: int = 30) -> dict:
        """
        Analyze edge for a stock pair.

        Args:
            stock_a_prices: Historical prices for stock A
            stock_b_prices: Historical prices for stock B
            holding_period: Expected holding period

        Returns:
            {
                'is_tradeable': bool,
                'win_rate': float,
                'avg_win': float,
                'avg_loss': float,
                'expected_value': float,
                'info': str,
                'num_historical_trades': int
            }
        """
        # Compute price ratio
        with np.errstate(divide='ignore', invalid='ignore'):
            ratio = stock_a_prices / stock_b_prices
            ratio = ratio[np.isfinite(ratio)]

        if len(ratio) < 252:
            return {
                'is_tradeable': False,
                'info': 'Insufficient historical data',
                'num_historical_trades': 0
            }

        # Estimate edge from historical ratio
        win_rate, avg_win, avg_loss, num_trades = self.edge_calc.estimate_historical_edge(
            ratio, holding_period=holding_period
        )

        # Validate
        is_valid, reason, ev = self.edge_calc.validate_edge(
            win_rate, avg_win, avg_loss,
            self.min_win_rate, self.min_ev_ratio
        )

        return {
            'is_tradeable': is_valid,
            'win_rate': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'expected_value': ev,
            'info': reason,
            'num_historical_trades': num_trades
        }
