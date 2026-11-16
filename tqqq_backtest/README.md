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
| `dashboard.py` | `dashboard.png`: entry/exit arrows + traffic-light board (run daily) |

## Round 3: indicator lights
Requiring extra "green lights" (MACD, Nasdaq above its 200SMA, low volatility) before entering
did **not** improve results: MACD costs 0.2-1.6 points of CAGR a year, and "all-in when all
lights are green" was worse than buying in thirds over 6 weeks (12-month median 34% vs 39%,
10th percentile -24% vs -14%). Rule lights = S&P vs 200SMA and Nasdaq volatility; the rest are context.

## Round 4: peer review (two review agents; scripts in review/)
* **Fixed a timing error:** the engine was filling at the same close that created the signal. The default
  is now a next-day close fill (`lag=2`). The tuned rule from 1986 goes from 27.9% / -64% to **23.8% / -81%**.
  Almost all of the gap is Black Monday 1987.
* Fixed look-ahead in now.py; Sharpe now subtracts T-bills.
* Walk-forward: picking settings from past data only would not have chosen the vol cap before 2000
  (-87% max drawdown). The vol cap never acted after 2000. Keep it as cheap insurance, but don't count on it.
* Bootstrap (resampled histories): median 22% CAGR, median max drawdown -73%, 25% chance of worse than -80%.
* Taxes cost about 6 points of CAGR in a taxable account; still about 8 points a year ahead of QQQ.
* Lower-risk variant: 50/50 TQQQ/QQQ (or 2x) with the same signals: ~20-21% CAGR / -47 to -61% drawdown.
* Known gap: scalein.py plans still trade at the signal close (same for every plan, so the comparison is fair).
