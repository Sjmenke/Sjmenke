from common import *
print(df.loc["1987-10-13":"1987-10-20", ["spx_dev","ndx_vol20"]].round(3).assign(tq=df.tqqq_ret.round(3)).to_string())
W = states(df, **TUNED)
for lag in [1,2]:
    r = sim(df,W,lag=lag); tab([row(r["1988":], f"lag{lag} 1988+"), row(r["1986":"1987"], f"lag{lag} 86-87")])
H = pd.DataFrame(W, index=df.index).shift(1).fillna(0); sr = df.spx.pct_change()
b = sr[(sr<-0.05)&(H[0]>0.5)]; print("SPX<-5% while in TQQQ:", b.round(3).to_dict(), (df.tqqq_ret[b.index]).round(3).tolist())
