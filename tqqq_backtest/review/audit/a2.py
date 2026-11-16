import numpy as np, pandas as pd
from backtest import load, stats, TD
from engine import add_features, states, sim
df = add_features(load()).loc["1986":]
W = states(df, vol_cap=0.40)
for lag in (1,2):
    r = sim(df, W, lag=lag); eq=(1+r).cumprod(); dd=eq/eq.cummax()-1
    t=dd.idxmin(); print("lag",lag,"maxDD",round(dd.min(),3),"peak",eq[:t].idxmax().date(),"trough",t.date())
    for a,b in [("1987-09","1987-11"),("2000-01","2002-12"),("2008-01","2009-06"),("2020-02","2020-04"),("2022-01","2022-12")]:
        print(f"   {a}..{b} ret {((1+r[a:b]).prod()-1)*100:6.1f}")
s = pd.DataFrame(W, index=df.index, columns=list("TQC"))
print(df.loc["1987-10-13":"1987-10-21",["spx_dev","ndx_vol20","tqqq_ret"]].round(3).join(s.loc["1987-10-13":"1987-10-21"]))
# sensitivity of vol cap
for vc in (0.35,0.40,0.45,0.50):
    r=sim(df,states(df,vol_cap=vc)); s1=stats(r); r2=sim(df,states(df,vol_cap=vc),lag=2); s2=stats(r2)
    print(f"vc{vc} lag1 {s1['CAGR']*100:.1f}/{s1['MaxDD']*100:.0f} lag2 {s2['CAGR']*100:.1f}/{s2['MaxDD']*100:.0f}")
# ex-1987 subperiods
for a in ("1988","2000","2010"):
    for nm,kw in (("base",{}),("tuned",dict(vol_cap=0.4))):
        r=sim(df,states(df,**kw)).loc[a:]; s1=stats(r); print(a,nm,f"{s1['CAGR']*100:.1f}/{s1['MaxDD']*100:.0f}")
