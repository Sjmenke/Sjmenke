"""
Economic calendar integration for TQQQ Market Regime Detection Framework.
Fetches economic events and indicators using FRED API.
"""

from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional
import logging

try:
    from fredapi import Fred
    FRED_AVAILABLE = True
except ImportError:
    FRED_AVAILABLE = False
    logging.warning("fredapi not installed. Economic calendar features will be limited.")

logger = logging.getLogger(__name__)


class EconomicCalendar:
    """
    Manages economic events and data from FRED (Federal Reserve Economic Data).
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize economic calendar.

        Args:
            api_key: FRED API key (get free key from https://fred.stlouisfed.org/)
        """
        self.api_key = api_key
        self.fred = None

        if api_key and FRED_AVAILABLE:
            try:
                self.fred = Fred(api_key=api_key)
                logger.info("FRED API initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize FRED API: {e}")
        elif not FRED_AVAILABLE:
            logger.warning("fredapi package not installed. Install with: pip install fredapi")
        else:
            logger.warning("No FRED API key provided. Economic calendar features disabled.")

    def is_available(self) -> bool:
        """Check if FRED API is available."""
        return self.fred is not None

    def get_series_data(
        self,
        series_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Optional[Any]:
        """
        Get economic data series from FRED.

        Args:
            series_id: FRED series ID (e.g., 'DFF' for Federal Funds Rate)
            start_date: Start date for data
            end_date: End date for data

        Returns:
            pandas Series with the data or None if unavailable
        """
        if not self.is_available():
            logger.warning("FRED API not available")
            return None

        try:
            data = self.fred.get_series(
                series_id,
                observation_start=start_date,
                observation_end=end_date
            )
            logger.info(f"Fetched {len(data)} data points for series {series_id}")
            return data

        except Exception as e:
            logger.error(f"Failed to fetch series {series_id}: {e}")
            return None

    def get_latest_value(self, series_id: str) -> Optional[float]:
        """
        Get the most recent value for a series.

        Args:
            series_id: FRED series ID

        Returns:
            Latest value or None if unavailable
        """
        if not self.is_available():
            return None

        try:
            # Get last 30 days of data to ensure we have the latest
            end_date = date.today()
            start_date = end_date - timedelta(days=30)

            data = self.get_series_data(series_id, start_date, end_date)

            if data is not None and not data.empty:
                latest = data.iloc[-1]
                logger.info(f"Latest value for {series_id}: {latest}")
                return float(latest)

            return None

        except Exception as e:
            logger.error(f"Failed to get latest value for {series_id}: {e}")
            return None

    def get_economic_indicators(self) -> Dict[str, Optional[float]]:
        """
        Get current values for key economic indicators.

        Returns:
            Dictionary mapping indicator name to current value
        """
        indicators = {
            'federal_funds_rate': 'DFF',
            'cpi': 'CPIAUCSL',
            'unemployment_rate': 'UNRATE',
            '10y_treasury_yield': 'DGS10',
            '2y_treasury_yield': 'DGS2',
        }

        results = {}

        for name, series_id in indicators.items():
            value = self.get_latest_value(series_id)
            results[name] = value

        # Calculate yield curve (10Y - 2Y)
        if results['10y_treasury_yield'] and results['2y_treasury_yield']:
            results['yield_curve_spread'] = (
                results['10y_treasury_yield'] - results['2y_treasury_yield']
            )
        else:
            results['yield_curve_spread'] = None

        return results

    def get_upcoming_fomc_meetings(self) -> List[date]:
        """
        Get upcoming FOMC meeting dates.

        Note: FOMC meeting dates are not available via FRED API.
        This returns a predefined list that should be updated periodically.

        Returns:
            List of FOMC meeting dates
        """
        # 2024-2025 FOMC meeting dates (update as needed)
        # Source: https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm
        fomc_dates = [
            date(2024, 12, 18),
            date(2025, 1, 29),
            date(2025, 3, 19),
            date(2025, 5, 7),
            date(2025, 6, 18),
            date(2025, 7, 30),
            date(2025, 9, 17),
            date(2025, 11, 5),
            date(2025, 12, 17),
        ]

        # Filter to future dates only
        today = date.today()
        upcoming = [d for d in fomc_dates if d >= today]

        return upcoming

    def get_next_fomc_meeting(self) -> Optional[date]:
        """
        Get the next FOMC meeting date.

        Returns:
            Date of next FOMC meeting or None
        """
        upcoming = self.get_upcoming_fomc_meetings()
        return upcoming[0] if upcoming else None

    def days_until_fomc(self) -> Optional[int]:
        """
        Get number of days until next FOMC meeting.

        Returns:
            Number of days or None if no upcoming meeting
        """
        next_meeting = self.get_next_fomc_meeting()
        if next_meeting:
            return (next_meeting - date.today()).days
        return None

    def is_fomc_week(self, check_date: Optional[date] = None) -> bool:
        """
        Check if a date is within 3 days of an FOMC meeting.

        Args:
            check_date: Date to check (defaults to today)

        Returns:
            True if within FOMC week
        """
        if check_date is None:
            check_date = date.today()

        upcoming = self.get_upcoming_fomc_meetings()

        for fomc_date in upcoming:
            days_diff = abs((fomc_date - check_date).days)
            if days_diff <= 3:
                return True

        return False

    def get_major_events(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[Dict[str, Any]]:
        """
        Get major economic events in a date range.

        Args:
            start_date: Start date (defaults to today)
            end_date: End date (defaults to 30 days from start)

        Returns:
            List of event dictionaries
        """
        if start_date is None:
            start_date = date.today()

        if end_date is None:
            end_date = start_date + timedelta(days=30)

        events = []

        # FOMC meetings
        fomc_dates = self.get_upcoming_fomc_meetings()
        for fomc_date in fomc_dates:
            if start_date <= fomc_date <= end_date:
                events.append({
                    'date': fomc_date,
                    'event_type': 'FOMC',
                    'event_name': 'FOMC Meeting',
                    'importance': 'high',
                    'description': 'Federal Reserve policy decision'
                })

        # CPI releases (typically mid-month)
        # Generate estimated CPI release dates
        current = start_date.replace(day=1)
        while current <= end_date:
            # CPI typically released around 13th of each month
            cpi_date = current.replace(day=13)
            if start_date <= cpi_date <= end_date:
                events.append({
                    'date': cpi_date,
                    'event_type': 'CPI',
                    'event_name': 'Consumer Price Index Release',
                    'importance': 'high',
                    'description': 'Inflation data'
                })

            # Move to next month
            if current.month == 12:
                current = current.replace(year=current.year + 1, month=1)
            else:
                current = current.replace(month=current.month + 1)

        # Non-Farm Payrolls (first Friday of each month)
        current = start_date.replace(day=1)
        while current <= end_date:
            # Find first Friday
            while current.weekday() != 4:  # 4 = Friday
                current += timedelta(days=1)

            if start_date <= current <= end_date:
                events.append({
                    'date': current,
                    'event_type': 'NFP',
                    'event_name': 'Non-Farm Payrolls',
                    'importance': 'high',
                    'description': 'Monthly jobs report'
                })

            # Move to next month
            if current.month == 12:
                current = date(current.year + 1, 1, 1)
            else:
                current = current.replace(month=current.month + 1, day=1)

        # Sort events by date
        events.sort(key=lambda x: x['date'])

        return events


class EconomicIndicatorTracker:
    """
    Tracks economic indicators and their changes over time.
    """

    def __init__(self, calendar: EconomicCalendar):
        """
        Initialize tracker.

        Args:
            calendar: EconomicCalendar instance
        """
        self.calendar = calendar

    def get_macro_regime(self) -> Dict[str, Any]:
        """
        Determine macroeconomic regime based on indicators.

        Returns:
            Dictionary with macro regime assessment
        """
        if not self.calendar.is_available():
            return {
                'regime': 'unknown',
                'reason': 'Economic data unavailable'
            }

        indicators = self.calendar.get_economic_indicators()

        # Simple macro regime classification
        fed_funds = indicators.get('federal_funds_rate')
        yield_curve = indicators.get('yield_curve_spread')
        unemployment = indicators.get('unemployment_rate')

        regime = 'neutral'
        factors = []

        # Inverted yield curve often precedes recession
        if yield_curve is not None and yield_curve < 0:
            regime = 'risk_off'
            factors.append('Inverted yield curve')

        # High unemployment
        if unemployment is not None and unemployment > 5.0:
            if regime != 'risk_off':
                regime = 'risk_off'
            factors.append('Elevated unemployment')

        # Rising rates environment
        if fed_funds is not None and fed_funds > 4.0:
            factors.append('High interest rates')

        return {
            'regime': regime,
            'factors': factors,
            'indicators': indicators
        }


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)

    # Initialize (without API key for demo)
    calendar = EconomicCalendar()

    print(f"FRED API available: {calendar.is_available()}")

    # Get upcoming FOMC meetings
    fomc_meetings = calendar.get_upcoming_fomc_meetings()
    print(f"\nUpcoming FOMC meetings: {len(fomc_meetings)}")
    for meeting in fomc_meetings[:3]:
        print(f"  {meeting}")

    # Check if in FOMC week
    print(f"\nIn FOMC week: {calendar.is_fomc_week()}")

    # Get major events
    events = calendar.get_major_events(end_date=date.today() + timedelta(days=60))
    print(f"\nMajor events in next 60 days: {len(events)}")
    for event in events[:5]:
        print(f"  {event['date']}: {event['event_name']} ({event['importance']})")

    print("\nNote: To enable full economic calendar features:")
    print("1. Get free API key from https://fred.stlouisfed.org/")
    print("2. Install fredapi: pip install fredapi")
    print("3. Set API key in config/data_sources.yaml")
