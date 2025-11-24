"""
Terminal dashboard for TQQQ Market Regime Detection Framework.
Displays current regime status and key indicators in a formatted terminal view.
"""

from datetime import datetime, date, timedelta
from typing import Dict, Any, Optional, List
import logging

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.layout import Layout
    from rich.text import Text
    from rich import box
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    logging.warning("rich package not installed. Install with: pip install rich")

logger = logging.getLogger(__name__)


class RegimeDashboard:
    """
    Terminal dashboard for displaying regime status.
    Uses the 'rich' library for pretty formatting.
    """

    REGIME_COLORS = {
        'bull': 'green',
        'bear': 'red',
        'choppy': 'yellow',
    }

    REGIME_SYMBOLS = {
        'bull': '📈',
        'bear': '📉',
        'choppy': '〰️',
    }

    def __init__(self):
        """Initialize dashboard."""
        if RICH_AVAILABLE:
            self.console = Console()
        else:
            self.console = None

    def is_available(self) -> bool:
        """Check if dashboard is available."""
        return self.console is not None

    def display_current_status(
        self,
        regime: str,
        confidence: float,
        exposure: float,
        indicators: Dict[str, float],
        regime_details: Optional[Dict[str, Any]] = None,
        price_data: Optional[Dict[str, float]] = None,
        last_update: Optional[datetime] = None,
        upcoming_events: Optional[List[Dict[str, Any]]] = None
    ) -> None:
        """
        Display current regime status dashboard.

        Args:
            regime: Current regime ('bull', 'bear', 'choppy')
            confidence: Confidence score (0-1)
            exposure: Recommended exposure (0-1)
            indicators: Dictionary of indicator values
            regime_details: Detailed regime evaluation results
            price_data: Current price data
            last_update: Timestamp of last update
            upcoming_events: List of upcoming economic events
        """
        if not self.is_available():
            self._display_simple_status(regime, confidence, exposure, indicators)
            return

        # Clear console
        self.console.clear()

        # Create layout
        layout = Layout()

        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main"),
            Layout(name="footer", size=3)
        )

        layout["main"].split_row(
            Layout(name="left"),
            Layout(name="right")
        )

        # Header
        header = self._create_header(last_update)
        layout["header"].update(header)

        # Main regime status
        regime_panel = self._create_regime_panel(regime, confidence, exposure)
        layout["left"].split_column(
            Layout(regime_panel, size=8),
            Layout(self._create_indicators_table(indicators))
        )

        # Right side
        right_panels = []

        if price_data:
            right_panels.append(Layout(self._create_price_panel(price_data), size=8))

        if regime_details:
            right_panels.append(Layout(self._create_rules_panel(regime, regime_details)))

        if upcoming_events:
            right_panels.append(Layout(self._create_events_panel(upcoming_events), size=10))

        if right_panels:
            layout["right"].split_column(*right_panels)

        # Footer
        footer = self._create_footer()
        layout["footer"].update(footer)

        # Display
        self.console.print(layout)

    def _create_header(self, last_update: Optional[datetime]) -> Panel:
        """Create header panel."""
        title = Text("TQQQ MARKET REGIME DETECTION", style="bold cyan", justify="center")

        if last_update:
            subtitle = f"Last Update: {last_update.strftime('%Y-%m-%d %H:%M:%S')}"
        else:
            subtitle = f"Current Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

        return Panel(
            f"{title}\n{subtitle}",
            box=box.DOUBLE,
            style="cyan"
        )

    def _create_regime_panel(self, regime: str, confidence: float, exposure: float) -> Panel:
        """Create regime status panel."""
        color = self.REGIME_COLORS.get(regime, 'white')
        symbol = self.REGIME_SYMBOLS.get(regime, '❓')

        # Create status text
        status_text = Text()
        status_text.append(f"\n{symbol}  ", style=f"bold {color}")
        status_text.append(f"{regime.upper()}\n\n", style=f"bold {color} underline")

        # Confidence bar
        confidence_pct = confidence * 100
        confidence_bar = self._create_progress_bar(confidence, 30, color)
        status_text.append(f"Confidence: {confidence_pct:.1f}%\n", style="bold")
        status_text.append(f"{confidence_bar}\n\n")

        # Exposure recommendation
        exposure_pct = exposure * 100
        exposure_bar = self._create_progress_bar(exposure, 30, 'blue')
        status_text.append(f"TQQQ Exposure: {exposure_pct:.0f}%\n", style="bold")
        status_text.append(f"{exposure_bar}\n")

        # Position size calculation
        account_value = 100000  # Example
        position_size = account_value * exposure
        status_text.append(f"\nPosition Size (on $100K): ${position_size:,.0f}\n", style="dim")

        return Panel(
            status_text,
            title="[bold]Current Regime Status[/bold]",
            border_style=color,
            box=box.ROUNDED
        )

    def _create_indicators_table(self, indicators: Dict[str, float]) -> Table:
        """Create indicators table."""
        table = Table(title="Key Indicators", box=box.SIMPLE, show_header=True)

        table.add_column("Indicator", style="cyan", no_wrap=True)
        table.add_column("Value", justify="right", style="green")
        table.add_column("Signal", justify="center")

        # Add rows for key indicators
        for name, value in indicators.items():
            if value is None:
                continue

            signal = self._get_indicator_signal(name, value)
            signal_color = signal[1] if isinstance(signal, tuple) else "white"
            signal_text = signal[0] if isinstance(signal, tuple) else signal

            # Format value
            if 'RSI' in name or 'ADX' in name:
                value_str = f"{value:.1f}"
            elif 'VIX' in name or 'price' in name.lower():
                value_str = f"{value:.2f}"
            elif 'SMA' in name:
                value_str = f"${value:.2f}"
            else:
                value_str = f"{value:.2f}"

            table.add_row(name, value_str, f"[{signal_color}]{signal_text}[/{signal_color}]")

        return table

    def _create_price_panel(self, price_data: Dict[str, float]) -> Panel:
        """Create price information panel."""
        text = Text()

        for ticker, price in price_data.items():
            text.append(f"{ticker}: ", style="bold cyan")
            text.append(f"${price:.2f}\n", style="bold white")

        return Panel(
            text,
            title="[bold]Current Prices[/bold]",
            border_style="blue",
            box=box.ROUNDED
        )

    def _create_rules_panel(self, regime: str, regime_details: Dict[str, Any]) -> Panel:
        """Create panel showing which rules passed."""
        if regime not in regime_details:
            return Panel("No rule details available", title="Rule Evaluation")

        details = regime_details[regime]
        results = details.get('results', [])

        text = Text()
        text.append(f"Rules for {regime.upper()}:\n\n", style="bold")

        for rule, passed in results:
            symbol = "✓" if passed else "✗"
            color = "green" if passed else "red"
            text.append(f"{symbol} ", style=f"bold {color}")
            text.append(f"{rule}\n", style="white" if passed else "dim")

        passed_count = details.get('rules_passed', 0)
        total_count = details.get('total_rules', 0)

        text.append(f"\nPassed: {passed_count}/{total_count}\n", style="bold")

        return Panel(
            text,
            title=f"[bold]{regime.upper()} Regime Rules[/bold]",
            border_style=self.REGIME_COLORS.get(regime, 'white'),
            box=box.ROUNDED
        )

    def _create_events_panel(self, events: List[Dict[str, Any]]) -> Panel:
        """Create upcoming events panel."""
        table = Table(box=box.SIMPLE, show_header=True, header_style="bold cyan")

        table.add_column("Date", style="cyan")
        table.add_column("Event", style="white")
        table.add_column("Importance", justify="center")

        for event in events[:5]:  # Show next 5 events
            event_date = event.get('date', date.today())
            if isinstance(event_date, str):
                event_date = datetime.strptime(event_date, '%Y-%m-%d').date()

            days_until = (event_date - date.today()).days
            date_str = f"{event_date.strftime('%m/%d')} ({days_until}d)"

            importance = event.get('importance', 'medium')
            imp_color = {
                'high': 'red',
                'medium': 'yellow',
                'low': 'green'
            }.get(importance, 'white')

            table.add_row(
                date_str,
                event.get('event_name', ''),
                f"[{imp_color}]{importance.upper()}[/{imp_color}]"
            )

        return Panel(
            table,
            title="[bold]Upcoming Economic Events[/bold]",
            border_style="yellow",
            box=box.ROUNDED
        )

    def _create_footer(self) -> Panel:
        """Create footer panel."""
        footer_text = "Press Ctrl+C to exit | Use 'python main.py chart' to generate charts | 'python main.py export' to export data"
        return Panel(footer_text, style="dim", box=box.ROUNDED)

    def _create_progress_bar(self, value: float, width: int, color: str) -> str:
        """
        Create a simple progress bar.

        Args:
            value: Value between 0 and 1
            width: Width of the bar in characters
            color: Color name

        Returns:
            Formatted progress bar string
        """
        filled = int(value * width)
        empty = width - filled

        bar = "█" * filled + "░" * empty
        return f"[{color}]{bar}[/{color}]"

    def _get_indicator_signal(self, name: str, value: float) -> tuple:
        """
        Get signal interpretation for an indicator.

        Returns:
            Tuple of (signal_text, color)
        """
        if 'RSI' in name:
            if value > 70:
                return ("Overbought", "red")
            elif value < 30:
                return ("Oversold", "green")
            else:
                return ("Neutral", "yellow")

        elif 'VIX' in name:
            if value < 15:
                return ("Low Vol", "green")
            elif value < 20:
                return ("Normal", "yellow")
            elif value < 30:
                return ("Elevated", "yellow")
            else:
                return ("High Vol", "red")

        elif 'MACD' in name:
            if value > 0:
                return ("Bullish", "green")
            else:
                return ("Bearish", "red")

        elif 'ADX' in name:
            if value > 25:
                return ("Strong Trend", "green")
            else:
                return ("Weak Trend", "yellow")

        return ("—", "white")

    def _display_simple_status(
        self,
        regime: str,
        confidence: float,
        exposure: float,
        indicators: Dict[str, float]
    ) -> None:
        """
        Display simple text-based status (fallback when rich is not available).
        """
        print("\n" + "=" * 60)
        print("TQQQ MARKET REGIME DETECTION".center(60))
        print("=" * 60)

        print(f"\nCurrent Regime: {regime.upper()}")
        print(f"Confidence: {confidence * 100:.1f}%")
        print(f"Recommended TQQQ Exposure: {exposure * 100:.0f}%")

        print("\nKey Indicators:")
        print("-" * 60)
        for name, value in indicators.items():
            if value is not None:
                print(f"  {name:20s}: {value:>10.2f}")

        print("=" * 60 + "\n")


if __name__ == "__main__":
    # Example usage
    dashboard = RegimeDashboard()

    print(f"Dashboard available: {dashboard.is_available()}")

    # Sample data
    regime = 'bull'
    confidence = 0.85
    exposure = 1.0

    indicators = {
        'QQQ_price': 450.25,
        'SMA_50': 445.10,
        'SMA_200': 435.50,
        'VIX': 14.5,
        'RSI': 58.3,
        'MACD': 2.5,
        'ADX': 28.5,
    }

    price_data = {
        'QQQ': 450.25,
        'SPY': 485.50,
        'VIX': 14.5,
    }

    upcoming_events = [
        {'date': date.today() + timedelta(days=3), 'event_name': 'FOMC Meeting', 'importance': 'high'},
        {'date': date.today() + timedelta(days=10), 'event_name': 'CPI Release', 'importance': 'high'},
        {'date': date.today() + timedelta(days=15), 'event_name': 'NFP Report', 'importance': 'high'},
    ]

    regime_details = {
        'bull': {
            'rules_passed': 5,
            'total_rules': 6,
            'results': [
                ('QQQ_price > SMA_50', True),
                ('SMA_50 > SMA_200', True),
                ('VIX < 20', True),
                ('RSI > 40', True),
                ('RSI < 75', True),
                ('MACD > 0', True),
            ]
        }
    }

    dashboard.display_current_status(
        regime=regime,
        confidence=confidence,
        exposure=exposure,
        indicators=indicators,
        regime_details=regime_details,
        price_data=price_data,
        last_update=datetime.now(),
        upcoming_events=upcoming_events
    )
