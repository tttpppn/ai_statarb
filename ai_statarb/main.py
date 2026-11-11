#!/usr/bin/env python3
"""
Ed Thorp Statistical Arbitrage Agent for AI4Trade
===================================================

Main entry point. This script:
1. Fetches daily stock data
2. Screens for overvalued/undervalued AI stocks
3. Constructs market-neutral pairs
4. Publishes signals to AI4Trade
5. Monitors positions and rebalances

Usage:
    python main.py --mode backtest           # Run 3-year backtest
    python main.py --mode paper-trade        # Paper trade (simulation)
    python main.py --mode live               # Live trading on AI4Trade
    python main.py --mode daily              # One-day screening
"""

import argparse
import json
import logging
from datetime import datetime

import sys
from pathlib import Path

# Add ai_statarb directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

import config.thorp_params as thorp_params
import config.stocks_universe as stocks_universe
from models.thorp_warrant import ThorpWarrantModel, create_valuation_snapshot
from sizing.kelly import KellyCriterion, PortfolioKellySizing, TradeStatistics
from data.data_fetcher import DataFetcher, setup_data_fetcher
from integrations.ai4trade_publisher import AI4TradePublisher

# Setup logging
logging.basicConfig(
    level=getattr(logging, thorp_params.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ThorpStatArbAgent:
    """
    Main statistical arbitrage agent implementing Ed Thorp's principles.
    """

    def __init__(self, mode='paper-trade'):
        """
        Initialize the agent.

        Args:
            mode: 'backtest', 'paper-trade', 'live', or 'daily'
        """
        self.mode = mode
        self.capital = thorp_params.STARTING_CAPITAL
        self.positions = {}  # Active positions
        self.trade_history = []  # All trades for backtesting
        self.warrant_model = ThorpWarrantModel(risk_free_rate=0.04)
        self.kelly_sizer = PortfolioKellySizing(
            self.capital,
            kelly_fraction=thorp_params.MIN_KELLY_FRACTION,
            max_leverage=thorp_params.MAX_LEVERAGE
        )
        self.publisher = AI4TradePublisher() if mode in ['live', 'paper-trade'] else None

        logger.info(f"Initialized StatArb Agent - Mode: {mode}")
        logger.info(f"Starting Capital: ${self.capital:,.0f}")
        logger.info(f"Max Leverage: {thorp_params.MAX_LEVERAGE}x")
        logger.info(f"Max Drawdown: {thorp_params.MAX_DRAWDOWN_PERCENT:.1%}")
        if self.publisher and thorp_params.AI4TRADE_API_TOKEN:
            logger.info(f"AI4Trade Publishing: Enabled")

    def screen_universe(self, stock_data: dict) -> dict:
        """
        Screen the stock universe and identify overvalued/undervalued stocks.

        Args:
            stock_data: {ticker: {'price', 'earnings', 'growth', 'volatility', 'beta', ...}}

        Returns:
            {
                'overvalued': [{'ticker': ..., 'score': ...}, ...],  # Top 10
                'undervalued': [...],  # Top 10
                'screening_date': date
            }
        """
        logger.info(f"Screening {len(stock_data)} stocks...")

        # Group stocks by sector
        stocks_by_sector = {}
        valuations = {}

        for ticker, data in stock_data.items():
            sector = data['sector']
            if sector not in stocks_by_sector:
                stocks_by_sector[sector] = []
            stocks_by_sector[sector].append(data)

            # Create valuation snapshot
            valuation = create_valuation_snapshot(
                ticker=ticker,
                price=data['price'],
                earnings=data['earnings'],
                growth=data['earnings_growth'],
                volatility=data['volatility'],
                beta=data['beta'],
                sector=sector
            )
            valuations[ticker] = valuation

        # Score each stock against sector peers
        scores = {}
        for ticker, valuation in valuations.items():
            sector = valuation.sector
            sector_peers = [valuations[t] for t in stocks_by_sector[sector] if t != ticker]

            score = self.warrant_model.compute_valuation_score(valuation, sector_peers)
            scores[ticker] = {
                'score': score,
                'valuation': valuation,
                'pe': valuation.pe_ratio,
                'peg': valuation.peg_ratio
            }

        # Sort by score: positive = overvalued, negative = undervalued
        sorted_scores = sorted(scores.items(), key=lambda x: x[1]['score'], reverse=True)

        overvalued = sorted_scores[:10]  # Top 10 most overvalued
        undervalued = sorted_scores[-10:]  # Bottom 10 (most undervalued)

        result = {
            'screening_date': datetime.now().isoformat(),
            'overvalued': [
                {
                    'ticker': t,
                    'score': s['score'],
                    'pe': s['pe'],
                    'peg': s['peg'],
                    'price': s['valuation'].price
                }
                for t, s in overvalued
            ],
            'undervalued': [
                {
                    'ticker': t,
                    'score': s['score'],
                    'pe': s['pe'],
                    'peg': s['peg'],
                    'price': s['valuation'].price
                }
                for t, s in undervalued
            ],
            'all_scores': {t: s['score'] for t, s in sorted_scores}
        }

        logger.info(f"Top 10 Overvalued: {[t for t, _ in overvalued]}")
        logger.info(f"Top 10 Undervalued: {[t for t, _ in undervalued]}")

        return result

    def construct_pairs(self, overvalued: list, undervalued: list, all_valuations: dict) -> list:
        """
        Construct hedged pairs from overvalued/undervalued stocks.

        Args:
            overvalued: List of overvalued stocks
            undervalued: List of undervalued stocks
            all_valuations: All stock valuations

        Returns:
            List of pairs: [{'long': ticker, 'short': ticker, ...}, ...]
        """
        logger.info(f"Constructing pairs from {len(overvalued)} overvalued, {len(undervalued)} undervalued...")

        # For simplicity: pair each undervalued stock with an overvalued one
        # In production: use correlation analysis, cross-sector matching, etc.
        pairs = []

        for i, under in enumerate(undervalued[:10]):
            over = overvalued[i] if i < len(overvalued) else overvalued[0]

            long_val = all_valuations.get(under['ticker'])
            short_val = all_valuations.get(over['ticker'])

            if not long_val or not short_val:
                continue

            # Compute hedge ratio (Thorp's delta)
            hedge_ratio = short_val.beta / long_val.beta if long_val.beta > 0 else 1.0

            pair = {
                'long_ticker': under['ticker'],
                'short_ticker': over['ticker'],
                'long_price': long_val.price,
                'short_price': short_val.price,
                'hedge_ratio': hedge_ratio,
                'long_beta': long_val.beta,
                'short_beta': short_val.beta,
                'mispricing': self.warrant_model.compute_pair_mispricing(long_val, short_val)
            }
            pairs.append(pair)

        logger.info(f"Constructed {len(pairs)} pairs")
        return pairs

    def daily_screening(self, stock_data: dict) -> dict:
        """Run daily screening and return trading signals."""
        logger.info("=" * 80)
        logger.info(f"DAILY SCREENING - {datetime.now()}")
        logger.info("=" * 80)

        # Screen the universe
        screening_result = self.screen_universe(stock_data)

        # Build valuation dict for pair construction
        valuations = {}
        for ticker in stock_data.keys():
            data = stock_data[ticker]
            valuation = create_valuation_snapshot(
                ticker, data['price'], data['earnings'],
                data['earnings_growth'], data['volatility'],
                data['beta'], data['sector']
            )
            valuations[ticker] = valuation

        # Construct pairs
        pairs = self.construct_pairs(
            screening_result['overvalued'],
            screening_result['undervalued'],
            valuations
        )

        # Prepare signals
        signals = {
            'agent_id': thorp_params.AI4TRADE_AGENT_ID,
            'signal_date': datetime.now().isoformat(),
            'screening': screening_result,
            'pairs': pairs,
            'mode': self.mode
        }

        return signals

    def run_daily(self, stock_data: dict) -> None:
        """Run a single day of screening."""
        signals = self.daily_screening(stock_data)

        # Print summary
        print("\n" + "=" * 80)
        print("TRADING SIGNALS")
        print("=" * 80)
        print(json.dumps(signals, indent=2, default=str))
        print("=" * 80)

        # Publish to AI4Trade if enabled
        if self.publisher and self.mode in ['live', 'paper-trade']:
            logger.info("\nPublishing signals to AI4Trade...")
            screening_result = {
                'pairs': signals.get('pairs', []),
                'overvalued': signals.get('screening', {}).get('overvalued', []),
                'undervalued': signals.get('screening', {}).get('undervalued', [])
            }
            publish_result = self.publisher.publish_screening_signals(screening_result)
            logger.info(f"Published: {publish_result['published']} signals, "
                       f"Pairs: {publish_result['pairs_published']}, "
                       f"Failed: {publish_result['failed']}")

        logger.info("Daily screening complete")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Ed Thorp Statistical Arbitrage Agent')
    parser.add_argument('--mode', choices=['backtest', 'paper-trade', 'live', 'daily'],
                       default='daily', help='Execution mode')
    parser.add_argument('--sample-data', action='store_true',
                       help='Use sample data (for testing)')
    parser.add_argument('--real-data', action='store_true',
                       help='Fetch real market data from APIs')

    args = parser.parse_args()

    # Initialize agent
    agent = ThorpStatArbAgent(mode=args.mode)

    # Load data
    if args.real_data:
        logger.info("Fetching real market data...")
        fetcher = setup_data_fetcher(use_api_keys=True)
        tickers = stocks_universe.get_all_tickers()
        sample_fallback = create_sample_stock_data()
        stock_data = fetcher.fetch_batch_with_fallback(tickers, sample_fallback)
    else:
        stock_data = create_sample_stock_data()

    # Run in specified mode
    if args.mode == 'daily':
        agent.run_daily(stock_data)
    elif args.mode == 'paper-trade':
        logger.info("Paper trading mode - not yet implemented")
    elif args.mode == 'backtest':
        logger.info("Backtesting mode - not yet implemented")
    elif args.mode == 'live':
        logger.info("Live trading mode - not yet implemented")


def create_sample_stock_data() -> dict:
    """Create sample stock data for testing."""
    import random

    tickers = stocks_universe.get_all_tickers()
    stock_data = {}

    for ticker in tickers[:15]:  # Use first 15 for demo
        stock_data[ticker] = {
            'ticker': ticker,
            'price': random.uniform(50, 500),
            'earnings': random.uniform(1, 50),
            'earnings_growth': random.uniform(5, 100),
            'volatility': random.uniform(0.2, 0.6),
            'beta': random.uniform(0.8, 2.5),
            'sector': stocks_universe.get_stock(ticker)['sector']
        }

    return stock_data


if __name__ == '__main__':
    main()
