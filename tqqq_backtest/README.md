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
| `engine.py` | general rule engine; compares rule variants decade by decade |
| `scalein.py` | ways for a new buyer to build a position from a state like today's |
| `chart2.py` | `tuning_scalein.png` |

## Round 2 findings
* **Tuned rule:** +4/-3 S&P signal, plus hold QQQ instead of TQQQ whenever Nasdaq-100
  20-day volatility is above 40% (switch back to TQQQ below 35%).
  Full period 27.9% CAGR / -64% max drawdown vs 26.8% / -81% for the base rule.
  Results are similar for any cap from 35% to 50%, and it helped every entry/exit pair tested.
* **Didn't help:** Nasdaq-based exits, 3-day confirmation, and the Reddit "bodyguard"
  (the sticky version fixes 2000 but costs the 1990s).
* **Scale-in:** thirds over 6 weeks gave up ~3 points of median 12-month return vs
  all-in, but cut the 10th-percentile outcome from -24% to -14%.
