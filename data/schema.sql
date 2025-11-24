-- TQQQ Market Regime Detection Framework Database Schema

-- Market data (OHLCV)
CREATE TABLE IF NOT EXISTS market_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT NOT NULL,
    date DATE NOT NULL,
    open REAL NOT NULL,
    high REAL NOT NULL,
    low REAL NOT NULL,
    close REAL NOT NULL,
    volume INTEGER NOT NULL,
    adjusted_close REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(ticker, date)
);

CREATE INDEX IF NOT EXISTS idx_market_data_ticker_date ON market_data(ticker, date);
CREATE INDEX IF NOT EXISTS idx_market_data_date ON market_data(date);

-- Calculated indicators
CREATE TABLE IF NOT EXISTS indicators (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT NOT NULL,
    date DATE NOT NULL,
    indicator_name TEXT NOT NULL,
    value REAL NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(ticker, date, indicator_name)
);

CREATE INDEX IF NOT EXISTS idx_indicators_ticker_date ON indicators(ticker, date);
CREATE INDEX IF NOT EXISTS idx_indicators_name ON indicators(indicator_name);

-- Regime classifications
CREATE TABLE IF NOT EXISTS regimes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE NOT NULL UNIQUE,
    regime TEXT NOT NULL CHECK(regime IN ('bull', 'bear', 'choppy')),
    confidence_score REAL NOT NULL,
    exposure_recommendation REAL NOT NULL CHECK(exposure_recommendation >= 0 AND exposure_recommendation <= 1),
    rules_passed INTEGER NOT NULL,
    total_rules INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_regimes_date ON regimes(date);
CREATE INDEX IF NOT EXISTS idx_regimes_regime ON regimes(regime);

-- Economic events
CREATE TABLE IF NOT EXISTS economic_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE NOT NULL,
    event_type TEXT NOT NULL,
    event_name TEXT NOT NULL,
    importance TEXT CHECK(importance IN ('high', 'medium', 'low')),
    actual_value REAL,
    forecast_value REAL,
    previous_value REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_economic_events_date ON economic_events(date);
CREATE INDEX IF NOT EXISTS idx_economic_events_type ON economic_events(event_type);

-- Metadata table for tracking data updates
CREATE TABLE IF NOT EXISTS metadata (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
