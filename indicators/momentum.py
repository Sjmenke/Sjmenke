"""
Momentum indicators for TQQQ Market Regime Detection Framework.
Includes: RSI, MACD, ROC, Stochastic
"""

import pandas as pd
import numpy as np
from typing import Optional, Dict, Any
from .base import BaseIndicator, CompositeIndicator, register_indicator
import logging

logger = logging.getLogger(__name__)


@register_indicator('rsi')
class RSI(BaseIndicator):
    """
    Relative Strength Index (RSI) - momentum oscillator.

    Values:
        0-30: Oversold
        30-70: Neutral
        70-100: Overbought

    Config parameters:
        - period: Number of periods for RSI calculation (default: 14)
    """

    def _validate_config(self) -> None:
        """Validate RSI configuration."""
        period = self.config.get('period', 14)
        if not isinstance(period, int) or period < 1:
            raise ValueError(f"RSI period must be a positive integer, got {period}")

    def calculate(self, data: pd.DataFrame) -> pd.Series:
        """
        Calculate Relative Strength Index.

        Args:
            data: DataFrame with OHLCV data

        Returns:
            Series with RSI values (0-100)
        """
        if 'close' not in data.columns:
            raise ValueError("Data must contain 'close' column")

        period = self.config.get('period', 14)

        # Calculate price changes
        delta = data['close'].diff()

        # Separate gains and losses
        gain = delta.copy()
        gain[gain < 0] = 0

        loss = -delta.copy()
        loss[loss < 0] = 0

        # Calculate average gain and loss using Wilder's smoothing (EMA)
        avg_gain = gain.ewm(span=period, adjust=False).mean()
        avg_loss = loss.ewm(span=period, adjust=False).mean()

        # Calculate RS and RSI
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        return rsi


@register_indicator('macd')
class MACD(CompositeIndicator):
    """
    Moving Average Convergence Divergence (MACD).

    Returns a DataFrame with columns: macd, signal, histogram

    Config parameters:
        - fast_period: Fast EMA period (default: 12)
        - slow_period: Slow EMA period (default: 26)
        - signal_period: Signal line EMA period (default: 9)
    """

    def _validate_config(self) -> None:
        """Validate MACD configuration."""
        fast = self.config.get('fast_period', 12)
        slow = self.config.get('slow_period', 26)
        signal = self.config.get('signal_period', 9)

        if not isinstance(fast, int) or fast < 1:
            raise ValueError(f"MACD fast_period must be a positive integer, got {fast}")
        if not isinstance(slow, int) or slow < 1:
            raise ValueError(f"MACD slow_period must be a positive integer, got {slow}")
        if not isinstance(signal, int) or signal < 1:
            raise ValueError(f"MACD signal_period must be a positive integer, got {signal}")
        if fast >= slow:
            raise ValueError(f"MACD fast_period ({fast}) must be less than slow_period ({slow})")

    def calculate(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate MACD, Signal, and Histogram.

        Args:
            data: DataFrame with OHLCV data

        Returns:
            DataFrame with columns: macd, signal, histogram
        """
        if 'close' not in data.columns:
            raise ValueError("Data must contain 'close' column")

        fast_period = self.config.get('fast_period', 12)
        slow_period = self.config.get('slow_period', 26)
        signal_period = self.config.get('signal_period', 9)

        # Calculate MACD line
        ema_fast = data['close'].ewm(span=fast_period, adjust=False).mean()
        ema_slow = data['close'].ewm(span=slow_period, adjust=False).mean()
        macd_line = ema_fast - ema_slow

        # Calculate signal line
        signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()

        # Calculate histogram
        histogram = macd_line - signal_line

        result = pd.DataFrame({
            'macd': macd_line,
            'signal': signal_line,
            'histogram': histogram
        }, index=data.index)

        return result

    def get_latest_value(self, data: pd.DataFrame) -> Optional[float]:
        """
        Get the latest MACD histogram value (primary signal).

        Args:
            data: DataFrame with OHLCV data

        Returns:
            Latest histogram value
        """
        result = self.calculate(data)
        if not result.empty and pd.notna(result['histogram'].iloc[-1]):
            return float(result['histogram'].iloc[-1])
        return None


@register_indicator('roc')
class ROC(BaseIndicator):
    """
    Rate of Change (ROC) - momentum indicator.

    Measures percentage change over a specified period.

    Config parameters:
        - period: Number of periods for ROC calculation (default: 63 for 3-month)
    """

    def _validate_config(self) -> None:
        """Validate ROC configuration."""
        period = self.config.get('period', 63)
        if not isinstance(period, int) or period < 1:
            raise ValueError(f"ROC period must be a positive integer, got {period}")

    def calculate(self, data: pd.DataFrame) -> pd.Series:
        """
        Calculate Rate of Change.

        Args:
            data: DataFrame with OHLCV data

        Returns:
            Series with ROC values (percentage)
        """
        if 'close' not in data.columns:
            raise ValueError("Data must contain 'close' column")

        period = self.config.get('period', 63)

        # Calculate ROC as percentage change
        roc = ((data['close'] - data['close'].shift(period)) / data['close'].shift(period)) * 100

        return roc


@register_indicator('stochastic')
class Stochastic(BaseIndicator):
    """
    Stochastic Oscillator - momentum indicator.

    Returns a DataFrame with columns: k, d

    Values:
        0-20: Oversold
        20-80: Neutral
        80-100: Overbought

    Config parameters:
        - k_period: %K period (default: 14)
        - d_period: %D smoothing period (default: 3)
    """

    def _validate_config(self) -> None:
        """Validate Stochastic configuration."""
        k_period = self.config.get('k_period', 14)
        d_period = self.config.get('d_period', 3)

        if not isinstance(k_period, int) or k_period < 1:
            raise ValueError(f"Stochastic k_period must be a positive integer, got {k_period}")
        if not isinstance(d_period, int) or d_period < 1:
            raise ValueError(f"Stochastic d_period must be a positive integer, got {d_period}")

    def calculate(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate Stochastic Oscillator.

        Args:
            data: DataFrame with OHLCV data (must have high, low, close)

        Returns:
            DataFrame with columns: k, d
        """
        required_columns = ['high', 'low', 'close']
        for col in required_columns:
            if col not in data.columns:
                raise ValueError(f"Data must contain '{col}' column")

        k_period = self.config.get('k_period', 14)
        d_period = self.config.get('d_period', 3)

        # Calculate %K
        low_min = data['low'].rolling(window=k_period, min_periods=k_period).min()
        high_max = data['high'].rolling(window=k_period, min_periods=k_period).max()

        k = 100 * (data['close'] - low_min) / (high_max - low_min)

        # Calculate %D (smoothed %K)
        d = k.rolling(window=d_period, min_periods=d_period).mean()

        result = pd.DataFrame({
            'k': k,
            'd': d
        }, index=data.index)

        return result

    def get_latest_value(self, data: pd.DataFrame) -> Optional[float]:
        """
        Get the latest %K value (primary signal).

        Args:
            data: DataFrame with OHLCV data

        Returns:
            Latest %K value
        """
        result = self.calculate(data)
        if not result.empty and pd.notna(result['k'].iloc[-1]):
            return float(result['k'].iloc[-1])
        return None


@register_indicator('momentum')
class Momentum(BaseIndicator):
    """
    Simple Momentum indicator - difference between current and past price.

    Config parameters:
        - period: Number of periods to look back (default: 10)
    """

    def _validate_config(self) -> None:
        """Validate configuration."""
        period = self.config.get('period', 10)
        if not isinstance(period, int) or period < 1:
            raise ValueError(f"Momentum period must be a positive integer, got {period}")

    def calculate(self, data: pd.DataFrame) -> pd.Series:
        """
        Calculate momentum.

        Args:
            data: DataFrame with OHLCV data

        Returns:
            Series with momentum values (price difference)
        """
        if 'close' not in data.columns:
            raise ValueError("Data must contain 'close' column")

        period = self.config.get('period', 10)

        momentum = data['close'] - data['close'].shift(period)

        return momentum


def create_momentum_indicators(config: Dict[str, Any]) -> Dict[str, BaseIndicator]:
    """
    Create all momentum indicators from configuration.

    Args:
        config: Configuration dictionary with momentum parameters

    Returns:
        Dictionary mapping indicator names to indicator instances
    """
    indicators = {}

    # RSI
    if 'rsi_period' in config:
        indicators['RSI'] = RSI(
            name='RSI',
            config={'period': config['rsi_period']}
        )

    # MACD
    if all(k in config for k in ['macd_fast', 'macd_slow', 'macd_signal']):
        indicators['MACD'] = MACD(
            name='MACD',
            config={
                'fast_period': config['macd_fast'],
                'slow_period': config['macd_slow'],
                'signal_period': config['macd_signal']
            }
        )

    # ROC
    if 'roc_period' in config:
        indicators['ROC'] = ROC(
            name='ROC',
            config={'period': config['roc_period']}
        )

    # Stochastic
    if 'stoch_k_period' in config:
        indicators['STOCHASTIC'] = Stochastic(
            name='STOCHASTIC',
            config={
                'k_period': config['stoch_k_period'],
                'd_period': config.get('stoch_d_period', 3)
            }
        )

    logger.info(f"Created {len(indicators)} momentum indicators")
    return indicators


if __name__ == "__main__":
    # Example usage
    import yfinance as yf

    # Fetch sample data
    ticker = yf.Ticker("QQQ")
    data = ticker.history(period="1y")
    data.columns = [col.lower().replace(' ', '_') for col in data.columns]

    # Test RSI
    rsi = RSI(name='RSI_14', config={'period': 14})
    rsi_values = rsi.calculate(data)
    print(f"RSI latest value: {rsi.get_latest_value(data)}")

    # Test MACD
    macd = MACD(name='MACD', config={'fast_period': 12, 'slow_period': 26, 'signal_period': 9})
    macd_values = macd.calculate(data)
    print(f"\nMACD latest values:")
    print(macd_values.tail(1))
    print(f"MACD histogram: {macd.get_latest_value(data)}")

    # Test ROC
    roc = ROC(name='ROC_63', config={'period': 63})
    roc_values = roc.calculate(data)
    print(f"\nROC (3-month) latest value: {roc.get_latest_value(data)}%")

    # Test Stochastic
    stoch = Stochastic(name='STOCH', config={'k_period': 14, 'd_period': 3})
    stoch_values = stoch.calculate(data)
    print(f"\nStochastic latest values:")
    print(stoch_values.tail(1))
