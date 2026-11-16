import pandas as pd, numpy as np
from backtest import *
df = load()
S = {
 "QQQ buy&hold":            None,
 "TQQQ buy&hold":           None,
 "SPY 200SMA 0/0 TQQQ/cash": dict(entry=0, exit_=0, mode="cash"),
 "+4/-3 TQQQ/cash":         dict(mode="cash"),
 "+4/-3 TQQQ/QQQ":          dict(mode="qqq"),
 "+4/-3 TQQQ/DCA-QQQ":      dict(mode="dca"),
 "+4/-3 DCA + bodyguard (Reddit full)": dict(mode="dca", bodyguard=True),
 "+4/-3 cash + bodyguard":  dict(mode="cash", bodyguard=True),
}
def go(start):
    d = df.loc[start:]
    rows = []
    for k, v in S.items():
        if k == "QQQ buy&hold": r = d.qqq_ret
        elif k == "TQQQ buy&hold": r = d.tqqq_ret
        else: r, W = run(d, **v)
        rows.append(stats(r, k))
    t = pd.DataFrame(rows).set_index("name")
    for c in ["CAGR","MaxDD","Vol"]: t[c] = (t[c]*100).round(1)
    t["Final"] = t["Final"].round(0); t[["Sharpe","Calmar"]] = t[["Sharpe","Calmar"]].round(2)
    print(f"\n=== {start} -> {d.index[-1].date()} ($1 grows to 'Final') ==="); print(t.to_string())
for s in ["1986-01-01","2000-03-01","2003-01-01","2010-02-12"]: go(s)
