# Ed Thorp Statistical Arbitrage Backtest Results

## Backtest Configuration
- **Strategy**: Ed Thorp Warrant Model + Kelly Criterion
- **Period**: 2023-01-01 to 2025-12-31 (3 years)
- **Universe**: 30-50 AI-focused US stocks
- **Starting Capital**: $100,000
- **Max Leverage**: 3x
- **Max Drawdown Threshold**: 20%
- **Kelly Fraction**: 0.25 (quarter-Kelly for safety)

## Test Cases

### Test 1: Daily Screening
**Status**: ⏳ Pending
**Description**: Run daily stock universe screening for one day
**Expected Output**: 
- Top 10 overvalued stocks
- Top 10 undervalued stocks
- Suggested pairs to trade

---

### Test 2: Pair Construction
**Status**: ⏳ Pending
**Description**: Construct hedged pairs from screening results
**Expected Output**:
- Pair mispricing scores
- Hedge ratios (beta-adjusted)
- Entry signals

---

### Test 3: Paper Trade Simulation
**Status**: ⏳ Not Yet Implemented
**Description**: Simulate 1 month of trading with sample data
**Expected Metrics**:
- Win rate > 50%
- Sharpe ratio > 1.0
- Max drawdown < 15%

---

### Test 4: Full 3-Year Backtest
**Status**: ⏳ Not Yet Implemented
**Description**: Run full backtest from 2023-2025
**Expected Metrics**:
- Minimum 50+ trades
- Annual Sharpe ratio > 1.0
- Max drawdown < 15%
- Win rate > 52%

---

## Performance Metrics to Track

| Metric | Target | Status |
|--------|--------|--------|
| Win Rate | > 52% | ⏳ |
| Sharpe Ratio | > 1.0 | ⏳ |
| Max Drawdown | < 15% | ⏳ |
| Information Ratio | > 0.5 | ⏳ |
| Avg Win / Avg Loss | > 1.1x | ⏳ |
| Total Trades | > 50 | ⏳ |

---

## Branch: backtest/thorp-statarb-v1
**Created**: 2026-11-10
**Purpose**: Track backtest development and results
