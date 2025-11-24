# TQQQ Market Regime Detection Framework

A comprehensive, modular Python framework for detecting market regimes and generating TQQQ (3x leveraged Nasdaq-100 ETF) exposure recommendations based on technical indicators and market conditions.

## 🎯 Features

- **Automated Market Regime Classification**: Classifies markets into Bull, Bear, or Choppy regimes
- **Multiple Technical Indicators**: SMA, EMA, ADX, RSI, MACD, ROC, ATR, Bollinger Bands, VIX analysis
- **Configurable Rule Engine**: Define custom regime rules via YAML configuration
- **Economic Calendar Integration**: Track FOMC meetings, CPI releases, NFP reports
- **Rich Terminal Dashboard**: Beautiful terminal UI showing current regime status
- **Professional Charts**: Generate matplotlib-based analysis charts
- **SQLite Database**: Persistent storage for historical data and analysis
- **Backtesting Ready**: Clean architecture ready for historical backtesting
- **Modular Design**: Easy to extend with new indicators or regime rules

## 📋 Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Usage](#usage)
- [Configuration](#configuration)
- [Architecture](#architecture)
- [Indicators](#indicators)
- [Regime Classification](#regime-classification)
- [Advanced Usage](#advanced-usage)

## 🚀 Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Setup

1. **Clone or download this repository**

```bash
cd /path/to/Sjmenke
```

2. **Install dependencies**

```bash
pip install -r requirements.txt
```

3. **(Optional) Set up FRED API for economic calendar**

Get a free API key from [FRED](https://fred.stlouisfed.org/docs/api/api_key.html), then update `config/data_sources.yaml`:

```yaml
fred_api:
  api_key: "YOUR_FRED_API_KEY_HERE"
```

4. **Initialize the database**

```bash
python main.py init
```

This will create the SQLite database and fetch 2 years of historical data.

## 🎬 Quick Start

### 1. Initialize Database

```bash
python main.py init --period 2y
```

### 2. Update Data and Classify Regime

```bash
python main.py update
```

### 3. View Current Status

```bash
python main.py status
```

### 4. Generate Charts

```bash
python main.py chart
```

## 📖 Usage

### Commands

- `init` - Initialize database with historical data
- `update` - Update data, calculate indicators, classify regime
- `status` - Display current regime dashboard
- `history` - View regime history
- `chart` - Generate charts
- `export` - Export data to CSV

**Example workflows**:

```bash
# Daily update
python main.py update && python main.py status

# Weekly analysis
python main.py history --days 90
python main.py chart

# Export for analysis
python main.py export
```

## ⚙️ Configuration

### Indicator Configuration (`config/indicators.yaml`)

```yaml
trend:
  sma_short: 50
  sma_long: 200
  adx_period: 14

volatility:
  vix_low_threshold: 15
  vix_high_threshold: 25

momentum:
  rsi_period: 14
  macd_fast: 12
  macd_slow: 26
```

### Regime Rules (`config/regime_rules.yaml`)

```yaml
bull:
  conditions:
    - "QQQ_price > SMA_50"
    - "SMA_50 > SMA_200"
    - "VIX < 20"
    - "RSI > 40"
    - "MACD > 0"
  exposure: 1.0
  strategy: "all_must_pass"
```

## 🏗️ Architecture

```
Sjmenke/
├── data/                    # Data fetching and storage
├── indicators/             # Technical indicators
├── regime/                 # Regime classification
├── events/                 # Economic calendar
├── visualization/          # Charts and dashboard
├── config/                 # Configuration files
├── outputs/                # Generated files
└── main.py                 # CLI interface
```

## 📊 Indicators

### Trend
- SMA (50, 200), EMA, ADX, Price Position

### Volatility
- VIX, ATR, Bollinger Bands, Historical Volatility

### Momentum
- RSI, MACD, ROC, Stochastic

## 🎯 Regime Classification

- **Bull**: 100% TQQQ exposure (favorable conditions)
- **Bear**: 0% TQQQ exposure (unfavorable conditions)
- **Choppy**: 25% TQQQ exposure (mixed signals)

Classification based on configurable rules evaluating:
- Trend direction and strength
- Volatility levels
- Momentum indicators

## 🔧 Advanced Usage

### Custom Indicators

```python
from indicators.base import BaseIndicator, register_indicator

@register_indicator('my_indicator')
class MyIndicator(BaseIndicator):
    def calculate(self, data):
        return result
```

### Programmatic Access

```python
from main import MarketRegimeApp

app = MarketRegimeApp()
app.update()

regime = app.db.get_current_regime()
print(f"Current: {regime['regime']}")
```

## ⚠️ Disclaimer

**Educational and research purposes only. Not financial advice.**

- Leveraged ETFs carry significant risk
- Past performance ≠ future results
- Consult a financial advisor before investing

## 🐛 Troubleshooting

**Missing dependencies**:
```bash
pip install -r requirements.txt
```

**VIX data issues**: Symbol is `^VIX` in Yahoo Finance

**Charts not showing**: Install matplotlib and system graphics libraries

## 📝 Future Enhancements

- Backtesting engine
- Machine learning classification
- Web dashboard
- Portfolio allocation
- Risk metrics

---

**Built with**: pandas, yfinance, matplotlib, rich

**Happy Trading! 📈**
