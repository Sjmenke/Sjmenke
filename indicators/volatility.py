"""
Volatility indicators for TQQQ Market Regime Detection Framework.
Includes: VIX analysis, ATR, Bollinger Bands, Historical Volatility
"""

import pandas as pd
import numpy as np
from typing import Optional, Dict, Any
from .base import BaseIndicator, register_indicator
import logging

logger = logging.getLogger(__name__)


@register_indicator('vix_ma')
class VIXMovingAverage(BaseIndicator):
    """
    VIX Moving Average indicator.
    Note: VIX data itself comes from the data fetcher, this calculates its MA.

    Config parameters:
        - period: Number of periods for the moving average (default: 20)
    """

    def _validate_config(self) -> None:
        """Validate configuration."""
        period = self.config.get('period', 20)
        if not isinstance(period, int) or period < 1:
            raise ValueError(f"VIX MA period must be a positive integer, got {period}")

    def calculate(self, data: pd.DataFrame) -> pd.Series:
        """
        Calculate VIX moving average.

        Args:
            data: DataFrame with VIX close data

        Returns:
            Series with VIX MA values
        """
        if 'close' not in data.columns:
            raise ValueError("Data must contain 'close' column")

        period = self.config.get('period', 20)
        vix_ma = data['close'].rolling(window=period, min_periods=period).mean()

        return vix_ma


@register_indicator('atr')
class ATR(BaseIndicator):
    """
    Average True Range (ATR) - measures volatility.

    Config parameters:
        - period: Number of periods for ATR calculation (default: 14)
    """

    def _validate_config(self) -> None:
        """Validate ATR configuration."""
        period = self.config.get('period', 14)
        if not isinstance(period, int) or period < 1:
            raise ValueError(f"ATR period must be a positive integer, got {period}")

    def calculate(self, data: pd.DataFrame) -> pd.Series:
        """
        Calculate Average True Range.

        Args:
            data: DataFrame with OHLCV data (must have high, low, close)

        Returns:
            Series with ATR values
        """
        required_columns = ['high', 'low', 'close']
        for col in required_columns:
            if col not in data.columns:
                raise ValueError(f"Data must contain '{col}' column")

        period = self.config.get('period', 14)

        high = data['high']
        low = data['low']
        close = data['close']

        # Calculate True Range
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))

        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

        # Calculate ATR as the moving average of True Range
        atr = tr.rolling(window=period, min_periods=period).mean()

        return atr


@register_indicator('atr_percent')
class ATRPercent(BaseIndicator):
    """
    ATR as a percentage of price - normalized volatility measure.

    Config parameters:
        - period: Number of periods for ATR calculation (default: 14)
    """

    def _validate_config(self) -> None:
        """Validate configuration."""
        period = self.config.get('period', 14)
        if not isinstance(period, int) or period < 1:
            raise ValueError(f"ATR period must be a positive integer, got {period}")

    def calculate(self, data: pd.DataFrame) -> pd.Series:
        """
        Calculate ATR as percentage of price.

        Args:
            data: DataFrame with OHLCV data

        Returns:
            Series with ATR% values
        """
        atr_indicator = ATR(name='ATR_temp', config=self.config)
        atr = atr_indicator.calculate(data)

        # Calculate as percentage of closing price
        atr_percent = (atr / data['close']) * 100

        return atr_percent


@register_indicator('bollinger_bands')
class BollingerBands(BaseIndicator):
    """
    Bollinger Bands - volatility bands around a moving average.

    Returns a DataFrame with columns: middle, upper, lower, bandwidth, percent_b

    Config parameters:
        - period: Number of periods for the moving average (default: 20)
        - std_dev: Number of standard deviations for bands (default: 2)
    """

    def _validate_config(self) -> None:
        """Validate configuration."""
        period = self.config.get('period', 20)
        std_dev = self.config.get('std_dev', 2)

        if not isinstance(period, int) or period < 1:
            raise ValueError(f"Period must be a positive integer, got {period}")
        if not isinstance(std_dev, (int, float)) or std_dev <= 0:
            raise ValueError(f"Standard deviation must be positive, got {std_dev}")

    def calculate(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate Bollinger Bands.

        Args:
            data: DataFrame with OHLCV data

        Returns:
            DataFrame with columns: middle, upper, lower, bandwidth, percent_b
        """
        if 'close' not in data.columns:
            raise ValueError("Data must contain 'close' column")

        period = self.config.get('period', 20)
        std_dev = self.config.get('std_dev', 2)

        # Calculate middle band (SMA)
        middle = data['close'].rolling(window=period, min_periods=period).mean()

        # Calculate standard deviation
        std = data['close'].rolling(window=period, min_periods=period).std()

        # Calculate upper and lower bands
        upper = middle + (std * std_dev)
        lower = middle - (std * std_dev)

        # Calculate bandwidth (volatility measure)
        bandwidth = ((upper - lower) / middle) * 100

        # Calculate %B (position within bands)
        # %B = 1 means price at upper band, 0 means at lower band, 0.5 means at middle
        percent_b = (data['close'] - lower) / (upper - lower)

        result = pd.DataFrame({
            'middle': middle,
            'upper': upper,
            'lower': lower,
            'bandwidth': bandwidth,
            'percent_b': percent_b
        }, index=data.index)

        return result

    def get_latest_value(self, data: pd.DataFrame) -> Optional[float]:
        """
        Get the latest bandwidth value (primary metric).

        Args:
            data: DataFrame with OHLCV data

        Returns:
            Latest bandwidth value
        """
        result = self.calculate(data)
        if not result.empty and pd.notna(result['bandwidth'].iloc[-1]):
            return float(result['bandwidth'].iloc[-1])
        return None


@register_indicator('historical_volatility')
class HistoricalVolatility(BaseIndicator):
    """
    Historical Volatility (annualized standard deviation of returns).

    Config parameters:
        - period: Number of periods for volatility calculation (default: 20)
        - annualization_factor: Factor to annualize volatility (default: 252 for daily data)
    """

    def _validate_config(self) -> None:
        """Validate configuration."""
        period = self.config.get('period', 20)
        if not isinstance(period, int) or period < 2:
            raise ValueError(f"Period must be >= 2, got {period}")

    def calculate(self, data: pd.DataFrame) -> pd.Series:
        """
        Calculate historical volatility.

        Args:
            data: DataFrame with OHLCV data

        Returns:
            Series with annualized volatility values (in percentage)
        """
        if 'close' not in data.columns:
            raise ValueError("Data must contain 'close' column")

        period = self.config.get('period', 20)
        annualization_factor = self.config.get('annualization_factor', 252)

        # Calculate log returns
        log_returns = np.log(data['close'] / data['close'].shift(1))

        # Calculate rolling standard deviation
        volatility = log_returns.rolling(window=period, min_periods=period).std()

        # Annualize and convert to percentage
        annualized_volatility = volatility * np.sqrt(annualization_factor) * 100

        return annualized_volatility


@register_indicator('vix_level')
class VIXLevel(BaseIndicator):
    """
    Simple wrapper to get VIX level (close price).
    Used for consistency in the indicator framework.
    """

    def calculate(self, data: pd.DataFrame) -> pd.Series:
        """
        Return VIX close prices.

        Args:
            data: DataFrame with VIX data

        Returns:
            Series with VIX levels
        """
        if 'close' not in data.columns:
            raise ValueError("Data must contain 'close' column")

        return data['close']


def create_volatility_indicators(config: Dict[str, Any]) -> Dict[str, BaseIndicator]:
    """
    Create all volatility indicators from configuration.

    Args:
        config: Configuration dictionary with volatility parameters

    Returns:
        Dictionary mapping indicator names to indicator instances
    """
    indicators = {}

    # VIX MA
    if 'vix_ma_period' in config:
        indicators['VIX_MA'] = VIXMovingAverage(
            name='VIX_MA',
            config={'period': config['vix_ma_period']}
        )

    # VIX Level
    indicators['VIX_LEVEL'] = VIXLevel(name='VIX_LEVEL', config={})

    # ATR
    if 'atr_period' in config:
        indicators['ATR'] = ATR(
            name='ATR',
            config={'period': config['atr_period']}
        )
        indicators['ATR_PERCENT'] = ATRPercent(
            name='ATR_PERCENT',
            config={'period': config['atr_period']}
        )

    # Bollinger Bands
    if 'bb_period' in config:
        indicators['BOLLINGER_BANDS'] = BollingerBands(
            name='BOLLINGER_BANDS',
            config={
                'period': config['bb_period'],
                'std_dev': config.get('bb_std_dev', 2)
            }
        )

    # Historical Volatility
    if 'hv_period' in config:
        indicators['HISTORICAL_VOL'] = HistoricalVolatility(
            name='HISTORICAL_VOL',
            config={'period': config['hv_period']}
        )

    logger.info(f"Created {len(indicators)} volatility indicators")
    return indicators


if __name__ == "__main__":
    # Example usage
    import yfinance as yf

    # Fetch sample data
    ticker = yf.Ticker("QQQ")
    data = ticker.history(period="1y")
    data.columns = [col.lower().replace(' ', '_') for col in data.columns]

    # Test ATR
    atr = ATR(name='ATR_14', config={'period': 14})
    atr_values = atr.calculate(data)
    print(f"ATR latest value: {atr.get_latest_value(data)}")

    # Test ATR%
    atr_pct = ATRPercent(name='ATR_PCT', config={'period': 14})
    print(f"ATR% latest value: {atr_pct.get_latest_value(data)}%")

    # Test Bollinger Bands
    bb = BollingerBands(name='BB_20', config={'period': 20, 'std_dev': 2})
    bb_values = bb.calculate(data)
    print(f"\nBollinger Bands latest values:")
    print(bb_values.tail(1))

    # Test Historical Volatility
    hv = HistoricalVolatility(name='HV_20', config={'period': 20})
    hv_values = hv.calculate(data)
    print(f"\nHistorical Volatility latest value: {hv.get_latest_value(data)}%")
