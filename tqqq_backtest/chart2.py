import pandas as pd, numpy as np, matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from engine import *
from backtest import run
df = add_features(load()).loc["1986":]
fig, ax = plt.subplots(2, 1, figsize=(11, 11), gridspec_kw={"height_ratios": [3, 2.4]})
a = ax[0]
S = {"QQQ buy&hold": (df.qqq_ret, "#999999", "-"),
     "Reddit full (DCA + bodyguard)": (run(df, mode="dca", bodyguard=True)[0], "#CC79A7", "--"),
     "Base +4/-3 TQQQ/cash": (sim(df, states(df)), "#0072B2", "-"),
     "Tuned: +4/-3 + Nasdaq vol cap 40%→QQQ": (sim(df, states(df, vol_cap=0.40)), "#009E73", "-.")}
for k, (r, c, ls) in S.items():
    s = stats(r); a.plot((1 + r).cumprod(), color=c, ls=ls, lw=1.7,
                         label=f"{k}  CAGR {s['CAGR']*100:.1f}%  MaxDD {s['MaxDD']*100:.0f}%")
a.set_yscale("log"); a.grid(alpha=.3); a.legend(fontsize=9, loc="upper left")
a.set_title("Growth of $1 since 1986 (log scale; TQQQ synthetic before 2010)")
R = pd.read_csv("scalein_samples.csv")
g = R.groupby("plan"); x = g.r12.quantile(.1) * 100; y = g.r12.median() * 100
a = ax[1]
mk = ["o", "s", "^", "D", "v", "P", "X", "*"]
cols = ["#D55E00", "#999999", "#E69F00", "#009E73", "#56B4E9", "#0072B2", "#CC79A7", "#000000"]
for i, p in enumerate(x.index):
    a.scatter(x[p], y[p], s=110, marker=mk[i], color=cols[i], edgecolor="k", lw=.6, zorder=3, label=p)
a.set_xlabel("Bad case: 10th-percentile 12-month return (%)  →  further right = safer")
a.set_ylabel("Typical: median 12-month return (%)")
a.set_title("Building a position from a state like today (239 start days, 20 episodes since 1987)")
a.grid(alpha=.3); a.legend(fontsize=8.5, loc="lower left", ncol=2)
plt.tight_layout(); plt.savefig("tuning_scalein.png", dpi=110)
