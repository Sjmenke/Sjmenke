import pandas as pd, numpy as np
from backtest import *
df = load()
tq_px = (1+df.tqqq_ret).cumprod(); df["tq_dev"] = tq_px/tq_px.rolling(200).mean()-1
df = df.dropna(subset=["tq_dev"])
d = df.loc["1987":]
# today-like state: SPX between -3% and +4% of SMA (hysteresis zone), NDX within -6..+1% of SMA,
# TQQQ 10-25% below its own 200SMA
cond = d.spx_dev.between(-0.03,0.04) & d.ndx_dev.between(-0.06,0.01) & d.tq_dev.between(-0.25,-0.10)
idx = d.index[cond]
print("Matching days:", len(idx), "episodes (years):", sorted(set(idx.year)))
fw = {}
tqc = (1+d.tqqq_ret).cumprod(); qc=(1+d.qqq_ret).cumprod()
H = {"3m":63,"6m":126,"12m":252,"24m":504}
rows=[]
for t in idx[::3]:
    i = d.index.get_loc(t)
    if i+504 >= len(d): continue
    seg = d.iloc[i:i+505]
    a,_ = run(seg, start_in=True, lag=0)   # buy now, then follow strategy
    b,_ = run(seg, start_in=False, lag=0)  # wait for +4% signal
    row={"date":t}
    for k,h in H.items():
        row["now_"+k]=(1+a.iloc[1:h+1]).prod()-1
        row["wait_"+k]=(1+b.iloc[1:h+1]).prod()-1
        row["tqqqBH_"+k]=tqc.iloc[i+h]/tqc.iloc[i]-1
    row["tqqq_maxDD12"]=(tqc.iloc[i:i+253]/tqc.iloc[i]).min()-1
    rows.append(row)
R = pd.DataFrame(rows).set_index("date")
print("Samples:", len(R))
summ = pd.DataFrame({k:{"median %":R[k].median()*100,"mean %":R[k].mean()*100,"P(loss) %":(R[k]<0).mean()*100,"p10 %":R[k].quantile(.1)*100} for k in R.columns}).T.round(1)
print(summ.to_string())
# by episode
R["ep"]=R.index.to_period("Q")
print("\nBy quarter (12m: buy-now-then-strategy vs wait-for-signal vs TQQQ hold):")
print((R.groupby("ep")[["now_12m","wait_12m","tqqqBH_12m","tqqq_maxDD12"]].median()*100).round(0).to_string())
# unconditional baseline
allr = pd.Series([tqc.iloc[i+252]/tqc.iloc[i]-1 for i in range(0,len(d)-253,5)])
print(f"\nUnconditional TQQQ 12m: median {allr.median()*100:.0f}%, P(loss) {(allr<0).mean()*100:.0f}%")
R.to_csv("now_samples.csv")
