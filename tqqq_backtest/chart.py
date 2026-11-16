import pandas as pd, numpy as np, matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from backtest import *
df=load(); p=pd.read_csv("data/prices.csv",index_col=0,parse_dates=True)
fig,ax=plt.subplots(3,1,figsize=(11,13),gridspec_kw={"height_ratios":[3,3,2]})
C={"QQQ buy&hold":"#888","TQQQ buy&hold":"#c33","+4/-3 TQQQ/cash":"#1f6fd1","+4/-3 DCA + bodyguard (Reddit)":"#2a9d55"}
for a,start in zip(ax[:2],["1986","2003"]):
    d=df.loc[start:]
    S={"QQQ buy&hold":d.qqq_ret,"TQQQ buy&hold":d.tqqq_ret,
       "+4/-3 TQQQ/cash":run(d,mode="cash")[0],"+4/-3 DCA + bodyguard (Reddit)":run(d,mode="dca",bodyguard=True)[0]}
    for k,r in S.items():
        s=stats(r); a.plot((1+r).cumprod(),color=C[k],lw=1.4,label=f"{k}  CAGR {s['CAGR']*100:.1f}%  MaxDD {s['MaxDD']*100:.0f}%")
    a.set_yscale("log"); a.set_title(f"Growth of $1 from {start} (log scale; TQQQ synthetic before 2010)"); a.legend(fontsize=9,loc="upper left"); a.grid(alpha=.3)
d=df.loc["2025-06":]
a=ax[2]; a.plot(d.spx,color="k",lw=1.2,label="S&P 500"); a.plot(d.spx_sma,color="m",label="200 SMA")
a.plot(d.spx_sma*1.04,"g--",lw=1,label="+4% entry"); a.plot(d.spx_sma*0.97,"r--",lw=1,label="-3% exit")
a.set_title(f"Signal today ({d.index[-1].date()}): S&P {d.spx_dev.iloc[-1]*100:+.1f}% vs 200SMA — in the hold zone"); a.legend(fontsize=9); a.grid(alpha=.3)
plt.tight_layout(); plt.savefig("backtest.png",dpi=110)
