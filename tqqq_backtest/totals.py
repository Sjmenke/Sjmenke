"""What $10,000 became + how deep/long the drawdowns were. Next-day fills."""
import numpy as np, pandas as pd, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
from engine import add_features, states, sim
from backtest import load, run, stats

df = add_features(load()).loc["1986":]
d5 = df.copy(); d5["tqqq_ret"] = .5 * df.tqqq_ret + .5 * df.qqq_ret
S = {  # name: (returns, color, line style, bar hatch)
    "QQQ buy & hold": (df.qqq_ret, "#999999", "-", ""),
    "TQQQ buy & hold": (df.tqqq_ret, "#D55E00", ":", "xx"),
    "Reddit full (+4/-3, DCA, bodyguard)": (run(df, mode="dca", bodyguard=True)[0], "#CC79A7", "--", "//"),
    "Tuned 3x (+4/-3, vol cap)": (sim(df, states(df, vol_cap=.4)), "#0072B2", "-", ""),
    "Tuned 50/50 TQQQ+QQQ": (sim(d5, states(d5, vol_cap=.4)), "#009E73", "-.", ".."),
}
STARTS = ["1990-01-01", "2000-03-10", "2010-02-12", "2016-11-16", "2021-11-16"]
LBL = ["1990 (36 yrs)", "Mar 2000 dot-com top", "2010 (TQQQ launch)", "Last 10 yrs", "Last 5 yrs"]

rows = []
for nm, (r, *_ ) in S.items():
    row = {"strategy": nm}
    for s, l in zip(STARTS, LBL):
        row[l] = 1e4 * (1 + r.loc[s:]).prod()
    x = r.loc["1990":]; eq = (1 + x).cumprod(); dd = eq / eq.cummax() - 1
    under = (dd < -0.0001).astype(int); runs = under.groupby((under == 0).cumsum()).sum()
    st = stats(x)
    row.update({"CAGR 1990+": st["CAGR"], "Max DD": st["MaxDD"],
                "Longest underwater (yrs)": runs.max() / 252,
                "Worst calendar yr": x.groupby(x.index.year).apply(lambda y: (1 + y).prod() - 1).min()})
    rows.append(row)
T = pd.DataFrame(rows).set_index("strategy")
fmt = T.copy()
for l in LBL: fmt[l] = T[l].map(lambda v: f"${v:,.0f}")
for c in ["CAGR 1990+", "Max DD", "Worst calendar yr"]: fmt[c] = T[c].map(lambda v: f"{v*100:.0f}%")
fmt["Longest underwater (yrs)"] = T["Longest underwater (yrs)"].map(lambda v: f"{v:.1f}")
pd.set_option("display.width", 260); print(fmt.to_string())

fig = plt.figure(figsize=(13, 13))
gs = fig.add_gridspec(2, 5, height_ratios=[1.15, 1], hspace=.35, wspace=.08)
names = list(S)
for i, l in enumerate(LBL):
    a = fig.add_subplot(gs[0, i]); vals = T[l].values
    for j, nm in enumerate(names):
        c, ls, h = S[nm][1], S[nm][2], S[nm][3]
        a.barh(len(names) - 1 - j, vals[j], color=c, hatch=h, edgecolor="k", lw=.6)
        a.text(vals[j], len(names) - 1 - j, f" ${vals[j]/1e3:,.0f}k" if vals[j] < 1e6 else f" ${vals[j]/1e6:,.1f}M",
               va="center", fontsize=8.5)
    a.set_xscale("log"); a.axvline(1e4, color="k", lw=.8, ls=":")
    a.set_title(f"From {l}", fontsize=10); a.set_xlim(1e3, vals.max() * 30)
    a.set_yticks(range(len(names)));
    a.set_yticklabels(names[::-1] if i == 0 else [], fontsize=9)
    a.tick_params(axis="x", labelsize=7)
fig.suptitle("What \\$10,000 became (log scale; dotted line = the \\$10k you started with). Next-day fills, before taxes.",
         fontsize=12, y=.915)
a = fig.add_subplot(gs[1, :])
for nm in ["QQQ buy & hold", "Tuned 3x (+4/-3, vol cap)", "Tuned 50/50 TQQQ+QQQ"]:
    r, c, ls, _ = S[nm]; x = r.loc["1990":]; eq = (1 + x).cumprod(); dd = (eq / eq.cummax() - 1) * 100
    a.plot(dd, color=c, ls=ls, lw=1.4, label=f"{nm}  (worst {dd.min():.0f}%)")
    t = dd.idxmin(); a.annotate(f"{dd.min():.0f}%\n{t:%b %Y}", (t, dd.min()), xytext=(25, -5),
                                textcoords="offset points", fontsize=8.5, color=c, fontweight="bold",
                                arrowprops=dict(arrowstyle="-|>", color=c))
a.axhline(-50, color="k", lw=.7, ls=":"); a.text(df.index[-1], -49, "-50%", ha="right", fontsize=8)
a.set_ylim(-100, 3); a.grid(alpha=.3); a.legend(fontsize=9, loc="lower left")
a.set_title("How far below its previous high each portfolio was (drawdown), 1990 to today", fontsize=11)
plt.savefig("totals.png", dpi=110, bbox_inches="tight")
