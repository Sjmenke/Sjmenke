"""
Market breadth indicators for TQQQ Market Regime Detection Framework.
Includes: Advance/Decline analysis, stocks above moving averages

Note: Some breadth indicators require additional data that may not be readily available
from free data sources. These are implemented with fallback options.
"""

import pandas as pd
import numpy as np
from typing import Optional, Dict, Any
from .base import BaseIndicator, register_indicator
import logging

logger = logging.getLogger(__name__)


@register_indicator('advance_decline_line')
class AdvanceDeclineLine(BaseIndicator):
    """
    Advance/Decline Line - cumulative measure of market breadth.

    Note: Requires advance and decline data which may need to be fetched separately.

    Config parameters:
        None
    """

    def calculate(self, data: pd.DataFrame) -> pd.Series:
        """
        Calculate Advance/Decline Line.

        Args:
            data: DataFrame with 'advances' and 'declines' columns

        Returns:
            Series with cumulative A/D line
        """
        required_columns = ['advances', 'declines']
        for col in required_columns:
            if col not in data.columns:
                raise ValueError(f"Data must contain '{col}' column for A/D Line")

        # Calculate net advances
        net_advances = data['advances'] - data['declines']

        # Cumulative sum
        ad_line = net_advances.cumsum()

        return ad_line


@register_indicator('percent_above_ma')
class PercentAboveMA(BaseIndicator):
    """
    Percentage of stocks above their moving average.

    Note: This is a placeholder. In production, you would need to:
    1. Fetch data for multiple stocks (e.g., QQQ components)
    2. Calculate MA for each stock
    3. Calculate percentage above their respective MAs

    For now, this can be approximated using sector ETFs or major indices.

    Config parameters:
        - ma_period: Moving average period (default: 200)
    """

    def _validate_config(self) -> None:
        """Validate configuration."""
        ma_period = self.config.get('ma_period', 200)
        if not isinstance(ma_period, int) or ma_period < 1:
            raise ValueError(f"MA period must be a positive integer, got {ma_period}")

    def calculate(self, data: pd.DataFrame) -> pd.Series:
        """
        Calculate percentage above MA (placeholder implementation).

        Args:
            data: DataFrame with OHLCV data

        Returns:
            Series with estimated percentage
        """
        # This is a simplified version
        # In production, you'd calculate this across multiple stocks
        logger.warning("PercentAboveMA is using simplified calculation")

        ma_period = self.config.get('ma_period', 200)

        if 'close' not in data.columns:
            raise ValueError("Data must contain 'close' column")

        # Calculate MA
        ma = data['close'].rolling(window=ma_period, min_periods=ma_period).mean()

        # Binary: 1 if above MA, 0 if below (simplified for single ticker)
        above_ma = (data['close'] > ma).astype(int) * 100

        return above_ma


@register_indicator('breadth_thrust')
class BreadthThrust(BaseIndicator):
    """
    Breadth Thrust indicator - measures rapid improvement in market breadth.

    A breadth thrust occurs when the 10-day moving average of the advance/decline
    ratio moves from below 40% to above 61.5% within 10 days.

    Config parameters:
        - period: Moving average period (default: 10)
        - low_threshold: Lower threshold (default: 0.4)
        - high_threshold: Upper threshold (default: 0.615)
    """

    def _validate_config(self) -> None:
        """Validate configuration."""
        period = self.config.get('period', 10)
        if not isinstance(period, int) or period < 1:
            raise ValueError(f"Period must be a positive integer, got {period}")

    def calculate(self, data: pd.DataFrame) -> pd.Series:
        """
        Calculate Breadth Thrust indicator.

        Args:
            data: DataFrame with 'advances' and 'declines' columns

        Returns:
            Series with breadth thrust ratio
        """
        required_columns = ['advances', 'declines']
        for col in required_columns:
            if col not in data.columns:
                raise ValueError(f"Data must contain '{col}' column")

        period = self.config.get('period', 10)

        # Calculate advance/decline ratio
        ad_ratio = data['advances'] / (data['advances'] + data['declines'])

        # Calculate moving average
        ad_ratio_ma = ad_ratio.rolling(window=period, min_periods=period).mean()

        return ad_ratio_ma


@register_indicator('mcclellan_oscillator')
class McClellanOscillator(BaseIndicator):
    """
    McClellan Oscillator - breadth momentum indicator.

    Difference between 19-day and 39-day EMAs of net advances.

    Config parameters:
        - fast_period: Fast EMA period (default: 19)
        - slow_period: Slow EMA period (default: 39)
    """

    def _validate_config(self) -> None:
        """Validate configuration."""
        fast = self.config.get('fast_period', 19)
        slow = self.config.get('slow_period', 39)

        if not isinstance(fast, int) or fast < 1:
            raise ValueError(f"Fast period must be a positive integer, got {fast}")
        if not isinstance(slow, int) or slow < 1:
            raise ValueError(f"Slow period must be a positive integer, got {slow}")

    def calculate(self, data: pd.DataFrame) -> pd.Series:
        """
        Calculate McClellan Oscillator.

        Args:
            data: DataFrame with 'advances' and 'declines' columns

        Returns:
            Series with McClellan Oscillator values
        """
        required_columns = ['advances', 'declines']
        for col in required_columns:
            if col not in data.columns:
                raise ValueError(f"Data must contain '{col}' column")

        fast_period = self.config.get('fast_period', 19)
        slow_period = self.config.get('slow_period', 39)

        # Calculate net advances
        net_advances = data['advances'] - data['declines']

        # Calculate EMAs
        ema_fast = net_advances.ewm(span=fast_period, adjust=False).mean()
        ema_slow = net_advances.ewm(span=slow_period, adjust=False).mean()

        # McClellan Oscillator
        mcclellan = ema_fast - ema_slow

        return mcclellan


def create_breadth_indicators(config: Dict[str, Any]) -> Dict[str, BaseIndicator]:
    """
    Create breadth indicators from configuration.

    Note: Many breadth indicators require additional data sources.

    Args:
        config: Configuration dictionary with breadth parameters

    Returns:
        Dictionary mapping indicator names to indicator instances
    """
    indicators = {}

    # Percent above MA (if enabled)
    if config.get('enable_percent_above_ma', False):
        indicators['PERCENT_ABOVE_MA_200'] = PercentAboveMA(
            name='PERCENT_ABOVE_MA_200',
            config={'ma_period': 200}
        )

    # Note: Other breadth indicators require advance/decline data
    # which needs to be fetched separately

    logger.info(f"Created {len(indicators)} breadth indicators")
    return indicators


if __name__ == "__main__":
    # Example usage
    print("Breadth indicators require additional data sources (advance/decline data)")
    print("These are typically available from paid data providers or require")
    print("fetching and processing data for multiple stocks.")
    print("\nFor the initial implementation, breadth indicators are optional.")
