# SPY 200SMA (+4%/-3%) TQQQ strategy — backtest (first pass)

Data: Yahoo Finance (^GSPC, ^NDX, QQQ, TQQQ adjusted closes) and FRED 3M T-bill (DTB3), through 2026-11-16.

* Signal = S&P 500 price index vs its 200-day SMA (same as unadjusted SPY on TradingView).
* TQQQ before 2010 = 3x daily Nasdaq-100 total return − 2×(T-bill + 1.0%) − 0.84% ER.
  Calibrated to real TQQQ 2010–2026: 39.6% vs 39.6% CAGR, 0.999 daily correlation.
* Signal at close t, trade at close t+1; 5 bps cost per trade; cash earns T-bills. No taxes.

| Script | What it does |
|---|---|
| `backtest.py` | data loading, synthetic TQQQ, strategy simulator |
| `compare.py` | strategy table for 1986 / 2000 / 2003 / 2010 starts |
| `deep.py` | drawdown episodes, trade list, entry/exit threshold grid |
| `now.py` | "buy today vs wait for +4% signal" in historically similar states |
| `chart.py` | `backtest.png` |
