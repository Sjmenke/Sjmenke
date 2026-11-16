from common import *
W = states(df, **TUNED); Wb = states(df, **BASE)
rows = []
for lag in [1,2]:
    e=(1+sim(df,W,lag=lag)).cumprod(); d=e/e.cummax()-1; print("lag",lag,"DD trough",d.idxmin().date(),"peak",e[:d.idxmin()].idxmax().date())
for lag in [1,2]:
    for c in [0.0005,0.001,0.0025]:
        rows.append(row(sim(df,W,lag=lag,cost=c), f"tuned lag{lag} {c*1e4:.0f}bp"))
rows.append(row(sim(df,Wb,lag=2,cost=0.0025), "base lag2 25bp"))
tab(rows)
sw = (np.abs(np.diff(W, axis=0)).sum(1) > 0).sum()/(len(df)/TD); print("trades/yr", round(sw,1))
# held weight on day t (decided t-1)
H = pd.DataFrame(W, index=df.index, columns=["L","Q","C"]).shift(1).fillna(0)
nr = df.ndx.pct_change(); sr = df.spx.pct_change()
big = sr[sr < -0.05].index
print("SPX days < -5%:", len(big), " in TQQQ:", int((H.L[big]>0.5).sum()), " in QQQ:", int((H.Q[big]>0.5).sum()))
big = nr[nr < -0.07].index
print("NDX days < -7%:", len(big), " in TQQQ:", int((H.L[big]>0.5).sum()), " dates:", [str(d.date()) for d in big[H.L[big]>0.5]])
print("frac days in TQQQ", round(H.L.mean(),2), "QQQ", round(H.Q.mean(),2))
# 1987 gap: was strategy in TQQQ on 1987-10-19?
print("1987-10-16..19 weights:\n", H.loc["1987-10-14":"1987-10-20"].to_string())
r = sim(df,W); print("worst strat days:", r.nsmallest(3).round(3).to_dict())
# hypothetical: -60% gap hit while in TQQQ at the equity peak
eq=(1+r).cumprod(); print("one -60% gap at random TQQQ day => CAGR", round(((eq.iloc[-1]*0.4)**(TD/len(r))-1)*100,1))
