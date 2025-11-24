"""
Base indicator class for TQQQ Market Regime Detection Framework.
All technical indicators inherit from this base class.
"""

from abc import ABC, abstractmethod
import pandas as pd
from typing import Dict, Any, Union, Optional
import logging

logger = logging.getLogger(__name__)


class BaseIndicator(ABC):
    """
    Abstract base class for all technical indicators.

    All indicators must implement the calculate() method.
    """

    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize indicator.

        Args:
            name: Indicator name (e.g., 'SMA_50', 'RSI_14')
            config: Configuration parameters for the indicator
        """
        self.name = name
        self.config = config or {}
        self._validate_config()

    def _validate_config(self) -> None:
        """
        Validate configuration parameters.
        Override in subclasses to add specific validation.
        """
        pass

    @abstractmethod
    def calculate(self, data: pd.DataFrame) -> Union[pd.Series, pd.DataFrame]:
        """
        Calculate the indicator values.

        Args:
            data: DataFrame with OHLCV data (columns: open, high, low, close, volume)
                  Indexed by date

        Returns:
            Series or DataFrame with calculated indicator values, indexed by date
        """
        pass

    def get_latest_value(self, data: pd.DataFrame) -> Optional[float]:
        """
        Get the most recent indicator value.

        Args:
            data: DataFrame with OHLCV data

        Returns:
            Latest indicator value or None if calculation failed
        """
        try:
            result = self.calculate(data)

            if isinstance(result, pd.Series):
                if not result.empty and pd.notna(result.iloc[-1]):
                    return float(result.iloc[-1])
            elif isinstance(result, pd.DataFrame):
                # For multi-column indicators, return the primary column
                # Subclasses should override this method for custom behavior
                if not result.empty:
                    return float(result.iloc[-1, 0])

            return None

        except Exception as e:
            logger.error(f"Failed to get latest value for {self.name}: {e}")
            return None

    def get_value_at_date(self, data: pd.DataFrame, date: pd.Timestamp) -> Optional[float]:
        """
        Get indicator value at a specific date.

        Args:
            data: DataFrame with OHLCV data
            date: Date to get value for

        Returns:
            Indicator value at the specified date or None
        """
        try:
            result = self.calculate(data)

            if isinstance(result, pd.Series):
                if date in result.index and pd.notna(result.loc[date]):
                    return float(result.loc[date])
            elif isinstance(result, pd.DataFrame):
                if date in result.index:
                    return float(result.loc[date].iloc[0])

            return None

        except Exception as e:
            logger.error(f"Failed to get value at {date} for {self.name}: {e}")
            return None

    def get_config_value(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value with a default fallback.

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        return self.config.get(key, default)

    def __repr__(self) -> str:
        """String representation of the indicator."""
        return f"{self.__class__.__name__}(name='{self.name}', config={self.config})"


class CompositeIndicator(BaseIndicator):
    """
    Base class for indicators that combine multiple sub-indicators.

    Example: MACD combines multiple moving averages
    """

    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(name, config)
        self.sub_indicators: Dict[str, BaseIndicator] = {}

    def add_sub_indicator(self, key: str, indicator: BaseIndicator) -> None:
        """
        Add a sub-indicator.

        Args:
            key: Identifier for the sub-indicator
            indicator: BaseIndicator instance
        """
        self.sub_indicators[key] = indicator

    def get_sub_indicator(self, key: str) -> Optional[BaseIndicator]:
        """
        Get a sub-indicator by key.

        Args:
            key: Identifier for the sub-indicator

        Returns:
            BaseIndicator instance or None if not found
        """
        return self.sub_indicators.get(key)


class IndicatorRegistry:
    """
    Registry for managing and instantiating indicators.
    Allows dynamic indicator creation from configuration.
    """

    def __init__(self):
        """Initialize the indicator registry."""
        self._registry: Dict[str, type] = {}

    def register(self, indicator_type: str, indicator_class: type) -> None:
        """
        Register an indicator class.

        Args:
            indicator_type: String identifier for the indicator (e.g., 'sma', 'rsi')
            indicator_class: Indicator class (must inherit from BaseIndicator)
        """
        if not issubclass(indicator_class, BaseIndicator):
            raise TypeError(f"{indicator_class} must inherit from BaseIndicator")

        self._registry[indicator_type.lower()] = indicator_class
        logger.info(f"Registered indicator: {indicator_type}")

    def create(
        self,
        indicator_type: str,
        name: str,
        config: Optional[Dict[str, Any]] = None
    ) -> BaseIndicator:
        """
        Create an indicator instance.

        Args:
            indicator_type: Type of indicator (e.g., 'sma', 'rsi')
            name: Name for this indicator instance
            config: Configuration parameters

        Returns:
            Initialized indicator instance

        Raises:
            ValueError: If indicator type not registered
        """
        indicator_class = self._registry.get(indicator_type.lower())

        if indicator_class is None:
            raise ValueError(
                f"Unknown indicator type: {indicator_type}. "
                f"Available types: {list(self._registry.keys())}"
            )

        return indicator_class(name=name, config=config)

    def list_indicators(self) -> list:
        """
        Get list of registered indicator types.

        Returns:
            List of indicator type strings
        """
        return list(self._registry.keys())

    def is_registered(self, indicator_type: str) -> bool:
        """
        Check if an indicator type is registered.

        Args:
            indicator_type: Indicator type to check

        Returns:
            True if registered, False otherwise
        """
        return indicator_type.lower() in self._registry


# Global registry instance
global_registry = IndicatorRegistry()


def register_indicator(indicator_type: str):
    """
    Decorator to register an indicator class.

    Usage:
        @register_indicator('sma')
        class SMA(BaseIndicator):
            ...
    """
    def decorator(indicator_class: type):
        global_registry.register(indicator_type, indicator_class)
        return indicator_class
    return decorator
