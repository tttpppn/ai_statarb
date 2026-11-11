# Ed Thorp's Warrant Pricing Model (Adapted for Pairs Trading)
#
# Thorp's original insight: Warrant pricing is fundamentally a relative value problem.
# We apply this principle to identify overvalued vs. undervalued stock pairs.
#
# Fair value = function of:
#   1. Earnings yield (P/E ratio)
#   2. Earnings growth rate (PEG ratio)
#   3. Volatility (Implied Volatility)
#   4. Risk-free rate

import numpy as np
from dataclasses import dataclass

@dataclass
class StockValuation:
    """Thorp's valuation metrics for a stock."""
    ticker: str
    price: float
    earnings: float
    earnings_growth: float  # YoY growth %
    volatility: float  # Implied volatility (0-1 scale)
    beta: float  # Market beta
    sector: str

    @property
    def pe_ratio(self):
        """Price-to-Earnings ratio."""
        if self.earnings <= 0:
            return 999
        return self.price / self.earnings

    @property
    def peg_ratio(self):
        """Price/Earnings-to-Growth ratio."""
        if self.earnings_growth <= 0 or self.pe_ratio <= 0:
            return 999
        return self.pe_ratio / self.earnings_growth

    @property
    def earnings_yield(self):
        """Earnings yield (inverse of P/E)."""
        if self.pe_ratio >= 999:
            return 0
        return 1 / self.pe_ratio


class ThorpWarrantModel:
    """
    Thorp's relative valuation model.

    Key principle: A stock's fair value relative to peers is determined by:
    - Fundamental quality (earnings, growth)
    - Risk (volatility, beta)
    - Market context (peer average metrics)
    """

    def __init__(self, risk_free_rate=0.04):
        """
        Args:
            risk_free_rate: Risk-free rate (default 4% = current US treasury)
        """
        self.risk_free_rate = risk_free_rate

    def compute_valuation_score(self, stock: StockValuation, sector_peers: list):
        """
        Compute Thorp's relative valuation score.

        Returns a score from -100 (deeply undervalued) to +100 (deeply overvalued).

        Score = 40% PEG deviation + 30% relative multiples + 30% risk adjustment
        """
        if not sector_peers:
            return 0.0

        # Calculate sector averages
        peer_pe_ratios = [p.pe_ratio for p in sector_peers if p.pe_ratio < 999]
        peer_peg_ratios = [p.peg_ratio for p in sector_peers if p.peg_ratio < 999]
        peer_volatilities = [p.volatility for p in sector_peers]

        if not peer_pe_ratios or not peer_peg_ratios:
            return 0.0

        peer_pe_mean = np.mean(peer_pe_ratios)
        peer_pe_std = np.std(peer_pe_ratios) or 1e-6
        peer_peg_mean = np.mean(peer_peg_ratios)
        peer_peg_std = np.std(peer_peg_ratios) or 1e-6
        peer_vol_mean = np.mean(peer_volatilities)

        # 1. PEG Ratio Deviation (40% weight)
        # PEG compares valuation to growth; this is Thorp's primary metric
        if stock.peg_ratio < 999:
            peg_zscore = (stock.peg_ratio - peer_peg_mean) / peer_peg_std
        else:
            peg_zscore = 0

        peg_score = np.tanh(peg_zscore / 2) * 50  # Normalize to -50 to +50

        # 2. Relative Multiples Deviation (30% weight)
        # Compare P/E to peers
        if stock.pe_ratio < 999:
            pe_zscore = (stock.pe_ratio - peer_pe_mean) / peer_pe_std
        else:
            pe_zscore = 0

        pe_score = np.tanh(pe_zscore / 2) * 50

        # 3. Risk Adjustment (30% weight)
        # Higher volatility should lower valuation (more risk)
        vol_zscore = (stock.volatility - peer_vol_mean) / (np.std(peer_volatilities) or 1e-6)
        vol_score = np.tanh(vol_zscore / 2) * 30  # Volatility penalty

        # Composite score (weighted average)
        total_score = (0.40 * peg_score) + (0.30 * pe_score) + (0.30 * vol_score)

        # Clamp to [-100, 100]
        total_score = np.clip(total_score, -100, 100)

        return total_score

    def compute_pair_mispricing(self, stock_a: StockValuation, stock_b: StockValuation):
        """
        Compute mispricing between two stocks in the same sector.
        This is the core Thorp pairs trading logic.

        Returns:
            mispricing_percent: How much is stock_a overvalued relative to stock_b?
                               - Positive: stock_a is overvalued (short candidate)
                               - Negative: stock_a is undervalued (long candidate)
        """
        # Fundamental value ratio (based on earnings, growth, risk)
        if stock_a.price <= 0 or stock_b.price <= 0:
            return 0

        # Earnings-based fair value ratio
        earnings_ratio_a = stock_a.earnings_yield * (1 + 0.01 * stock_a.earnings_growth)
        earnings_ratio_b = stock_b.earnings_yield * (1 + 0.01 * stock_b.earnings_growth)

        if earnings_ratio_b <= 0:
            return 0

        fair_earnings_ratio = earnings_ratio_a / earnings_ratio_b

        # Risk adjustment (volatility & beta)
        vol_adj_a = 1 + (0.05 * stock_a.volatility)
        vol_adj_b = 1 + (0.05 * stock_b.volatility)
        fair_vol_ratio = vol_adj_a / vol_adj_b

        # Fair price ratio
        fair_price_ratio = fair_earnings_ratio * fair_vol_ratio

        # Current price ratio
        current_price_ratio = stock_a.price / stock_b.price

        # Mispricing percentage
        if fair_price_ratio > 0:
            mispricing = ((current_price_ratio - fair_price_ratio) / fair_price_ratio) * 100
        else:
            mispricing = 0

        return mispricing

    def implied_volatility_estimate(self, historical_returns: np.ndarray, window=30):
        """
        Estimate implied volatility from historical returns.

        Args:
            historical_returns: Array of daily returns
            window: Window size for rolling volatility (default 30 days)

        Returns:
            Implied volatility (annualized)
        """
        if len(historical_returns) < window:
            return 0.0

        daily_vol = np.std(historical_returns[-window:])
        annualized_vol = daily_vol * np.sqrt(252)  # 252 trading days

        return annualized_vol


def create_valuation_snapshot(ticker, price, earnings, growth, volatility, beta, sector):
    """Helper to create a StockValuation object."""
    return StockValuation(
        ticker=ticker,
        price=price,
        earnings=earnings,
        earnings_growth=growth,
        volatility=volatility,
        beta=beta,
        sector=sector
    )
