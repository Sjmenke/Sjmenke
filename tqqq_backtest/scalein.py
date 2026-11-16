"""How should a NEW buyer build a TQQQ position from a state like today's?

Today-like state: S&P between -3% and +4% of its 200SMA (strategy "hold zone"),
NDX within -6%..+1% of its 200SMA, TQQQ 10-25% under its own 200SMA.

Every plan obeys the strategy's stop: if S&P closes < -3% under its 200SMA, everything
goes to cash, and the plan then waits for the normal +4% signal to go 100% in.
Once a plan is fully in (or the +4% signal fires), the tuned strategy takes over
(+4/-3 with 40% NDX-vol cap -> QQQ).
"""
import numpy as np
import pandas as pd
from engine import add_features, states, T, Q, C
from backtest import load

H = 504  # simulate 2 years from each start


def plan_sim(seg, plan, strat_W):
    """seg: slice starting at the decision day. Returns daily equity (len H+1).

    plan: dict(tranches=[(trigger, frac_of_target)], park='cash'|'qqq')
      trigger: ('now',) | ('day', k) | ('ndx_above', x) | ('spx_above', x) | ('vol_below', v, after_day)
    """
    sd = seg.spx_dev.values; nd = seg.ndx_dev.values; v = seg.ndx_vol20.values
    R = seg[["tqqq_ret", "qqq_ret", "cash_ret"]].values
    n = min(H + 1, len(seg))
    park = 1 if plan.get("park") == "qqq" else 2
    h = np.zeros(3); h[park] = 1.0
    pending = list(plan["tranches"])
    mode = "stopped" if not plan["tranches"] else "building"  # building -> full (strategy) ; stopped -> wait for +4 -> full
    eq = np.ones(n)
    for t in range(n):
        if t > 0:
            h = h * (1 + R[t]); eq[t] = h.sum()
        tot = h.sum()
        if mode == "building":
            if sd[t] < -0.03:
                h = np.array([0, 0, tot]); mode = "stopped"; pending = []
            elif sd[t] > 0.04:
                mode = "full"
            else:
                fired = []
                for tr in pending:
                    trig, frac = tr[0], tr[1]
                    k = trig[0]
                    if (k == "now" or (k == "day" and t >= trig[1]) or
                            (k == "ndx_above" and nd[t] > trig[1]) or
                            (k == "vol_below" and t >= trig[2] and v[t] < trig[1])):
                        fired.append(tr)
                for tr in fired:
                    pending.remove(tr)
                    amt = tr[1] * h[park]  # fraction of money still parked
                    h[park] -= amt; h[0] += amt
                if not pending:
                    mode = "full"
        elif mode == "stopped":
            if sd[t] > 0.04:
                mode = "full"
        if mode == "full":
            w = strat_W[t]
            h = np.array(w) * h.sum()
        # 5bps cost ignored for tranche moves (small)
    return eq


PLANS = {
    "1 All-in TQQQ now":               dict(tranches=[(("now",), 1.0)]),
    "2 Wait for +4% signal":           dict(tranches=[]),
    "3 Half now, half at +4%":         dict(tranches=[(("now",), 0.5), (("spx_above", 9), 0)]),
    "4 Thirds by time (0/3wk/6wk)":    dict(tranches=[(("now",), 1/3), (("day", 15), 0.5), (("day", 30), 1.0)]),
    "5 Thirds by signal (now/NDX>SMA/+4%)": dict(tranches=[(("now",), 1/3), (("ndx_above", 0.0), 0.5), (("spx_above", 9), 0)]),
    "6 QQQ now, TQQQ at +4%":          dict(tranches=[(("spx_above", 9), 0)], park="qqq"),
    "7 1/3 TQQQ + 2/3 QQQ, all at +4%": dict(tranches=[(("now",), 1/3), (("spx_above", 9), 0)], park="qqq"),
    "8 1/3 now, rest when vol<30% (>=2wk)": dict(tranches=[(("now",), 1/3), (("vol_below", 0.30, 10), 0.5), (("vol_below", 0.30, 20), 1.0)]),
}
# note: ("spx_above", 9) never fires on its own; the +4% graduation handles it.


def main():
    df = add_features(load())
    tq = (1 + df.tqqq_ret).cumprod()
    df["tq_dev"] = tq / tq.rolling(200).mean() - 1
    df = df.dropna(subset=["tq_dev"]).loc["1987":]
    cond = (df.spx_dev.between(-0.03, 0.04) & df.ndx_dev.between(-0.06, 0.01)
            & df.tq_dev.between(-0.25, -0.10))
    idx = [i for i, t in enumerate(df.index) if cond.iloc[i] and i + H < len(df)][::2]
    out = []
    for i in idx:
        seg = df.iloc[i:i + H + 1]
        # strategy weights for "full" mode: in-regime path starting from this day
        sw = states(seg, vol_cap=0.40, start_in=True)
        for name, p in PLANS.items():
            eq = plan_sim(seg, p, sw)
            dd12 = (eq[:253] / np.maximum.accumulate(eq[:253]) - 1).min()
            out.append(dict(date=df.index[i], plan=name, r3=eq[63] - 1, r6=eq[126] - 1,
                            r12=eq[252] - 1, r24=eq[504] - 1, dd12=dd12, worst12=eq[:253].min() - 1))
    R = pd.DataFrame(out)
    # episodes: new episode if gap > 40 trading days
    ds = pd.Series(sorted(R.date.unique()))
    ep = (ds.diff().dt.days.fillna(999) > 60).cumsum()
    R["episode"] = R.date.map(dict(zip(ds, ep)))
    R["year"] = R.date.dt.year
    pd.set_option("display.width", 250)
    print(f"start days: {R.date.nunique()}  independent episodes: {R.episode.nunique()}")
    g = R.groupby("plan")
    S = pd.DataFrame({
        "12m median": g.r12.median() * 100, "12m p10": g.r12.quantile(.1) * 100,
        "P(12m loss)": g.r12.apply(lambda x: (x < 0).mean()) * 100,
        "24m median": g.r24.median() * 100, "24m p10": g.r24.quantile(.1) * 100,
        "worst dip 12m (median)": g.worst12.median() * 100,
        "worst dip 12m (p10)": g.worst12.quantile(.1) * 100,
        "maxDD 12m (p10)": g.dd12.quantile(.1) * 100,
    }).round(1)
    print(S.to_string())
    # episode-weighted (each episode counts once)
    E = R.groupby(["plan", "episode"])[["r12", "r24", "worst12"]].median().groupby("plan")
    print("\nEpisode-weighted (each historical episode counts once):")
    print(pd.DataFrame({"12m median": E.r12.median() * 100, "12m worst ep": E.r12.min() * 100,
                        "24m median": E.r24.median() * 100, "worst dip med": E.worst12.median() * 100,
                        "worst dip worst ep": E.worst12.min() * 100}).round(1).to_string())
    # regret: how often each plan beats all-in / wait at 12m
    piv = R.pivot_table(index="date", columns="plan", values="r12")
    print("\n% of start days each plan beat 'Wait' / 'All-in' at 12m:")
    for c in piv.columns:
        print(f"  {c:40s} beat wait {(piv[c] > piv['2 Wait for +4% signal']).mean()*100:4.0f}%   beat all-in {(piv[c] > piv['1 All-in TQQQ now']).mean()*100:4.0f}%")
    # high-vol subset like today
    hv = R[R.date.isin(df.index[df.ndx_vol20 > 0.28])]
    print(f"\nSubset with NDX 20d vol > 28% (like now): {hv.date.nunique()} days, years {sorted(hv.year.unique())}")
    print((hv.groupby("plan")[["r12", "r24", "worst12"]].median() * 100).round(1).to_string())
    R.to_csv("scalein_samples.csv", index=False)


if __name__ == "__main__":
    main()
