"""Generalized rule engine for tuning experiments.

states(): builds a per-day target allocation from rule options.
sim():    applies target weights (decided at close t, held from t+1) with costs.
"""
import numpy as np
import pandas as pd
from backtest import load, stats, TD

T, Q, C = (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)


def add_features(df):
    df = df.copy()
    nr = df["ndx"].pct_change()
    df["ndx_vol20"] = nr.rolling(20).std() * np.sqrt(TD)
    for k in ("spx", "ndx"):
        m = df[k].ewm(span=12, adjust=False).mean() - df[k].ewm(span=26, adjust=False).mean()
        df[f"{k}_macd"] = m
        df[f"{k}_macd_sig"] = m.ewm(span=9, adjust=False).mean()
    # weekly MACD on S&P (Friday closes, forward-filled to days; uses only completed weeks)
    wk = df["spx"].resample("W-FRI").last()
    wm = wk.ewm(span=12, adjust=False).mean() - wk.ewm(span=26, adjust=False).mean()
    wh = (wm - wm.ewm(span=9, adjust=False).mean())
    df["spx_wmacd_hist"] = wh.reindex(df.index, method="ffill").shift(1)
    return df.dropna(subset=["ndx_vol20"])


def states(df, entry=0.04, exit_=0.03, ndx_exit=None, ndx_reentry=None,
           bodyguard=None, sticky_bg=False, vol_cap=None, vol_hys=0.05,
           confirm=1, out=C, start_in=False, entry_gate=None):
    """Return (n,3) target weights.

    ndx_exit:    also exit if NDX falls this far below its own 200SMA (e.g. 0.05)
    ndx_reentry: on re-entry also require NDX dev above this (e.g. 0.0)
    bodyguard:   (delever, sell) NDX dev levels -> QQQ / cash while in regime
    sticky_bg:   once bodyguard trips, stay de-levered until the next SPX exit
    vol_cap:     hold QQQ instead of TQQQ when NDX 20d vol > vol_cap
                 (re-lever when vol < vol_cap - vol_hys)
    confirm:     entry requires `confirm` consecutive closes above the entry line
    """
    sd = df["spx_dev"].values; nd = df["ndx_dev"].values; v = df["ndx_vol20"].values
    n = len(df); W = np.zeros((n, 3))
    in_lev = start_in; above = 0; tripped = False; hi_vol = False
    for t in range(n):
        above = above + 1 if sd[t] > entry else 0
        if in_lev:
            ex = sd[t] < -exit_ or (ndx_exit is not None and nd[t] < -ndx_exit)
            if ex:
                in_lev = False; tripped = False
        else:
            ok = above >= confirm and (ndx_reentry is None or nd[t] > ndx_reentry) and (entry_gate is None or entry_gate[t])
            if ok:
                in_lev = True
        if vol_cap is not None:
            if hi_vol and v[t] < vol_cap - vol_hys: hi_vol = False
            elif not hi_vol and v[t] > vol_cap: hi_vol = True
        if not in_lev:
            W[t] = out; continue
        w = T
        if bodyguard:
            dl, sl = bodyguard
            if nd[t] > sl: w = C; tripped = True
            elif nd[t] > dl or (sticky_bg and tripped): w = Q; tripped = True
        if hi_vol and w == T: w = Q
        W[t] = w
    return W


def sim(df, W, lag=1, cost=0.0005):
    Wd = pd.DataFrame(W, index=df.index).shift(lag)
    Wd.iloc[:lag] = [0, 0, 1]
    R = df[["tqqq_ret", "qqq_ret", "cash_ret"]].values
    turn = np.abs(Wd.diff().fillna(0).values).sum(1) / 2
    return pd.Series((Wd.values * R).sum(1) - turn * cost, index=df.index)


PERIODS = {"1986-99": ("1986", "1999"), "2000-09": ("2000", "2009"),
           "2010-26": ("2010", "2026"), "FULL": ("1986", "2026")}


def evaluate(df, name, **kw):
    W = states(df, **kw)
    r = sim(df, W)
    row = {"name": name}
    for p, (a, b) in PERIODS.items():
        s = stats(r.loc[a:b])
        row[f"{p} CAGR"] = round(s["CAGR"] * 100, 1)
        row[f"{p} DD"] = round(s["MaxDD"] * 100)
    sw = (np.abs(np.diff(W[:, 0])) > 0.5).sum() / 2 / (len(df) / TD)
    row["switches/yr"] = round(sw, 2)
    return row


if __name__ == "__main__":
    df = add_features(load()).loc["1986":]
    base = dict()
    V = [
        ("A  base +4/-3 TQQQ/cash", {}),
        ("B  Reddit bodyguard 30/40 (non-sticky)", dict(bodyguard=(0.30, 0.40))),
        ("C  sticky bodyguard 30/40", dict(bodyguard=(0.30, 0.40), sticky_bg=True)),
        ("D  + NDX exit -5%", dict(ndx_exit=0.05)),
        ("E  + NDX exit -3%", dict(ndx_exit=0.03)),
        ("F  + NDX exit -7%", dict(ndx_exit=0.07)),
        ("G  + NDX exit -5%, reentry NDX>0", dict(ndx_exit=0.05, ndx_reentry=0.0)),
        ("H  vol cap 30%", dict(vol_cap=0.30)),
        ("I  vol cap 35%", dict(vol_cap=0.35)),
        ("J  vol cap 40%", dict(vol_cap=0.40)),
        ("K  confirm 3 days", dict(confirm=3)),
        ("L  NDX exit -5% + sticky BG", dict(ndx_exit=0.05, bodyguard=(0.30, 0.40), sticky_bg=True)),
        ("M  NDX exit -5% + vol cap 35%", dict(ndx_exit=0.05, vol_cap=0.35)),
        ("N  NDX-5 + sticky BG + vol35", dict(ndx_exit=0.05, bodyguard=(0.30, 0.40), sticky_bg=True, vol_cap=0.35)),
    ]
    rows = [evaluate(df, k, **v) for k, v in V]
    t = pd.DataFrame(rows).set_index("name")
    pd.set_option("display.width", 250)
    print(t.to_string())
