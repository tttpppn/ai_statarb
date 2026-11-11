# Real Market Data Fetcher
# Integrates with Alpha Vantage, Polygon.io, and FMP for live stock data

import requests
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from pathlib import Path
import pickle

logger = logging.getLogger(__name__)

CACHE_DIR = Path(__file__).parent / '.cache'
CACHE_DIR.mkdir(exist_ok=True)

class DataFetcher:
    """Fetches real stock market data from multiple sources."""

    def __init__(self, alpha_vantage_key: str = "", polygon_key: str = "", fmp_key: str = ""):
        """Initialize data fetcher with API keys."""
        self.av_key = alpha_vantage_key or self._get_env_key('ALPHA_VANTAGE_KEY')
        self.polygon_key = polygon_key or self._get_env_key('POLYGON_KEY')
        self.fmp_key = fmp_key or self._get_env_key('FMP_KEY')
        self.cache_ttl_hours = 24
        logger.info("Initialized DataFetcher")

    @staticmethod
    def _get_env_key(key_name: str) -> str:
        """Get API key from environment."""
        import os
        return os.getenv(key_name, "")

    def _get_cached_data(self, cache_key: str) -> Dict:
        """Get data from local cache if fresh."""
        cache_file = CACHE_DIR / f"{cache_key}.pkl"

        if not cache_file.exists():
            return None

        try:
            with open(cache_file, 'rb') as f:
                cached = pickle.load(f)

            if datetime.now() - cached['timestamp'] < timedelta(hours=self.cache_ttl_hours):
                logger.info(f"Using cached data for {cache_key}")
                return cached['data']
        except Exception as e:
            logger.warning(f"Cache read failed: {e}")

        return None

    def _set_cached_data(self, cache_key: str, data: Dict) -> None:
        """Store data in local cache."""
        cache_file = CACHE_DIR / f"{cache_key}.pkl"

        try:
            cached = {'timestamp': datetime.now(), 'data': data}
            with open(cache_file, 'wb') as f:
                pickle.dump(cached, f)
        except Exception as e:
            logger.warning(f"Cache write failed: {e}")

    def fetch_stock_data(self, ticker: str) -> Dict:
        """Fetch comprehensive stock data (price + fundamentals)."""
        cached = self._get_cached_data(f"stock_{ticker}")
        if cached:
            return cached

        logger.info(f"Fetching live data for {ticker}...")

        # Try yfinance first (free, no keys needed - best for backtesting)
        data = self._fetch_from_yfinance(ticker)
        if data:
            self._set_cached_data(f"stock_{ticker}", data)
            return data

        # Try FMP (best for fundamentals, needs key)
        data = self._fetch_from_fmp(ticker)
        if data:
            self._set_cached_data(f"stock_{ticker}", data)
            return data

        # Fallback to Alpha Vantage
        data = self._fetch_from_alpha_vantage(ticker)
        if data:
            self._set_cached_data(f"stock_{ticker}", data)
            return data

        # Fallback to Polygon
        data = self._fetch_from_polygon(ticker)
        if data:
            self._set_cached_data(f"stock_{ticker}", data)
            return data

        logger.error(f"Could not fetch data for {ticker}")
        return None

    def _fetch_from_yfinance(self, ticker: str) -> Dict:
        """Fetch from Yahoo Finance (yfinance) - free, no keys needed."""
        try:
            import yfinance as yf
        except ImportError:
            logger.warning("yfinance not installed. Install with: pip install yfinance")
            return None

        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="90d")

            if hist.empty:
                logger.warning(f"No yfinance data for {ticker}")
                return None

            current_price = float(hist['Close'].iloc[-1])

            if current_price <= 0:
                return None

            # Calculate 30-day volatility
            prices = hist['Close'].tail(30).values
            returns = [(prices[i] - prices[i+1]) / prices[i+1] for i in range(len(prices)-1)]
            volatility = (sum(r**2 for r in returns) / len(returns)) ** 0.5 if returns else 0.3

            # Get info
            info = stock.info or {}

            return {
                'ticker': ticker,
                'price': current_price,
                'earnings': float(info.get('trailingEps', 1)) or 1.0,
                'earnings_growth': float(info.get('earningsGrowth', 15)) or 15.0,
                'volatility': volatility,
                'beta': float(info.get('beta', 1.0)) or 1.0,
                'sector': info.get('sector', 'Technology'),
                'pe_ratio': float(info.get('trailingPE', 25)) or 25.0,
                'source': 'yfinance'
            }

        except Exception as e:
            logger.warning(f"yfinance error for {ticker}: {e}")
            return None

    def _fetch_from_alpha_vantage(self, ticker: str) -> Dict:
        """Fetch from Alpha Vantage API (free tier)."""
        if not self.av_key:
            return None

        try:
            url = "https://www.alphavantage.co/query"
            params = {
                'function': 'TIME_SERIES_DAILY',
                'symbol': ticker,
                'apikey': self.av_key,
                'outputsize': 'full'
            }

            response = requests.get(url, params=params, timeout=5)
            if response.status_code != 200:
                return None

            data = response.json()

            if 'Time Series (Daily)' not in data:
                logger.warning(f"No data for {ticker}")
                return None

            time_series = data['Time Series (Daily)']
            latest_date = list(time_series.keys())[0]
            latest = time_series[latest_date]

            current_price = float(latest['4. close'])

            # Calculate 30-day volatility
            prices = [float(time_series[d]['4. close']) for d in list(time_series.keys())[:30]]
            returns = [(prices[i] - prices[i+1]) / prices[i+1] for i in range(len(prices)-1)]
            volatility = (sum(r**2 for r in returns) / len(returns)) ** 0.5 if returns else 0.3

            # Get company info
            company_url = "https://www.alphavantage.co/query"
            company_params = {
                'function': 'OVERVIEW',
                'symbol': ticker,
                'apikey': self.av_key
            }
            company_response = requests.get(company_url, params=company_params, timeout=5)
            company_data = company_response.json()

            return {
                'ticker': ticker,
                'price': current_price,
                'earnings': float(company_data.get('EPS', 1)) or 1.0,
                'earnings_growth': float(company_data.get('RevenueShrinkageRateTTM', 10)) or 10.0,
                'volatility': volatility,
                'beta': float(company_data.get('Beta', 1.0)) or 1.0,
                'sector': company_data.get('Sector', 'Technology'),
                'pe_ratio': float(company_data.get('TrailingPE', 25)) or 25.0,
                'source': 'Alpha Vantage'
            }

        except Exception as e:
            logger.warning(f"Alpha Vantage error: {e}")
            return None

    def _fetch_from_fmp(self, ticker: str) -> Dict:
        """Fetch from Financial Modeling Prep API."""
        if not self.fmp_key:
            return None

        try:
            quote_url = f"https://financialmodelingprep.com/api/v3/quote/{ticker}"
            quote_params = {'apikey': self.fmp_key}
            quote_response = requests.get(quote_url, params=quote_params, timeout=5)

            if quote_response.status_code != 200:
                return None

            quote_data = quote_response.json()
            if not quote_data:
                return None

            quote = quote_data[0]
            current_price = float(quote.get('price', 0))

            if current_price <= 0:
                return None

            # Get historical volatility
            hist_url = f"https://financialmodelingprep.com/api/v3/historical-price-full/{ticker}"
            hist_params = {**quote_params, 'serietype': 'line', 'timeseries': 30}
            hist_response = requests.get(hist_url, params=hist_params, timeout=5)
            hist_data = hist_response.json()

            volatility = 0.3
            if 'historical' in hist_data and hist_data['historical']:
                prices = [float(d['close']) for d in hist_data['historical'][:30]]
                returns = [(prices[i] - prices[i+1]) / prices[i+1] for i in range(len(prices)-1)]
                volatility = (sum(r**2 for r in returns) / len(returns)) ** 0.5 if returns else 0.3

            return {
                'ticker': ticker,
                'price': current_price,
                'earnings': float(quote.get('eps', 1)) or 1.0,
                'earnings_growth': 15.0,
                'volatility': volatility,
                'beta': float(quote.get('beta', 1.0)) or 1.0,
                'sector': quote.get('sector', 'Technology'),
                'pe_ratio': float(quote.get('pe', 25)) or 25.0,
                'source': 'FMP'
            }

        except Exception as e:
            logger.warning(f"FMP error: {e}")
            return None

    def _fetch_from_polygon(self, ticker: str) -> Dict:
        """Fetch from Polygon.io API."""
        if not self.polygon_key:
            return None

        try:
            quote_url = f"https://api.polygon.io/v3/quotes/{ticker}/latest"
            quote_params = {'apikey': self.polygon_key}
            quote_response = requests.get(quote_url, params=quote_params, timeout=5)

            if quote_response.status_code != 200:
                return None

            quote_data = quote_response.json()
            if 'results' not in quote_data:
                return None

            quote = quote_data['results']
            current_price = float(quote.get('c', 0))

            if current_price <= 0:
                return None

            # Get daily bars for volatility
            bars_url = f"https://api.polygon.io/v2/aggs/ticker/{ticker}/range/1/day"
            bars_params = {
                **quote_params,
                'from': (datetime.now() - timedelta(days=60)).strftime('%Y-%m-%d'),
                'to': datetime.now().strftime('%Y-%m-%d')
            }
            bars_response = requests.get(bars_url, params=bars_params, timeout=5)

            volatility = 0.35
            if bars_response.status_code == 200:
                bars_data = bars_response.json()
                if 'results' in bars_data and len(bars_data['results']) > 1:
                    prices = [float(d['c']) for d in bars_data['results'][:30]]
                    returns = [(prices[i] - prices[i+1]) / prices[i+1] for i in range(len(prices)-1)]
                    volatility = (sum(r**2 for r in returns) / len(returns)) ** 0.5 if returns else 0.35

            return {
                'ticker': ticker,
                'price': current_price,
                'earnings': current_price / 25,
                'earnings_growth': 12.0,
                'volatility': volatility,
                'beta': 1.0,
                'sector': 'Technology',
                'pe_ratio': 25.0,
                'source': 'Polygon'
            }

        except Exception as e:
            logger.warning(f"Polygon error: {e}")
            return None

    def fetch_multiple(self, tickers: List[str]) -> Dict[str, Dict]:
        """Fetch data for multiple tickers."""
        results = {}

        for ticker in tickers:
            data = self.fetch_stock_data(ticker)
            if data:
                results[ticker] = data
            else:
                logger.warning(f"Failed to fetch: {ticker}")

        return results

    def fetch_batch_with_fallback(self, tickers: List[str], fallback_data: Dict = None) -> Dict:
        """Fetch real data, fallback to sample if API fails."""
        results = {}
        failed = []

        for ticker in tickers:
            data = self.fetch_stock_data(ticker)
            if data:
                results[ticker] = data
            else:
                failed.append(ticker)

        if failed and fallback_data:
            logger.warning(f"Using fallback for {len(failed)} tickers")
            for ticker in failed:
                if ticker in fallback_data:
                    results[ticker] = fallback_data[ticker]

        logger.info(f"Fetched {len(results)}/{len(tickers)} tickers")
        return results
