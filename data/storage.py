"""
Database storage layer for TQQQ Market Regime Detection Framework.
Handles SQLite operations for market data, indicators, regimes, and events.
"""

import sqlite3
import pandas as pd
from datetime import datetime, date
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
import logging

logger = logging.getLogger(__name__)


class DatabaseStorage:
    """Manages SQLite database operations for the framework."""

    def __init__(self, db_path: str = "market_regime.db"):
        """
        Initialize database connection.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = None
        self._initialize_db()

    def _initialize_db(self) -> None:
        """Create database and tables if they don't exist."""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row

            # Read and execute schema
            schema_path = Path(__file__).parent / "schema.sql"
            with open(schema_path, 'r') as f:
                schema_sql = f.read()

            self.conn.executescript(schema_sql)
            self.conn.commit()
            logger.info(f"Database initialized at {self.db_path}")

        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise

    def close(self) -> None:
        """Close database connection."""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")

    # ==================== MARKET DATA OPERATIONS ====================

    def insert_market_data(self, ticker: str, df: pd.DataFrame) -> int:
        """
        Insert market data into database.

        Args:
            ticker: Stock ticker symbol
            df: DataFrame with columns: date, open, high, low, close, volume

        Returns:
            Number of rows inserted
        """
        if self.conn is None:
            raise RuntimeError("Database connection not initialized")

        try:
            rows_inserted = 0
            for idx, row in df.iterrows():
                try:
                    # Convert index to date if it's a datetime
                    row_date = idx if isinstance(idx, date) else idx.date()

                    self.conn.execute("""
                        INSERT OR REPLACE INTO market_data
                        (ticker, date, open, high, low, close, volume, adjusted_close)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        ticker,
                        row_date,
                        float(row.get('Open', row.get('open', 0))),
                        float(row.get('High', row.get('high', 0))),
                        float(row.get('Low', row.get('low', 0))),
                        float(row.get('Close', row.get('close', 0))),
                        int(row.get('Volume', row.get('volume', 0))),
                        float(row.get('Adj Close', row.get('adjusted_close', row.get('Close', row.get('close', 0)))))
                    ))
                    rows_inserted += 1
                except Exception as e:
                    logger.warning(f"Failed to insert row for {ticker} on {idx}: {e}")
                    continue

            self.conn.commit()
            logger.info(f"Inserted {rows_inserted} rows for {ticker}")
            return rows_inserted

        except Exception as e:
            logger.error(f"Failed to insert market data for {ticker}: {e}")
            self.conn.rollback()
            raise

    def get_market_data(
        self,
        ticker: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> pd.DataFrame:
        """
        Retrieve market data for a ticker.

        Args:
            ticker: Stock ticker symbol
            start_date: Start date for data range
            end_date: End date for data range

        Returns:
            DataFrame with market data
        """
        if self.conn is None:
            raise RuntimeError("Database connection not initialized")

        query = "SELECT date, open, high, low, close, volume, adjusted_close FROM market_data WHERE ticker = ?"
        params: List[Any] = [ticker]

        if start_date:
            query += " AND date >= ?"
            params.append(start_date)

        if end_date:
            query += " AND date <= ?"
            params.append(end_date)

        query += " ORDER BY date ASC"

        df = pd.read_sql_query(query, self.conn, params=params)
        if not df.empty:
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)

        return df

    def get_latest_date(self, ticker: str) -> Optional[date]:
        """Get the most recent date for which we have data for a ticker."""
        if self.conn is None:
            raise RuntimeError("Database connection not initialized")

        cursor = self.conn.execute(
            "SELECT MAX(date) as max_date FROM market_data WHERE ticker = ?",
            (ticker,)
        )
        result = cursor.fetchone()

        if result and result['max_date']:
            return datetime.strptime(result['max_date'], '%Y-%m-%d').date()
        return None

    # ==================== INDICATOR OPERATIONS ====================

    def insert_indicators(self, ticker: str, date_val: date, indicators: Dict[str, float]) -> int:
        """
        Insert calculated indicators for a specific date.

        Args:
            ticker: Stock ticker symbol
            date_val: Date for the indicators
            indicators: Dictionary of indicator_name: value pairs

        Returns:
            Number of indicators inserted
        """
        if self.conn is None:
            raise RuntimeError("Database connection not initialized")

        try:
            rows_inserted = 0
            for indicator_name, value in indicators.items():
                if pd.notna(value):  # Skip NaN values
                    self.conn.execute("""
                        INSERT OR REPLACE INTO indicators (ticker, date, indicator_name, value)
                        VALUES (?, ?, ?, ?)
                    """, (ticker, date_val, indicator_name, float(value)))
                    rows_inserted += 1

            self.conn.commit()
            return rows_inserted

        except Exception as e:
            logger.error(f"Failed to insert indicators for {ticker} on {date_val}: {e}")
            self.conn.rollback()
            raise

    def get_indicators(
        self,
        ticker: str,
        date_val: date,
        indicator_names: Optional[List[str]] = None
    ) -> Dict[str, float]:
        """
        Get indicator values for a specific ticker and date.

        Args:
            ticker: Stock ticker symbol
            date_val: Date to retrieve indicators for
            indicator_names: Optional list of specific indicators to retrieve

        Returns:
            Dictionary of indicator_name: value pairs
        """
        if self.conn is None:
            raise RuntimeError("Database connection not initialized")

        query = "SELECT indicator_name, value FROM indicators WHERE ticker = ? AND date = ?"
        params: List[Any] = [ticker, date_val]

        if indicator_names:
            placeholders = ','.join('?' * len(indicator_names))
            query += f" AND indicator_name IN ({placeholders})"
            params.extend(indicator_names)

        cursor = self.conn.execute(query, params)
        return {row['indicator_name']: row['value'] for row in cursor.fetchall()}

    def get_indicator_history(
        self,
        ticker: str,
        indicator_name: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> pd.DataFrame:
        """
        Get historical values for a specific indicator.

        Args:
            ticker: Stock ticker symbol
            indicator_name: Name of the indicator
            start_date: Start date for data range
            end_date: End date for data range

        Returns:
            DataFrame with date index and indicator values
        """
        if self.conn is None:
            raise RuntimeError("Database connection not initialized")

        query = """
            SELECT date, value
            FROM indicators
            WHERE ticker = ? AND indicator_name = ?
        """
        params: List[Any] = [ticker, indicator_name]

        if start_date:
            query += " AND date >= ?"
            params.append(start_date)

        if end_date:
            query += " AND date <= ?"
            params.append(end_date)

        query += " ORDER BY date ASC"

        df = pd.read_sql_query(query, self.conn, params=params)
        if not df.empty:
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)

        return df

    # ==================== REGIME OPERATIONS ====================

    def insert_regime(
        self,
        date_val: date,
        regime: str,
        confidence_score: float,
        exposure: float,
        rules_passed: int,
        total_rules: int
    ) -> None:
        """
        Insert or update regime classification for a date.

        Args:
            date_val: Date of the regime classification
            regime: Regime type ('bull', 'bear', 'choppy')
            confidence_score: Confidence score (0-1)
            exposure: Recommended TQQQ exposure (0-1)
            rules_passed: Number of rules that passed
            total_rules: Total number of rules evaluated
        """
        if self.conn is None:
            raise RuntimeError("Database connection not initialized")

        try:
            self.conn.execute("""
                INSERT OR REPLACE INTO regimes
                (date, regime, confidence_score, exposure_recommendation, rules_passed, total_rules)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (date_val, regime, confidence_score, exposure, rules_passed, total_rules))

            self.conn.commit()
            logger.info(f"Inserted regime '{regime}' for {date_val}")

        except Exception as e:
            logger.error(f"Failed to insert regime for {date_val}: {e}")
            self.conn.rollback()
            raise

    def get_current_regime(self) -> Optional[Dict[str, Any]]:
        """Get the most recent regime classification."""
        if self.conn is None:
            raise RuntimeError("Database connection not initialized")

        cursor = self.conn.execute("""
            SELECT date, regime, confidence_score, exposure_recommendation,
                   rules_passed, total_rules
            FROM regimes
            ORDER BY date DESC
            LIMIT 1
        """)

        row = cursor.fetchone()
        if row:
            return dict(row)
        return None

    def get_regime_history(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> pd.DataFrame:
        """
        Get historical regime classifications.

        Args:
            start_date: Start date for data range
            end_date: End date for data range

        Returns:
            DataFrame with regime history
        """
        if self.conn is None:
            raise RuntimeError("Database connection not initialized")

        query = """
            SELECT date, regime, confidence_score, exposure_recommendation,
                   rules_passed, total_rules
            FROM regimes
            WHERE 1=1
        """
        params: List[Any] = []

        if start_date:
            query += " AND date >= ?"
            params.append(start_date)

        if end_date:
            query += " AND date <= ?"
            params.append(end_date)

        query += " ORDER BY date ASC"

        df = pd.read_sql_query(query, self.conn, params=params)
        if not df.empty:
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)

        return df

    # ==================== ECONOMIC EVENTS OPERATIONS ====================

    def insert_economic_event(
        self,
        date_val: date,
        event_type: str,
        event_name: str,
        importance: str = 'medium',
        actual_value: Optional[float] = None,
        forecast_value: Optional[float] = None,
        previous_value: Optional[float] = None
    ) -> None:
        """Insert economic event into database."""
        if self.conn is None:
            raise RuntimeError("Database connection not initialized")

        try:
            self.conn.execute("""
                INSERT OR REPLACE INTO economic_events
                (date, event_type, event_name, importance, actual_value, forecast_value, previous_value)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (date_val, event_type, event_name, importance, actual_value, forecast_value, previous_value))

            self.conn.commit()

        except Exception as e:
            logger.error(f"Failed to insert economic event for {date_val}: {e}")
            self.conn.rollback()
            raise

    def get_upcoming_events(self, days_ahead: int = 7) -> List[Dict[str, Any]]:
        """Get upcoming economic events."""
        if self.conn is None:
            raise RuntimeError("Database connection not initialized")

        from datetime import timedelta
        end_date = date.today() + timedelta(days=days_ahead)

        cursor = self.conn.execute("""
            SELECT date, event_type, event_name, importance
            FROM economic_events
            WHERE date >= date('now') AND date <= ?
            ORDER BY date ASC
        """, (end_date,))

        return [dict(row) for row in cursor.fetchall()]

    # ==================== METADATA OPERATIONS ====================

    def set_metadata(self, key: str, value: str) -> None:
        """Set a metadata value."""
        if self.conn is None:
            raise RuntimeError("Database connection not initialized")

        self.conn.execute("""
            INSERT OR REPLACE INTO metadata (key, value, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        """, (key, value))
        self.conn.commit()

    def get_metadata(self, key: str) -> Optional[str]:
        """Get a metadata value."""
        if self.conn is None:
            raise RuntimeError("Database connection not initialized")

        cursor = self.conn.execute(
            "SELECT value FROM metadata WHERE key = ?",
            (key,)
        )
        result = cursor.fetchone()
        return result['value'] if result else None


# Context manager support
class DatabaseStorageContext(DatabaseStorage):
    """Database storage with context manager support."""

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False
