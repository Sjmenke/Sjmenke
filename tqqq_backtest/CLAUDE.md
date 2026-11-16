# Chart conventions for this project (user preferences)

Apply to every chart produced here:

1. **Colorblind-safe.** Okabe-Ito palette only (#000000, #E69F00, #56B4E9, #009E73,
   #F0E442, #0072B2, #D55E00, #CC79A7, grey #999999). Never rely on color alone:
   give each series a distinct line style or marker as well.
2. **Entry/exit arrows** on price charts: BUY = up arrow, green #009E73, label with date;
   SELL = down arrow, vermillion #D55E00; partial de-lever (e.g. TQQQ→QQQ) = blue #0072B2.
   Shade the background by what the strategy holds.
3. **Traffic lights** for every criterion: GO #009E73 ✓, WAIT #F0E442 !, STOP #D55E00 ✕
   (the symbol is always drawn inside the light). Show a timeline strip per criterion and
   a "TODAY" board. Mark lights as ● rule (backtested, drives decisions) or ○ context (info only).
   Only promote a light to "rule" after a backtest shows that requiring it helps.

`dashboard.py` is the reference implementation; run `python3 dashboard.py [start-date]`.
