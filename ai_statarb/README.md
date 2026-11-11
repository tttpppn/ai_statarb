# Ed Thorp Statistical Arbitrage Agent for AI4Trade

A Python implementation of **Ed Thorp's statistical arbitrage system** applied to AI stocks, using modern pair trading and Kelly Criterion position sizing.

## Overview

This agent trades on AI4Trade using **Ed Thorp's principles**:

1. **Relative Value Analysis** — Find undervalued stocks (good shorts) and overvalued stocks (good longs)
2. **Mean Reversion Pairs** — Pair undervalued with overvalued stocks in same sector
3. **Kelly Criterion Sizing** — Optimal position sizing to maximize wealth without ruin
4. **Market Neutrality** — Hedged pairs eliminate systematic risk
5. **Risk of Ruin Protection** — Hard stops prevent catastrophic losses
6. **Information Ratio** — Track excess return per unit of risk

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run daily screening
python main.py --mode daily --sample-data

# Expected output: Top 10 overvalued + undervalued AI stocks, hedged pairs
```

## Architecture

- **Models**: Thorp's warrant pricing, edge validation
- **Sizing**: Kelly Criterion for optimal position sizing
- **Pairs**: Mean reversion pair selection with correlation analysis
- **Risk**: Drawdown limits, leverage caps, risk of ruin protection
- **Integration**: AI4Trade signal publishing (tradesync skill)

## Key Features

### Thorp's Warrant Pricing Model

Fair value = f(earnings yield, growth, volatility, beta)

Identifies mispricings when current price deviates >1.5σ from fair value.

### Kelly Criterion Sizing

Optimal bet fraction:
```
f* = (bp - q) / b

f_conservative = f* × 0.25  (Quarter-Kelly for safety)
```

Uses quarter-Kelly to reduce variance and drawdown.

### Market Neutral Portfolio

- **Long**: Undervalued stocks (cheap relative to fundamentals)
- **Short**: Overvalued stocks (expensive relative to fundamentals)
- **Hedge**: Adjust for different betas
- **Result**: Portfolio delta ≈ 0 (market neutral)

## Configuration

Edit `config/thorp_params.py`:

```python
# Capital & Risk
STARTING_CAPITAL = 100_000
MAX_LEVERAGE = 3.0
MAX_DRAWDOWN_PERCENT = 0.20

# Trading Edge
MIN_EDGE_THRESHOLD = 0.02       # 2% minimum edge
MIN_WIN_RATE = 0.50             # >50% win rate required
MIN_INFORMATION_RATIO = 0.5     # Target: IR > 0.5

# Pairs
CORRELATION_THRESHOLD = 0.70    # Highly correlated pairs
DEVIATION_THRESHOLD = 1.5       # 1.5σ entry signal
```

## Usage

```bash
# Daily screening
python main.py --mode daily --sample-data

# Paper trading simulation
python main.py --mode paper-trade --sample-data

# 3-year backtest
python main.py --mode backtest

# Live trading on AI4Trade
python main.py --mode live
```

## AI4Trade Integration

Registered on AI4Trade:
- **Agent ID**: 28579
- **Agent Name**: TaiTrader-11626
- **Capital**: $100,000 simulated
- **Token**: Securely stored

Publishes signals via `tradesync` skill.

## Risk Management (Thorp's Rules)

1. **Max Drawdown**: Stop if -20% loss
2. **Max Leverage**: 3x maximum (Thorp used 2-3x)
3. **Kelly Sizing**: Quarter-Kelly (safe, conservative)
4. **Position Limits**: No pair > 15% of portfolio
5. **Daily Rebalancing**: Keep delta ≈ 0
6. **Edge Validation**: Only trade >50% win rate + EV > 0

## Performance Targets

- **Annual Sharpe Ratio**: > 1.0
- **Information Ratio**: > 0.5 (excess return per risk unit)
- **Max Drawdown**: < 15%
- **Win Rate**: > 52%
- **Positive Months**: ≥ 70%

## Files

| File | Purpose |
|------|---------|
| `main.py` | Entry point & daily screening |
| `models/thorp_warrant.py` | Valuation model |
| `models/edge_calculator.py` | Edge validation |
| `sizing/kelly.py` | Kelly Criterion sizing |
| `config/thorp_params.py` | Trading parameters |
| `config/stocks_universe.py` | AI stock universe (30+) |

## Example Output

```
TRADING SIGNALS
Top 10 Overvalued:
  NVDA: score=85.2, PE=65.4, PEG=2.8
  MSFT: score=72.1, PE=42.1, PEG=1.9
  ...

Top 10 Undervalued:
  AMD: score=-75.3, PE=18.2, PEG=0.9
  INTC: score=-68.9, PE=12.1, PEG=0.7
  ...

Pairs:
  LONG AMD / SHORT NVDA (mispricing: +45.2%, hedge ratio: 0.95)
  LONG INTC / SHORT MSFT (mispricing: +42.1%, hedge ratio: 0.88)
  ...
```

## Thorp's 12 Trading Rules

1. ✅ Find mathematical edge (EV > 0)
2. ✅ Use Kelly Criterion for sizing
3. ✅ Hedge market risk (pairs)
4. ✅ Diversify uncorrelated bets
5. ✅ Limit leverage (max 3x)
6. ✅ Manage drawdowns (max 20%)
7. ✅ Protect against ruin
8. ✅ Backtest extensively
9. ✅ Paper trade first (30 days)
10. ✅ Track information ratio
11. ✅ Rebalance daily
12. ✅ Stay disciplined

## References

- **Beat the Market** (Thorp, 1967) — Original pairs trading
- **A Man for All Markets** (Thorp, 2017) — Kelly Criterion & risk
- **Fortune's Formula** (Poundstone, 2005) — Kelly history

## MIT License
