import numpy as np, pandas as pd
from backtest import load, stats, TD
from engine import add_features, states, sim
p = pd.read_csv("data/prices.csv", index_col=0, parse_dates=True)
print("first valid", {c: p[c].first_valid_index().date() for c in p})
print("NaN rows gspc/ndx after 1986:", p.loc["1986":,["^GSPC","^NDX"]].isna().sum().to_dict())
df = add_features(load()).loc["1986":]
print(df.index[0], df.index[-1], len(df))
def show(r, n):
    s = stats(r); rf = df.cash_ret.loc[r.index]
    ex = r - rf; sh = ex.mean()*TD/(ex.std()*np.sqrt(TD))
    print(f"{n:30s} CAGR {s['CAGR']*100:5.1f} DD {s['MaxDD']*100:5.0f} Sharpe {s['Sharpe']:.2f} exSharpe {sh:.2f}")
for lag in (1,2):
    show(sim(df, states(df), lag=lag), f"base lag{lag}")
    show(sim(df, states(df, vol_cap=0.40), lag=lag), f"tuned lag{lag}")
show(df.qqq_ret, "QQQ B&H")
show(sim(df, states(df, vol_cap=0.40), cost=0.0020), "tuned cost20bp")
# synthetic tracking
m = df.tqqq_real.notna() & df.index.to_series().gt("2010-02-12")
for a,b in [("2010","2014"),("2015","2019"),("2020","2022"),("2023","2026"),("2010","2026")]:
    s = df.loc[a:b][m.loc[a:b]]
    yr = len(s)/TD
    cr = (1+s.tqqq_real).prod()**(1/yr)-1; cs = (1+s.tqqq_syn).prod()**(1/yr)-1
    te = (s.tqqq_real - s.tqqq_syn).std()*np.sqrt(TD)
    print(f"{a}-{b} real {cr*100:6.1f} syn {cs*100:6.1f} diff {(cs-cr)*100:+.2f}/yr TE {te*100:.1f}%")
print("min syn daily", df.tqqq_syn.min(), df.tqqq_syn.idxmin().date())
print("largest NDX daily moves pre-99:", df.loc[:"1999","ndx"].pct_change().abs().nlargest(5).round(3).to_dict())
