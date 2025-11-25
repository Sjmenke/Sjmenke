#!/usr/bin/env python3
"""
TQQQ Market Regime Detection Framework - Main CLI Interface

Commands:
    update      - Fetch latest data, calculate indicators, classify regime
    status      - Show current regime dashboard
    history     - Show regime history
    chart       - Generate and display charts
    export      - Export data to CSV
    init        - Initialize database and fetch historical data
"""

import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime, date, timedelta
from typing import Optional, Dict, Any
import yaml

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from data.storage import DatabaseStorage
from data.fetcher import DataFetcher, IncrementalDataFetcher
from indicators.trend import create_trend_indicators
from indicators.volatility import create_volatility_indicators
from indicators.momentum import create_momentum_indicators
from regime.classifier import RegimeClassifier
from regime.evaluator import ContextBuilder
from visualization.charts import RegimeChartGenerator
from visualization.dashboard import RegimeDashboard
from events.economic_calendar import EconomicCalendar

# Create necessary directories before logging setup
Path("logs").mkdir(exist_ok=True)
Path("outputs").mkdir(exist_ok=True)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/market_regime.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class MarketRegimeApp:
    """Main application class for TQQQ Market Regime Detection."""

    def __init__(self, config_dir: str = "config"):
        """
        Initialize application.

        Args:
            config_dir: Directory containing configuration files
        """
        self.config_dir = Path(config_dir)
        self.config = self._load_config()
        self.db = DatabaseStorage()
        self.fetcher = DataFetcher()
        self.classifier = RegimeClassifier()
        self.dashboard = RegimeDashboard()
        self.chart_generator = RegimeChartGenerator()

        # Initialize economic calendar if configured
        fred_key = self.config.get('data_sources', {}).get('fred_api', {}).get('api_key')
        if fred_key and fred_key != 'YOUR_FRED_API_KEY_HERE':
            self.calendar = EconomicCalendar(api_key=fred_key)
        else:
            self.calendar = EconomicCalendar()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration files."""
        config = {}

        # Load indicators config
        indicators_path = self.config_dir / 'indicators.yaml'
        if indicators_path.exists():
            with open(indicators_path, 'r') as f:
                config['indicators'] = yaml.safe_load(f)

        # Load data sources config
        sources_path = self.config_dir / 'data_sources.yaml'
        if sources_path.exists():
            with open(sources_path, 'r') as f:
                config['data_sources'] = yaml.safe_load(f)

        return config

    def _get_tickers(self) -> list:
        """Get list of tickers to track."""
        sources = self.config.get('data_sources', {})
        tickers_config = sources.get('tickers', {})

        tickers = []
        tickers.extend(tickers_config.get('primary', ['QQQ']))
        tickers.extend(tickers_config.get('indices', []))
        tickers.extend(tickers_config.get('volatility', []))
        tickers.extend(tickers_config.get('safe_havens', []))

        # Remove duplicates while preserving order
        return list(dict.fromkeys(tickers))

    def init(self, period: str = "2y") -> None:
        """
        Initialize database with historical data.

        Args:
            period: Period of historical data to fetch
        """
        logger.info("Initializing database with historical data...")

        tickers = self._get_tickers()
        logger.info(f"Fetching data for {len(tickers)} tickers: {', '.join(tickers)}")

        for ticker in tickers:
            try:
                logger.info(f"Fetching {ticker}...")
                data = self.fetcher.fetch_ticker_data(ticker, period=period)

                if not data.empty:
                    self.db.insert_market_data(ticker, data)
                    logger.info(f"✓ {ticker}: {len(data)} rows inserted")
                else:
                    logger.warning(f"✗ {ticker}: No data fetched")

            except Exception as e:
                logger.error(f"✗ {ticker}: Failed - {e}")

        # Set metadata
        self.db.set_metadata('last_init', datetime.now().isoformat())
        logger.info("Database initialization complete")

    def update(self) -> None:
        """Update data, calculate indicators, and classify regime."""
        logger.info("=" * 60)
        logger.info("Starting market data update...")
        logger.info("=" * 60)

        # Step 1: Update market data
        logger.info("\n[Step 1/3] Updating market data...")
        self._update_market_data()

        # Step 2: Calculate indicators
        logger.info("\n[Step 2/3] Calculating indicators...")
        self._calculate_indicators()

        # Step 3: Classify regime
        logger.info("\n[Step 3/3] Classifying regime...")
        self._classify_regime()

        # Update metadata
        self.db.set_metadata('last_update', datetime.now().isoformat())

        logger.info("\n" + "=" * 60)
        logger.info("Update complete!")
        logger.info("=" * 60)

    def _update_market_data(self) -> None:
        """Update market data for all tickers."""
        tickers = self._get_tickers()
        incremental_fetcher = IncrementalDataFetcher()

        for ticker in tickers:
            try:
                # Get last date we have data for
                last_date = self.db.get_latest_date(ticker)

                # Fetch new data
                data = incremental_fetcher.fetch_since_last_update(ticker, last_date)

                if not data.empty:
                    self.db.insert_market_data(ticker, data)
                    logger.info(f"✓ {ticker}: Updated with {len(data)} rows")
                else:
                    logger.info(f"○ {ticker}: No new data")

            except Exception as e:
                logger.error(f"✗ {ticker}: Update failed - {e}")

    def _calculate_indicators(self) -> None:
        """Calculate all indicators for QQQ and VIX."""
        indicator_config = self.config.get('indicators', {})

        # Get data
        qqq_data = self.db.get_market_data('QQQ')
        vix_data = self.db.get_market_data('^VIX')

        if qqq_data.empty:
            logger.error("No QQQ data available")
            return

        # Create indicators
        trend_indicators = create_trend_indicators(indicator_config.get('trend', {}))
        volatility_indicators = create_volatility_indicators(indicator_config.get('volatility', {}))
        momentum_indicators = create_momentum_indicators(indicator_config.get('momentum', {}))

        all_indicators = {**trend_indicators, **volatility_indicators, **momentum_indicators}

        # Calculate and store each indicator
        for ind_name, indicator in all_indicators.items():
            try:
                # Determine which data to use
                if 'VIX' in ind_name:
                    if vix_data.empty:
                        logger.warning(f"Skipping {ind_name} - no VIX data")
                        continue
                    data = vix_data
                    ticker = '^VIX'
                else:
                    data = qqq_data
                    ticker = 'QQQ'

                # Calculate indicator
                result = indicator.calculate(data)

                # Store results
                if result is not None:
                    # Check if result is a DataFrame or Series
                    import pandas as pd

                    if isinstance(result, pd.DataFrame):
                        # For DataFrames (like MACD, Bollinger Bands), store primary column
                        # Use first column as the main value
                        primary_column = result.columns[0]
                        for idx, row in result.iterrows():
                            value = row[primary_column]
                            if pd.notna(value):
                                self.db.insert_indicators(
                                    ticker,
                                    idx.date() if hasattr(idx, 'date') else idx,
                                    {ind_name: float(value)}
                                )
                    elif isinstance(result, pd.Series):
                        # For Series (most indicators)
                        for idx, value in result.items():
                            if pd.notna(value):
                                self.db.insert_indicators(
                                    ticker,
                                    idx.date() if hasattr(idx, 'date') else idx,
                                    {ind_name: float(value)}
                                )

                    logger.info(f"✓ {ind_name}: Calculated")

            except Exception as e:
                logger.error(f"✗ {ind_name}: Calculation failed - {e}")

    def _classify_regime(self) -> None:
        """Classify current market regime."""
        # Get latest data
        qqq_data = self.db.get_market_data('QQQ')
        if qqq_data.empty:
            logger.error("No QQQ data available for classification")
            return

        latest_date = qqq_data.index[-1].date()

        # Get latest prices
        qqq_price = qqq_data.iloc[-1]['close']

        # Get indicator values
        indicator_values = self.db.get_indicators('QQQ', latest_date)

        # Also get VIX indicators
        vix_indicators = self.db.get_indicators('^VIX', latest_date)
        indicator_values.update(vix_indicators)

        # Build context
        ticker_data = {'QQQ': qqq_data}
        context = ContextBuilder.build_context(ticker_data, indicator_values)

        # Classify
        regime, confidence, details = self.classifier.classify(context)

        # Get exposure recommendation
        conservative_mode = self.config.get('data_sources', {}).get('features', {}).get('conservative_mode', True)
        exposure = self.classifier.get_exposure_recommendation(regime, confidence, conservative_mode)

        # Store regime
        passed = details[regime]['rules_passed']
        total = details[regime]['total_rules']

        self.db.insert_regime(
            date_val=latest_date,
            regime=regime,
            confidence_score=confidence,
            exposure=exposure,
            rules_passed=passed,
            total_rules=total
        )

        logger.info(f"✓ Regime classified: {regime.upper()} (confidence: {confidence:.2%}, exposure: {exposure:.0%})")

    def status(self) -> None:
        """Display current regime status."""
        # Get current regime
        current_regime = self.db.get_current_regime()

        if not current_regime:
            print("No regime data available. Run 'python main.py update' first.")
            return

        regime = current_regime['regime']
        confidence = current_regime['confidence_score']
        exposure = current_regime['exposure_recommendation']
        regime_date = current_regime['date']

        # Get indicator values
        indicator_values = self.db.get_indicators('QQQ', regime_date)
        vix_indicators = self.db.get_indicators('^VIX', regime_date)
        indicator_values.update(vix_indicators)

        # Get latest prices
        qqq_data = self.db.get_market_data('QQQ')
        spy_data = self.db.get_market_data('SPY')
        vix_data = self.db.get_market_data('^VIX')

        price_data = {}
        if not qqq_data.empty:
            price_data['QQQ'] = qqq_data.iloc[-1]['close']
        if not spy_data.empty:
            price_data['SPY'] = spy_data.iloc[-1]['close']
        if not vix_data.empty:
            price_data['VIX'] = vix_data.iloc[-1]['close']

        # Get upcoming events
        upcoming_events = []
        if self.calendar.is_available():
            upcoming_events = self.calendar.get_major_events(end_date=date.today() + timedelta(days=30))
        else:
            # Fallback without API
            upcoming_events = self.calendar.get_major_events(end_date=date.today() + timedelta(days=30))

        # Get regime details
        ticker_data = {'QQQ': qqq_data}
        context = ContextBuilder.build_context(ticker_data, indicator_values)
        _, _, regime_details = self.classifier.classify(context)

        # Display dashboard
        last_update_str = self.db.get_metadata('last_update')
        last_update = datetime.fromisoformat(last_update_str) if last_update_str else None

        self.dashboard.display_current_status(
            regime=regime,
            confidence=confidence,
            exposure=exposure,
            indicators=indicator_values,
            regime_details=regime_details,
            price_data=price_data,
            last_update=last_update,
            upcoming_events=upcoming_events
        )

    def history(self, days: int = 90) -> None:
        """
        Display regime history.

        Args:
            days: Number of days to show
        """
        end_date = date.today()
        start_date = end_date - timedelta(days=days)

        regime_history = self.db.get_regime_history(start_date, end_date)

        if regime_history.empty:
            print("No regime history available.")
            return

        print(f"\nRegime History (Last {days} days)")
        print("=" * 80)
        print(f"{'Date':<12} {'Regime':<10} {'Confidence':<12} {'Exposure':<10} {'Rules Passed'}")
        print("-" * 80)

        for idx, row in regime_history.iterrows():
            date_str = idx.strftime('%Y-%m-%d')
            regime = row['regime'].upper()
            confidence = f"{row['confidence_score']:.1%}"
            exposure = f"{row['exposure_recommendation']:.0%}"
            rules = f"{row['rules_passed']}/{row['total_rules']}"

            print(f"{date_str:<12} {regime:<10} {confidence:<12} {exposure:<10} {rules}")

        print("=" * 80)

        # Calculate regime statistics
        regime_counts = regime_history['regime'].value_counts()
        print("\nRegime Distribution:")
        for regime, count in regime_counts.items():
            pct = count / len(regime_history) * 100
            print(f"  {regime.upper()}: {count} days ({pct:.1f}%)")

    def chart(self, output_dir: str = "outputs") -> None:
        """
        Generate charts.

        Args:
            output_dir: Directory to save charts
        """
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        logger.info("Generating charts...")

        # Get data
        qqq_data = self.db.get_market_data('QQQ')
        regime_history = self.db.get_regime_history()

        if qqq_data.empty:
            print("No data available for charting.")
            return

        # Get indicators
        indicator_data = {}
        for ind_name in ['SMA_50', 'SMA_200', 'RSI', 'MACD', 'VIX_LEVEL', 'VIX_MA']:
            if 'VIX' in ind_name:
                ind_df = self.db.get_indicator_history('^VIX', ind_name)
            else:
                ind_df = self.db.get_indicator_history('QQQ', ind_name)

            if not ind_df.empty:
                indicator_data[ind_name] = ind_df['value']

        # Generate overview chart
        overview_path = output_path / "regime_overview.png"
        self.chart_generator.create_regime_overview(
            qqq_data,
            indicator_data,
            regime_history,
            save_path=str(overview_path)
        )
        print(f"✓ Regime overview chart: {overview_path}")

        # Generate timeline
        if not regime_history.empty:
            timeline_path = output_path / "regime_timeline.png"
            self.chart_generator.create_regime_timeline(
                regime_history,
                save_path=str(timeline_path)
            )
            print(f"✓ Regime timeline: {timeline_path}")

            # Generate exposure chart
            exposure_path = output_path / "exposure_recommendation.png"
            self.chart_generator.create_exposure_chart(
                regime_history,
                save_path=str(exposure_path)
            )
            print(f"✓ Exposure recommendation chart: {exposure_path}")

        logger.info("Chart generation complete")

    def export(self, output_dir: str = "outputs") -> None:
        """
        Export data to CSV files.

        Args:
            output_dir: Directory to save CSV files
        """
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        logger.info("Exporting data to CSV...")

        # Export regime history
        regime_history = self.db.get_regime_history()
        if not regime_history.empty:
            regime_path = output_path / "regime_history.csv"
            regime_history.to_csv(regime_path)
            print(f"✓ Regime history: {regime_path}")

        # Export market data
        for ticker in ['QQQ', 'SPY', '^VIX']:
            data = self.db.get_market_data(ticker)
            if not data.empty:
                ticker_clean = ticker.replace('^', '')
                data_path = output_path / f"{ticker_clean}_data.csv"
                data.to_csv(data_path)
                print(f"✓ {ticker} data: {data_path}")

        logger.info("Export complete")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='TQQQ Market Regime Detection Framework',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Init command
    init_parser = subparsers.add_parser('init', help='Initialize database with historical data')
    init_parser.add_argument('--period', default='2y', help='Historical period to fetch (default: 2y)')

    # Update command
    subparsers.add_parser('update', help='Update data and classify regime')

    # Status command
    subparsers.add_parser('status', help='Show current regime status')

    # History command
    history_parser = subparsers.add_parser('history', help='Show regime history')
    history_parser.add_argument('--days', type=int, default=90, help='Number of days to show (default: 90)')

    # Chart command
    chart_parser = subparsers.add_parser('chart', help='Generate charts')
    chart_parser.add_argument('--output', default='outputs', help='Output directory (default: outputs)')

    # Export command
    export_parser = subparsers.add_parser('export', help='Export data to CSV')
    export_parser.add_argument('--output', default='outputs', help='Output directory (default: outputs)')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Create app
    app = MarketRegimeApp()

    # Execute command
    try:
        if args.command == 'init':
            app.init(period=args.period)

        elif args.command == 'update':
            app.update()

        elif args.command == 'status':
            app.status()

        elif args.command == 'history':
            app.history(days=args.days)

        elif args.command == 'chart':
            app.chart(output_dir=args.output)

        elif args.command == 'export':
            app.export(output_dir=args.output)

    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        sys.exit(0)

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        sys.exit(1)

    finally:
        app.db.close()


if __name__ == '__main__':
    main()
