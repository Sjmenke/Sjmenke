"""
Data fetcher module for TQQQ Market Regime Detection Framework.
Fetches market data using yfinance.
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict
import logging
import time

logger = logging.getLogger(__name__)


class DataFetcher:
    """Fetches market data from Yahoo Finance."""

    def __init__(self, rate_limit_delay: float = 0.5):
        """
        Initialize data fetcher.

        Args:
            rate_limit_delay: Delay between API calls to respect rate limits (seconds)
        """
        self.rate_limit_delay = rate_limit_delay

    def fetch_ticker_data(
        self,
        ticker: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        period: str = "1y"
    ) -> pd.DataFrame:
        """
        Fetch OHLCV data for a ticker.

        Args:
            ticker: Stock ticker symbol (e.g., 'QQQ', 'SPY', '^VIX')
            start_date: Start date for historical data
            end_date: End date for historical data
            period: Period string if start_date not provided ('1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max')

        Returns:
            DataFrame with OHLCV data indexed by date
        """
        try:
            logger.info(f"Fetching data for {ticker}")

            # Create ticker object
            ticker_obj = yf.Ticker(ticker)

            # Fetch historical data
            if start_date and end_date:
                df = ticker_obj.history(start=start_date, end=end_date)
            elif start_date:
                df = ticker_obj.history(start=start_date)
            else:
                df = ticker_obj.history(period=period)

            if df.empty:
                logger.warning(f"No data retrieved for {ticker}")
                return pd.DataFrame()

            # Standardize column names
            df.columns = [col.lower().replace(' ', '_') for col in df.columns]

            # Remove timezone info from index
            if df.index.tz is not None:
                df.index = df.index.tz_localize(None)

            logger.info(f"Successfully fetched {len(df)} rows for {ticker}")

            # Rate limiting
            time.sleep(self.rate_limit_delay)

            return df

        except Exception as e:
            logger.error(f"Failed to fetch data for {ticker}: {e}")
            return pd.DataFrame()

    def fetch_multiple_tickers(
        self,
        tickers: List[str],
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        period: str = "1y"
    ) -> Dict[str, pd.DataFrame]:
        """
        Fetch data for multiple tickers.

        Args:
            tickers: List of ticker symbols
            start_date: Start date for historical data
            end_date: End date for historical data
            period: Period string if start_date not provided

        Returns:
            Dictionary mapping ticker to DataFrame
        """
        results = {}

        for ticker in tickers:
            df = self.fetch_ticker_data(ticker, start_date, end_date, period)
            if not df.empty:
                results[ticker] = df
            else:
                logger.warning(f"Skipping {ticker} - no data retrieved")

        logger.info(f"Fetched data for {len(results)}/{len(tickers)} tickers")
        return results

    def get_latest_price(self, ticker: str) -> Optional[float]:
        """
        Get the most recent closing price for a ticker.

        Args:
            ticker: Stock ticker symbol

        Returns:
            Latest closing price or None if unavailable
        """
        try:
            ticker_obj = yf.Ticker(ticker)
            hist = ticker_obj.history(period="1d")

            if not hist.empty:
                return float(hist['Close'].iloc[-1])

            logger.warning(f"No recent price data for {ticker}")
            return None

        except Exception as e:
            logger.error(f"Failed to get latest price for {ticker}: {e}")
            return None

    def get_ticker_info(self, ticker: str) -> Dict:
        """
        Get ticker information and metadata.

        Args:
            ticker: Stock ticker symbol

        Returns:
            Dictionary with ticker information
        """
        try:
            ticker_obj = yf.Ticker(ticker)
            info = ticker_obj.info
            time.sleep(self.rate_limit_delay)
            return info

        except Exception as e:
            logger.error(f"Failed to get info for {ticker}: {e}")
            return {}

    def fetch_intraday_data(
        self,
        ticker: str,
        interval: str = "1m",
        period: str = "1d"
    ) -> pd.DataFrame:
        """
        Fetch intraday data for a ticker.

        Args:
            ticker: Stock ticker symbol
            interval: Data interval ('1m', '2m', '5m', '15m', '30m', '60m', '90m', '1h')
            period: Period to fetch ('1d', '5d', '1mo')

        Returns:
            DataFrame with intraday OHLCV data
        """
        try:
            logger.info(f"Fetching intraday data for {ticker} ({interval}, {period})")

            ticker_obj = yf.Ticker(ticker)
            df = ticker_obj.history(period=period, interval=interval)

            if df.empty:
                logger.warning(f"No intraday data retrieved for {ticker}")
                return pd.DataFrame()

            # Standardize column names
            df.columns = [col.lower().replace(' ', '_') for col in df.columns]

            # Remove timezone info
            if df.index.tz is not None:
                df.index = df.index.tz_localize(None)

            logger.info(f"Successfully fetched {len(df)} intraday rows for {ticker}")
            time.sleep(self.rate_limit_delay)

            return df

        except Exception as e:
            logger.error(f"Failed to fetch intraday data for {ticker}: {e}")
            return pd.DataFrame()


class IncrementalDataFetcher(DataFetcher):
    """
    Fetcher optimized for incremental updates.
    Only fetches data since the last known date.
    """

    def fetch_since_last_update(
        self,
        ticker: str,
        last_date: Optional[date] = None,
        buffer_days: int = 5
    ) -> pd.DataFrame:
        """
        Fetch data since the last update with a buffer for corrections.

        Args:
            ticker: Stock ticker symbol
            last_date: Last date we have data for
            buffer_days: Number of days to overlap for data corrections

        Returns:
            DataFrame with new/updated data
        """
        if last_date is None:
            # If no last date, fetch 1 year of data
            return self.fetch_ticker_data(ticker, period="1y")

        # Start fetching from buffer_days before last_date to catch corrections
        start_date = last_date - timedelta(days=buffer_days)
        end_date = date.today()

        logger.info(f"Fetching incremental data for {ticker} from {start_date} to {end_date}")

        return self.fetch_ticker_data(
            ticker,
            start_date=start_date,
            end_date=end_date
        )


def fetch_vix_data(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    period: str = "1y"
) -> pd.DataFrame:
    """
    Convenience function to fetch VIX data.

    Args:
        start_date: Start date
        end_date: End date
        period: Period string if dates not provided

    Returns:
        DataFrame with VIX data
    """
    fetcher = DataFetcher()
    return fetcher.fetch_ticker_data("^VIX", start_date, end_date, period)


def fetch_default_tickers(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    period: str = "1y"
) -> Dict[str, pd.DataFrame]:
    """
    Fetch data for default tickers used in regime detection.

    Default tickers:
    - QQQ: Nasdaq-100 ETF (main asset)
    - SPY: S&P 500 ETF (market context)
    - ^VIX: VIX volatility index
    - TLT: 20+ Year Treasury Bond ETF (risk-off proxy)
    - GLD: Gold ETF (alternative safe haven)

    Args:
        start_date: Start date
        end_date: End date
        period: Period string if dates not provided

    Returns:
        Dictionary mapping ticker to DataFrame
    """
    default_tickers = ["QQQ", "SPY", "^VIX", "TLT", "GLD"]

    fetcher = DataFetcher()
    return fetcher.fetch_multiple_tickers(
        default_tickers,
        start_date,
        end_date,
        period
    )


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)

    fetcher = DataFetcher()

    # Fetch QQQ data for last year
    qqq_data = fetcher.fetch_ticker_data("QQQ", period="1y")
    print(f"\nQQQ Data:\n{qqq_data.head()}")
    print(f"Shape: {qqq_data.shape}")

    # Fetch multiple tickers
    data = fetch_default_tickers(period="1mo")
    print(f"\nFetched {len(data)} tickers")
    for ticker, df in data.items():
        print(f"{ticker}: {len(df)} rows")
