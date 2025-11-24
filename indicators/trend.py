"""
Trend indicators for TQQQ Market Regime Detection Framework.
Includes: Simple Moving Average (SMA), Exponential Moving Average (EMA), ADX
"""

import pandas as pd
import numpy as np
from typing import Optional, Dict, Any
from .base import BaseIndicator, register_indicator
import logging

logger = logging.getLogger(__name__)


@register_indicator('sma')
class SMA(BaseIndicator):
    """
    Simple Moving Average indicator.

    Config parameters:
        - period: Number of periods for the moving average (default: 50)
    """

    def _validate_config(self) -> None:
        """Validate SMA configuration."""
        period = self.config.get('period', 50)
        if not isinstance(period, int) or period < 1:
            raise ValueError(f"SMA period must be a positive integer, got {period}")

    def calculate(self, data: pd.DataFrame) -> pd.Series:
        """
        Calculate Simple Moving Average.

        Args:
            data: DataFrame with OHLCV data

        Returns:
            Series with SMA values
        """
        period = self.config.get('period', 50)

        if 'close' not in data.columns:
            raise ValueError("Data must contain 'close' column")

        sma = data['close'].rolling(window=period, min_periods=period).mean()
        return sma


@register_indicator('ema')
class EMA(BaseIndicator):
    """
    Exponential Moving Average indicator.

    Config parameters:
        - period: Number of periods for the moving average (default: 50)
    """

    def _validate_config(self) -> None:
        """Validate EMA configuration."""
        period = self.config.get('period', 50)
        if not isinstance(period, int) or period < 1:
            raise ValueError(f"EMA period must be a positive integer, got {period}")

    def calculate(self, data: pd.DataFrame) -> pd.Series:
        """
        Calculate Exponential Moving Average.

        Args:
            data: DataFrame with OHLCV data

        Returns:
            Series with EMA values
        """
        period = self.config.get('period', 50)

        if 'close' not in data.columns:
            raise ValueError("Data must contain 'close' column")

        ema = data['close'].ewm(span=period, adjust=False).mean()
        return ema


@register_indicator('adx')
class ADX(BaseIndicator):
    """
    Average Directional Index (ADX) - measures trend strength.

    Values:
        0-25: Weak trend
        25-50: Strong trend
        50-75: Very strong trend
        75-100: Extremely strong trend

    Config parameters:
        - period: Number of periods for ADX calculation (default: 14)
    """

    def _validate_config(self) -> None:
        """Validate ADX configuration."""
        period = self.config.get('period', 14)
        if not isinstance(period, int) or period < 1:
            raise ValueError(f"ADX period must be a positive integer, got {period}")

    def calculate(self, data: pd.DataFrame) -> pd.Series:
        """
        Calculate Average Directional Index.

        Args:
            data: DataFrame with OHLCV data (must have high, low, close)

        Returns:
            Series with ADX values
        """
        required_columns = ['high', 'low', 'close']
        for col in required_columns:
            if col not in data.columns:
                raise ValueError(f"Data must contain '{col}' column")

        period = self.config.get('period', 14)

        # Calculate True Range
        high = data['high']
        low = data['low']
        close = data['close']

        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))

        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

        # Calculate +DM and -DM
        high_diff = high.diff()
        low_diff = -low.diff()

        plus_dm = high_diff.copy()
        plus_dm[high_diff < low_diff] = 0
        plus_dm[plus_dm < 0] = 0

        minus_dm = low_diff.copy()
        minus_dm[low_diff < high_diff] = 0
        minus_dm[minus_dm < 0] = 0

        # Smooth the indicators
        atr = tr.rolling(window=period).mean()
        plus_di = 100 * (plus_dm.rolling(window=period).mean() / atr)
        minus_di = 100 * (minus_dm.rolling(window=period).mean() / atr)

        # Calculate ADX
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = dx.rolling(window=period).mean()

        return adx


@register_indicator('macd_trend')
class MACDTrend(BaseIndicator):
    """
    MACD as a trend indicator (just the MACD line, not the full histogram).

    Config parameters:
        - fast_period: Fast EMA period (default: 12)
        - slow_period: Slow EMA period (default: 26)
    """

    def _validate_config(self) -> None:
        """Validate MACD configuration."""
        fast = self.config.get('fast_period', 12)
        slow = self.config.get('slow_period', 26)

        if not isinstance(fast, int) or fast < 1:
            raise ValueError(f"MACD fast_period must be a positive integer, got {fast}")
        if not isinstance(slow, int) or slow < 1:
            raise ValueError(f"MACD slow_period must be a positive integer, got {slow}")
        if fast >= slow:
            raise ValueError(f"MACD fast_period ({fast}) must be less than slow_period ({slow})")

    def calculate(self, data: pd.DataFrame) -> pd.Series:
        """
        Calculate MACD line.

        Args:
            data: DataFrame with OHLCV data

        Returns:
            Series with MACD line values
        """
        if 'close' not in data.columns:
            raise ValueError("Data must contain 'close' column")

        fast_period = self.config.get('fast_period', 12)
        slow_period = self.config.get('slow_period', 26)

        ema_fast = data['close'].ewm(span=fast_period, adjust=False).mean()
        ema_slow = data['close'].ewm(span=slow_period, adjust=False).mean()

        macd_line = ema_fast - ema_slow

        return macd_line


@register_indicator('price_position')
class PricePosition(BaseIndicator):
    """
    Calculate price position relative to a moving average.
    Returns percentage above/below the MA.

    Config parameters:
        - period: MA period (default: 200)
    """

    def _validate_config(self) -> None:
        """Validate configuration."""
        period = self.config.get('period', 200)
        if not isinstance(period, int) or period < 1:
            raise ValueError(f"Period must be a positive integer, got {period}")

    def calculate(self, data: pd.DataFrame) -> pd.Series:
        """
        Calculate price position relative to MA.

        Args:
            data: DataFrame with OHLCV data

        Returns:
            Series with percentage above/below MA (positive = above, negative = below)
        """
        if 'close' not in data.columns:
            raise ValueError("Data must contain 'close' column")

        period = self.config.get('period', 200)

        ma = data['close'].rolling(window=period, min_periods=period).mean()
        position = ((data['close'] - ma) / ma) * 100

        return position


def create_trend_indicators(config: Dict[str, Any]) -> Dict[str, BaseIndicator]:
    """
    Create all trend indicators from configuration.

    Args:
        config: Configuration dictionary with trend parameters

    Returns:
        Dictionary mapping indicator names to indicator instances
    """
    indicators = {}

    # SMA indicators
    if 'sma_short' in config:
        indicators['SMA_SHORT'] = SMA(
            name='SMA_SHORT',
            config={'period': config['sma_short']}
        )

    if 'sma_long' in config:
        indicators['SMA_LONG'] = SMA(
            name='SMA_LONG',
            config={'period': config['sma_long']}
        )

    # ADX
    if 'adx_period' in config:
        indicators['ADX'] = ADX(
            name='ADX',
            config={'period': config['adx_period']}
        )

    # Price position
    if 'sma_long' in config:
        indicators['PRICE_POSITION'] = PricePosition(
            name='PRICE_POSITION',
            config={'period': config['sma_long']}
        )

    logger.info(f"Created {len(indicators)} trend indicators")
    return indicators


if __name__ == "__main__":
    # Example usage
    import yfinance as yf

    # Fetch sample data
    ticker = yf.Ticker("QQQ")
    data = ticker.history(period="1y")
    data.columns = [col.lower().replace(' ', '_') for col in data.columns]

    # Test SMA
    sma_50 = SMA(name='SMA_50', config={'period': 50})
    sma_values = sma_50.calculate(data)
    print(f"SMA 50 latest value: {sma_50.get_latest_value(data)}")

    # Test ADX
    adx = ADX(name='ADX_14', config={'period': 14})
    adx_values = adx.calculate(data)
    print(f"ADX latest value: {adx.get_latest_value(data)}")

    # Test Price Position
    price_pos = PricePosition(name='PRICE_POS_200', config={'period': 200})
    pos_values = price_pos.calculate(data)
    print(f"Price position latest value: {price_pos.get_latest_value(data)}%")
