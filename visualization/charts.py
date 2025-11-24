"""
Chart generation for TQQQ Market Regime Detection Framework.
Creates matplotlib-based visualizations of market data, indicators, and regime classifications.
"""

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Rectangle
import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
from typing import Optional, Dict, List, Tuple
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class RegimeChartGenerator:
    """
    Generates charts for regime detection analysis.
    """

    # Color scheme for regimes
    REGIME_COLORS = {
        'bull': '#2ecc71',      # Green
        'bear': '#e74c3c',      # Red
        'choppy': '#f39c12',    # Orange
    }

    def __init__(self, style: str = 'seaborn-v0_8-darkgrid'):
        """
        Initialize chart generator.

        Args:
            style: Matplotlib style to use
        """
        try:
            plt.style.use(style)
        except:
            logger.warning(f"Style '{style}' not available, using default")

        self.fig = None
        self.axes = None

    def create_regime_overview(
        self,
        price_data: pd.DataFrame,
        indicator_data: Dict[str, pd.Series],
        regime_data: pd.DataFrame,
        title: str = "TQQQ Market Regime Analysis",
        save_path: Optional[str] = None
    ) -> plt.Figure:
        """
        Create comprehensive regime overview chart.

        Args:
            price_data: DataFrame with OHLCV data
            indicator_data: Dictionary mapping indicator names to Series
            regime_data: DataFrame with regime classifications
            title: Chart title
            save_path: Path to save the chart (if None, displays instead)

        Returns:
            Matplotlib Figure object
        """
        # Create figure with subplots
        fig, axes = plt.subplots(4, 1, figsize=(14, 12), sharex=True)
        self.fig = fig
        self.axes = axes

        # Plot 1: Price with moving averages and regime background
        self._plot_price_with_regimes(axes[0], price_data, indicator_data, regime_data)

        # Plot 2: VIX
        self._plot_vix(axes[1], indicator_data)

        # Plot 3: RSI
        self._plot_rsi(axes[2], indicator_data)

        # Plot 4: MACD
        self._plot_macd(axes[3], indicator_data)

        # Format x-axis
        axes[-1].xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        axes[-1].xaxis.set_major_locator(mdates.MonthLocator(interval=1))
        plt.setp(axes[-1].xaxis.get_majorticklabels(), rotation=45, ha='right')

        # Overall title
        fig.suptitle(title, fontsize=16, fontweight='bold')

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"Chart saved to {save_path}")
        else:
            plt.show()

        return fig

    def _plot_price_with_regimes(
        self,
        ax: plt.Axes,
        price_data: pd.DataFrame,
        indicator_data: Dict[str, pd.Series],
        regime_data: pd.DataFrame
    ) -> None:
        """Plot price with moving averages and regime background colors."""
        # Add regime background colors
        if not regime_data.empty:
            self._add_regime_backgrounds(ax, regime_data)

        # Plot price
        ax.plot(price_data.index, price_data['close'], label='QQQ Price',
                color='black', linewidth=1.5, zorder=3)

        # Plot moving averages
        if 'SMA_50' in indicator_data:
            ax.plot(indicator_data['SMA_50'].index, indicator_data['SMA_50'],
                   label='SMA 50', color='blue', linewidth=1, alpha=0.7, zorder=2)

        if 'SMA_200' in indicator_data:
            ax.plot(indicator_data['SMA_200'].index, indicator_data['SMA_200'],
                   label='SMA 200', color='red', linewidth=1, alpha=0.7, zorder=2)

        ax.set_ylabel('Price ($)', fontweight='bold')
        ax.set_title('Price with Moving Averages and Regime', fontweight='bold')
        ax.legend(loc='upper left')
        ax.grid(True, alpha=0.3)

    def _plot_vix(self, ax: plt.Axes, indicator_data: Dict[str, pd.Series]) -> None:
        """Plot VIX with threshold levels."""
        if 'VIX_LEVEL' not in indicator_data:
            ax.text(0.5, 0.5, 'VIX data not available', ha='center', va='center',
                   transform=ax.transAxes)
            ax.set_ylabel('VIX')
            return

        vix = indicator_data['VIX_LEVEL']

        # Plot VIX
        ax.plot(vix.index, vix, label='VIX', color='purple', linewidth=1.5)

        # Plot VIX MA if available
        if 'VIX_MA' in indicator_data:
            ax.plot(indicator_data['VIX_MA'].index, indicator_data['VIX_MA'],
                   label='VIX MA(20)', color='purple', linewidth=1, alpha=0.5, linestyle='--')

        # Add threshold lines
        ax.axhline(y=20, color='orange', linestyle='--', alpha=0.5, label='Threshold: 20')
        ax.axhline(y=25, color='red', linestyle='--', alpha=0.5, label='Threshold: 25')

        ax.set_ylabel('VIX', fontweight='bold')
        ax.set_title('CBOE Volatility Index (VIX)', fontweight='bold')
        ax.legend(loc='upper left')
        ax.grid(True, alpha=0.3)

    def _plot_rsi(self, ax: plt.Axes, indicator_data: Dict[str, pd.Series]) -> None:
        """Plot RSI with overbought/oversold levels."""
        if 'RSI' not in indicator_data:
            ax.text(0.5, 0.5, 'RSI data not available', ha='center', va='center',
                   transform=ax.transAxes)
            ax.set_ylabel('RSI')
            return

        rsi = indicator_data['RSI']

        # Plot RSI
        ax.plot(rsi.index, rsi, label='RSI(14)', color='blue', linewidth=1.5)

        # Add overbought/oversold lines
        ax.axhline(y=70, color='red', linestyle='--', alpha=0.5, label='Overbought (70)')
        ax.axhline(y=30, color='green', linestyle='--', alpha=0.5, label='Oversold (30)')
        ax.axhline(y=50, color='gray', linestyle=':', alpha=0.3)

        # Fill overbought/oversold regions
        ax.fill_between(rsi.index, 70, 100, alpha=0.1, color='red')
        ax.fill_between(rsi.index, 0, 30, alpha=0.1, color='green')

        ax.set_ylabel('RSI', fontweight='bold')
        ax.set_title('Relative Strength Index (RSI)', fontweight='bold')
        ax.set_ylim(0, 100)
        ax.legend(loc='upper left')
        ax.grid(True, alpha=0.3)

    def _plot_macd(self, ax: plt.Axes, indicator_data: Dict[str, pd.Series]) -> None:
        """Plot MACD histogram."""
        if 'MACD' not in indicator_data:
            ax.text(0.5, 0.5, 'MACD data not available', ha='center', va='center',
                   transform=ax.transAxes)
            ax.set_ylabel('MACD')
            return

        macd = indicator_data['MACD']

        # Create histogram colors (green for positive, red for negative)
        colors = ['green' if val > 0 else 'red' for val in macd.values]

        # Plot MACD histogram
        ax.bar(macd.index, macd.values, color=colors, alpha=0.6, label='MACD Histogram')

        # Add zero line
        ax.axhline(y=0, color='black', linestyle='-', linewidth=0.8)

        ax.set_ylabel('MACD', fontweight='bold')
        ax.set_title('MACD Histogram', fontweight='bold')
        ax.set_xlabel('Date', fontweight='bold')
        ax.legend(loc='upper left')
        ax.grid(True, alpha=0.3)

    def _add_regime_backgrounds(
        self,
        ax: plt.Axes,
        regime_data: pd.DataFrame
    ) -> None:
        """Add colored background regions for each regime."""
        if regime_data.empty:
            return

        for i in range(len(regime_data) - 1):
            regime = regime_data.iloc[i]['regime']
            start = regime_data.index[i]
            end = regime_data.index[i + 1]

            color = self.REGIME_COLORS.get(regime, 'gray')

            ax.axvspan(start, end, alpha=0.1, color=color, zorder=1)

        # Add last regime to present
        if len(regime_data) > 0:
            last_regime = regime_data.iloc[-1]['regime']
            last_date = regime_data.index[-1]
            color = self.REGIME_COLORS.get(last_regime, 'gray')
            ax.axvspan(last_date, ax.get_xlim()[1], alpha=0.1, color=color, zorder=1)

    def create_regime_timeline(
        self,
        regime_data: pd.DataFrame,
        title: str = "Regime Timeline",
        save_path: Optional[str] = None
    ) -> plt.Figure:
        """
        Create a timeline visualization of regime changes.

        Args:
            regime_data: DataFrame with regime classifications
            title: Chart title
            save_path: Path to save the chart

        Returns:
            Matplotlib Figure object
        """
        fig, ax = plt.subplots(figsize=(14, 4))

        if regime_data.empty:
            ax.text(0.5, 0.5, 'No regime data available', ha='center', va='center',
                   transform=ax.transAxes)
            return fig

        # Create regime timeline
        for i in range(len(regime_data) - 1):
            regime = regime_data.iloc[i]['regime']
            start = regime_data.index[i]
            end = regime_data.index[i + 1]

            color = self.REGIME_COLORS.get(regime, 'gray')

            # Draw rectangle for this regime period
            width = (end - start).days
            rect = Rectangle(
                (mdates.date2num(start), 0),
                width,
                1,
                facecolor=color,
                edgecolor='black',
                linewidth=0.5
            )
            ax.add_patch(rect)

            # Add label
            mid_point = start + (end - start) / 2
            ax.text(mid_point, 0.5, regime.upper(), ha='center', va='center',
                   fontweight='bold', fontsize=10)

        # Last regime
        if len(regime_data) > 0:
            last_regime = regime_data.iloc[-1]['regime']
            last_date = regime_data.index[-1]
            color = self.REGIME_COLORS.get(last_regime, 'gray')

            # Extend to today
            today = pd.Timestamp.now()
            width = (today - last_date).days

            rect = Rectangle(
                (mdates.date2num(last_date), 0),
                width,
                1,
                facecolor=color,
                edgecolor='black',
                linewidth=0.5
            )
            ax.add_patch(rect)

            mid_point = last_date + (today - last_date) / 2
            ax.text(mid_point, 0.5, f"{last_regime.upper()} (Current)",
                   ha='center', va='center', fontweight='bold', fontsize=10)

        ax.set_ylim(0, 1)
        ax.set_xlim(regime_data.index[0], pd.Timestamp.now())
        ax.set_yticks([])
        ax.set_title(title, fontweight='bold', fontsize=14)
        ax.set_xlabel('Date', fontweight='bold')

        # Format x-axis
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"Timeline saved to {save_path}")
        else:
            plt.show()

        return fig

    def create_exposure_chart(
        self,
        regime_data: pd.DataFrame,
        title: str = "Recommended TQQQ Exposure Over Time",
        save_path: Optional[str] = None
    ) -> plt.Figure:
        """
        Create chart showing recommended exposure over time.

        Args:
            regime_data: DataFrame with regime classifications and exposure
            title: Chart title
            save_path: Path to save the chart

        Returns:
            Matplotlib Figure object
        """
        fig, ax = plt.subplots(figsize=(14, 6))

        if regime_data.empty or 'exposure_recommendation' not in regime_data.columns:
            ax.text(0.5, 0.5, 'No exposure data available', ha='center', va='center',
                   transform=ax.transAxes)
            return fig

        # Plot exposure as area chart
        ax.fill_between(
            regime_data.index,
            0,
            regime_data['exposure_recommendation'] * 100,
            alpha=0.3,
            color='blue',
            label='Recommended Exposure'
        )

        ax.plot(
            regime_data.index,
            regime_data['exposure_recommendation'] * 100,
            color='blue',
            linewidth=2
        )

        # Add reference lines
        ax.axhline(y=100, color='green', linestyle='--', alpha=0.5, label='100% (Full Bull)')
        ax.axhline(y=50, color='orange', linestyle='--', alpha=0.5, label='50% (Choppy)')
        ax.axhline(y=0, color='red', linestyle='--', alpha=0.5, label='0% (Cash)')

        ax.set_ylabel('Exposure (%)', fontweight='bold')
        ax.set_xlabel('Date', fontweight='bold')
        ax.set_title(title, fontweight='bold', fontsize=14)
        ax.set_ylim(-5, 105)
        ax.legend(loc='upper left')
        ax.grid(True, alpha=0.3)

        # Format x-axis
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"Exposure chart saved to {save_path}")
        else:
            plt.show()

        return fig


if __name__ == "__main__":
    # Example usage with sample data
    logging.basicConfig(level=logging.INFO)

    # Generate sample data
    dates = pd.date_range(start='2024-01-01', end='2024-12-01', freq='D')
    price_data = pd.DataFrame({
        'close': 400 + np.cumsum(np.random.randn(len(dates)) * 2),
        'volume': np.random.randint(10000000, 50000000, len(dates))
    }, index=dates)

    indicator_data = {
        'SMA_50': price_data['close'].rolling(50).mean(),
        'SMA_200': price_data['close'].rolling(200).mean(),
        'RSI': 50 + np.random.randn(len(dates)) * 20,
        'MACD': np.random.randn(len(dates)) * 5,
        'VIX_LEVEL': 15 + np.abs(np.random.randn(len(dates)) * 5),
    }

    for key in indicator_data:
        indicator_data[key] = pd.Series(indicator_data[key], index=dates)

    # Sample regime data
    regime_dates = pd.date_range(start='2024-01-01', end='2024-12-01', freq='30D')
    regime_data = pd.DataFrame({
        'regime': np.random.choice(['bull', 'bear', 'choppy'], len(regime_dates)),
        'confidence': np.random.random(len(regime_dates)),
        'exposure_recommendation': np.random.choice([0.0, 0.5, 1.0], len(regime_dates))
    }, index=regime_dates)

    # Create chart generator
    generator = RegimeChartGenerator()

    print("Generating sample charts...")
    print("Close the chart window to continue...")

    # Create overview chart
    generator.create_regime_overview(
        price_data,
        indicator_data,
        regime_data,
        save_path='outputs/regime_overview_sample.png'
    )

    print("Sample charts generated in outputs/ directory")
