import pandas as pd, numpy as np
from backtest import *
df = load()
d = df.loc["1986":]
r, W = run(d, mode="cash")
eq = (1+r).cumprod()
# worst drawdown episodes
dd = eq/eq.cummax()-1
print("Worst drawdowns (+4/-3 TQQQ/cash):")
seen=[]
for t in dd.sort_values().index:
    if any(abs((t-s).days)<400 for s in seen): continue
    peak = eq[:t].idxmax(); seen.append(t)
    print(f"  {peak.date()} -> {t.date()}  {dd[t]*100:6.1f}%")
    if len(seen)==6: break
# trades
st = (W.tqqq>0.5).astype(int); ch = st.diff().fillna(0)
ents = st.index[ch==1]; exs = st.index[ch==-1]
print(f"\nTrades since 1986: {len(ents)} entries, ~{len(ents)/40.9:.1f}/yr; time in TQQQ {st.mean()*100:.0f}%")
tr=[]
for e in ents:
    x = exs[exs>e]; x = x[0] if len(x) else d.index[-1]
    tr.append(((1+r[e:x].iloc[1:]).prod()-1, e, x))
tr = pd.DataFrame(tr, columns=["ret","in","out"])
print(f"Win rate {(tr.ret>0).mean()*100:.0f}%, median trade {tr.ret.median()*100:.1f}%, worst {tr.ret.min()*100:.1f}%, best {tr.ret.max()*100:.0f}%")
print("Worst 6 trades:"); print(tr.sort_values("ret").head(6).assign(ret=lambda x:(x.ret*100).round(1)).to_string(index=False))
# 1987 crash day
print("\n1987-10-19 TQQQ synthetic day:", round(d.loc['1987-10-19','tqqq_ret']*100,1), "% ; in market?", W.loc['1987-10-19','tqqq'])
# sensitivity grid
print("\nCAGR % / MaxDD % grid (TQQQ/cash, 1986-now) rows=entry, cols=exit")
ents_=[0,0.01,0.02,0.03,0.04,0.05,0.06]; exits=[0,0.01,0.02,0.03,0.04,0.05]
g=pd.DataFrame(index=ents_,columns=exits)
for a in ents_:
    for b in exits:
        s=stats(run(d,entry=a,exit_=b)[0]); g.loc[a,b]=f"{s['CAGR']*100:.1f}/{s['MaxDD']*100:.0f}"
print(g.to_string())
g2=pd.DataFrame(index=ents_,columns=exits)
for a in ents_:
    for b in exits:
        s=stats(run(df.loc['2010':],entry=a,exit_=b)[0]); g2.loc[a,b]=f"{s['CAGR']*100:.1f}/{s['MaxDD']*100:.0f}"
print("\nSame grid, 2010-now (real TQQQ):"); print(g2.to_string())
