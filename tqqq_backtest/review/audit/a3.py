import numpy as np, pandas as pd, sys
from engine import add_features, states
from backtest import load
import scalein as S
H=S.H
def run(lag):
    df = add_features(load())
    tq = (1 + df.tqqq_ret).cumprod()
    df["tq_dev"] = tq / tq.rolling(200).mean() - 1
    df = df.dropna(subset=["tq_dev"]).loc["1987":]
    df["lights"] = (df.ndx_dev > 0) & (df.ndx_vol20 < 0.35) & (df.spx_macd > df.spx_macd_sig)
    cond = (df.spx_dev.between(-0.03, 0.04) & df.ndx_dev.between(-0.06, 0.01) & df.tq_dev.between(-0.25, -0.10))
    sig = df.copy()
    if lag:
        for c in ["spx_dev","ndx_dev","ndx_vol20","lights"]: sig[c]=df[c].shift(lag)
        sig["lights"]=sig["lights"].fillna(False).astype(bool)
    idx = [i for i in range(len(df)) if cond.iloc[i] and i + H < len(df)][::2]
    out=[]
    for i in idx:
        seg = sig.iloc[i:i+H+1]
        sw = states(seg, vol_cap=0.40, start_in=True)
        for name,p in S.PLANS.items():
            eq = S.plan_sim(seg,p,sw)
            out.append(dict(date=df.index[i],plan=name,r12=eq[252]-1,r24=eq[504]-1,worst12=eq[:253].min()-1))
    R=pd.DataFrame(out)
    ds=pd.Series(sorted(R.date.unique())); ep=(ds.diff().dt.days.fillna(999)>60).cumsum()
    R["ep"]=R.date.map(dict(zip(ds,ep))); R["yr"]=R.date.dt.year
    print(f"lag{lag}: start days {R.date.nunique()} episodes {R.ep.nunique()} years {R.groupby('ep').yr.first().tolist()}")
    E=R.groupby(["plan","ep"])[["r12","r24","worst12"]].median().groupby("plan")
    g=R.groupby("plan")
    print(pd.DataFrame({"12med":g.r12.median()*100,"12p10":g.r12.quantile(.1)*100,"24med":g.r24.median()*100,
        "dipmed":g.worst12.median()*100,"EP12med":E.r12.median()*100,"EP24med":E.r24.median()*100,"EPdipworst":E.worst12.min()*100}).round(1).to_string())
    return R
R=run(0); run(1)
# per-episode table for key plans
piv=R.groupby(["ep","plan"]).r24.median().unstack()[["1 All-in TQQQ now","2 Wait for +4% signal","4 Thirds by time (0/3wk/6wk)"]]
print((piv*100).round(0).to_string())
