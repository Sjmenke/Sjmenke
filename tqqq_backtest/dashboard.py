"""Signal dashboard: entry/exit arrows + traffic-light criteria.

Colors (colorblind-safe Okabe-Ito) + symbols so color is never the only cue:
  GO     #009E73 green      ✓
  WAIT   #F0E442 yellow     !
  STOP   #D55E00 vermillion ✕
"""
import sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from engine import add_features, states
from backtest import load

GO, WAIT, STOP = "#009E73", "#F0E442", "#D55E00"
SYM = {GO: "✓", WAIT: "!", STOP: "✕"}
POS_COL = {"TQQQ": "#009E73", "QQQ": "#56B4E9", "Cash": "#BBBBBB"}


def lights(df):
    """Return dict name -> (series of colors, value-text series, is_rule)."""
    L = {}
    sd = df.spx_dev
    L["S&P vs 200SMA  (rule: +4% in / -3% out)"] = (
        np.where(sd > 0.04, GO, np.where(sd < -0.03, STOP, WAIT)),
        sd.map(lambda x: f"{x*100:+.1f}%"), True)
    v = df.ndx_vol20
    L["Nasdaq 20d vol  (rule: >40% → QQQ)"] = (
        np.where(v < 0.35, GO, np.where(v > 0.40, STOP, WAIT)),
        v.map(lambda x: f"{x*100:.1f}%"), True)
    nd = df.ndx_dev
    L["Nasdaq vs 200SMA  (context)"] = (
        np.where(nd > 0, GO, np.where(nd < -0.05, STOP, WAIT)),
        nd.map(lambda x: f"{x*100:+.1f}%"), False)
    m = df.spx_macd - df.spx_macd_sig
    L["S&P daily MACD  (context)"] = (
        np.where(m > 0, GO, STOP), m.map(lambda x: f"{x:+.0f}"), False)
    L["Bubble guard: Nasdaq stretch  (context)"] = (
        np.where(nd > 0.40, STOP, np.where(nd > 0.30, WAIT, GO)),
        nd.map(lambda x: f"{x*100:+.0f}% vs SMA"), False)
    return L


def main(start="2025-01-01"):
    p = pd.read_csv("data/prices.csv", index_col=0, parse_dates=True)
    full = add_features(load()).loc["1986":]
    W = states(full, vol_cap=0.40)
    pos = pd.Series(np.select([W[:, 0] > .5, W[:, 1] > .5], ["TQQQ", "QQQ"], "Cash"), index=full.index)
    df = full.loc[start:]; pos = pos.loc[start:]
    tq = p["TQQQ"].reindex(df.index)
    L = lights(df)

    fig = plt.figure(figsize=(14, 12.5))
    gs = fig.add_gridspec(3, 2, width_ratios=[5, 1.35], height_ratios=[3, 2.2, 2.1], wspace=0.03, hspace=0.18)
    a1 = fig.add_subplot(gs[0, 0]); a2 = fig.add_subplot(gs[1, 0], sharex=a1); a3 = fig.add_subplot(gs[2, 0], sharex=a1)
    at = fig.add_subplot(gs[:, 1]); at.axis("off")

    # --- Panel 1: TQQQ with position shading + arrows
    a1.plot(tq, color="k", lw=1.2, label="TQQQ")
    a1.plot(tq.rolling(200).mean().reindex(df.index) if False else p["TQQQ"].rolling(200).mean().reindex(df.index),
            color="#CC79A7", lw=1.4, label="TQQQ 200 SMA")
    blk = (pos != pos.shift()).cumsum()
    for _, g in pos.groupby(blk):
        a1.axvspan(g.index[0], g.index[-1], color=POS_COL[g.iloc[0]], alpha=.13, lw=0)
    ch = pos[pos != pos.shift()].iloc[1:]
    last_t = None
    for t, new in ch.items():
        y = tq.loc[t]
        dx = 28 if (last_t is not None and (t - last_t).days < 40) else 0
        last_t = t
        if new == "TQQQ":
            a1.annotate(f"BUY\n{t:%b %d}", (t, y), xytext=(dx, -38), textcoords="offset points", ha="center",
                        fontsize=8.5, color=GO, fontweight="bold",
                        arrowprops=dict(arrowstyle="-|>", color=GO, lw=2))
        elif new == "Cash":
            a1.annotate(f"SELL\n{t:%b %d}", (t, y), xytext=(dx, 34), textcoords="offset points", ha="center",
                        fontsize=8.5, color=STOP, fontweight="bold",
                        arrowprops=dict(arrowstyle="-|>", color=STOP, lw=2))
        else:
            a1.annotate(f"→QQQ\n{t:%b %d}", (t, y), xytext=(0, 34), textcoords="offset points", ha="center",
                        fontsize=8.5, color="#0072B2", fontweight="bold",
                        arrowprops=dict(arrowstyle="-|>", color="#0072B2", lw=2))
    for k, c in POS_COL.items():
        a1.add_patch(Rectangle((0, 0), 0, 0, color=c, alpha=.3, label=f"Strategy holds {k}"))
    a1.set_yscale("log"); a1.grid(alpha=.3); a1.legend(fontsize=8.5, loc="upper left")
    a1.set_title("TQQQ: strategy entries ▲ / exits ▼ (tuned rule: +4/-3 S&P signal, Nasdaq vol cap 40%)", fontsize=11)
    plt.setp(a1.get_xticklabels(), visible=False)

    # --- Panel 2: S&P signal with threshold-cross arrows
    a2.plot(df.spx, color="k", lw=1.2, label="S&P 500")
    a2.plot(df.spx_sma, color="#CC79A7", lw=1.5, label="200 SMA")
    a2.plot(df.spx_sma * 1.04, color=GO, ls="--", lw=1.4, label="+4% entry line")
    a2.plot(df.spx_sma * 0.97, color=STOP, ls=":", lw=1.8, label="-3% exit line")
    up = (df.spx_dev > .04) & (df.spx_dev.shift() <= .04)
    dn = (df.spx_dev < -.03) & (df.spx_dev.shift() >= -.03)
    a2.scatter(df.index[up], df.spx[up] * 0.985, marker="^", s=90, color=GO, edgecolor="k", zorder=5, label="crossed +4% ▲")
    a2.scatter(df.index[dn], df.spx[dn] * 1.015, marker="v", s=90, color=STOP, edgecolor="k", zorder=5, label="crossed -3% ▼")
    a2.grid(alpha=.3); a2.legend(fontsize=8.5, loc="upper left", ncol=2)
    a2.set_title("S&P 500 signal lines", fontsize=11)
    plt.setp(a2.get_xticklabels(), visible=False)

    # --- Panel 3: light strips
    names = list(L.keys())
    x = df.index
    for i, n in enumerate(names):
        cols = L[n][0]; yrow = len(names) - 1 - i
        blk = (pd.Series(cols) != pd.Series(cols).shift()).cumsum().values
        start_i = 0
        for j in range(1, len(cols) + 1):
            if j == len(cols) or blk[j] != blk[start_i]:
                x0 = x[start_i]; x1 = x[min(j, len(x) - 1)]
                a3.add_patch(Rectangle((matplotlib.dates.date2num(x0), yrow + .12),
                                       matplotlib.dates.date2num(x1) - matplotlib.dates.date2num(x0), .76,
                                       color=cols[start_i], lw=0))
                start_i = j
    a3.set_ylim(0, len(names)); a3.set_yticks([len(names) - 1 - i + .5 for i in range(len(names))])
    a3.set_yticklabels([("● " if L[n][2] else "○ ") + n.split("  (")[0] for n in names], fontsize=9)
    a3.set_title("Lights over time  (● = backtested rule light   ○ = context only)", fontsize=11)
    a3.grid(axis="x", alpha=.3)

    # --- Right: TODAY light board
    at.set_xlim(0, 1); at.set_ylim(0, 1)
    at.text(0.5, 0.985, f"TODAY  {df.index[-1]:%b %d, %Y}", ha="center", va="top", fontsize=13, fontweight="bold")
    yy = 0.92
    for grp, flag in (("RULE LIGHTS", True), ("CONTEXT LIGHTS", False)):
        at.text(0.02, yy, grp, fontsize=10, fontweight="bold", va="top"); yy -= 0.045
        for n in names:
            if L[n][2] != flag: continue
            c = L[n][0][-1]; val = L[n][1].iloc[-1]
            at.scatter([0.11], [yy - 0.018], s=1100, color=c, edgecolor="k", lw=.8, zorder=3)
            at.text(0.11, yy - 0.018, SYM[c], ha="center", va="center", fontsize=15, fontweight="bold", zorder=4,
                    color="k" if c == WAIT else "white")
            at.text(0.25, yy + 0.002, n.split("  (")[0], fontsize=9, va="top", fontweight="bold")
            at.text(0.25, yy - 0.028, f"{val}  ·  " + n.split("(")[1].rstrip(")"), fontsize=8, va="top", color="#333")
            yy -= 0.09
        yy -= 0.02
    cur = pos.iloc[-1]
    sma = df.spx_sma.iloc[-1]
    txt = (f"Holder: strategy says {cur}\n"
           f"New buyer: S&P in hold zone\n  → scale in by thirds\n  stop: S&P below\n"
           f"    {sma*0.97:,.0f} (-3%)\n  all-in: S&P above\n    {sma*1.04:,.0f} (+4%)")
    at.text(0.02, yy, txt, fontsize=8.3, va="top", family="monospace",
            bbox=dict(boxstyle="round", fc="#F4F4F4", ec="#999"))
    yy -= 0.17
    at.text(0.02, yy, "✓ go   ! wait/caution   ✕ stop", fontsize=9, va="top")
    plt.savefig("dashboard.png", dpi=110, bbox_inches="tight")


if __name__ == "__main__":
    main(*sys.argv[1:])
