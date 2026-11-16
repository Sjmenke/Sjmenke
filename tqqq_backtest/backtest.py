"""SPY 200SMA (+4%/-3%) TQQQ/QQQ strategy backtest.

Data: data/prices.csv (Yahoo, adjusted closes) and data/dtb3.csv (FRED 3M T-bill).
Signal series use PRICE indices (^GSPC for SPY, ^NDX for QQQ) so the SMA matches
what TradingView shows on unadjusted SPY/QQQ.
"""
import numpy as np
import pandas as pd

TD = 252
TQQQ_ER = 0.0084          # TQQQ expense ratio
FIN_SPREAD = 0.010
QQQ_ER = 0.0020
NDX_DIV = 0.008           # approx NDX dividend yield pre-1999 (no QQQ yet)


def load():
    p = pd.read_csv("data/prices.csv", index_col=0, parse_dates=True)
    r = pd.read_csv("data/dtb3.csv", index_col=0, parse_dates=True)["DTB3"]
    r = pd.to_numeric(r, errors="coerce").reindex(p.index).ffill() / 100
    df = pd.DataFrame(index=p.index)
    df["spx"] = p["^GSPC"]
    df["ndx"] = p["^NDX"]
    df["tbill"] = r.fillna(0.05)
    # QQQ total return: real QQQ (adjusted) from 1999-03-10, before that NDX + div - ER
    ndx_ret = p["^NDX"].pct_change() + (NDX_DIV - QQQ_ER) / TD
    qqq_ret = p["QQQ"].pct_change()
    df["qqq_ret"] = qqq_ret.where(p["QQQ"].shift(1).notna(), ndx_ret)
    # unlevered underlying gross of QQQ ER (for building 3x)
    und = df["qqq_ret"] + QQQ_ER / TD
    fin = (df["tbill"] + FIN_SPREAD) / TD
    df["tqqq_syn"] = 3 * und - 2 * fin - TQQQ_ER / TD
    df["tqqq_real"] = p["TQQQ"].pct_change()
    # splice: real TQQQ where available
    df["tqqq_ret"] = df["tqqq_real"].where(p["TQQQ"].shift(1).notna(), df["tqqq_syn"])
    df["cash_ret"] = df["tbill"] / TD
    df["spx_sma"] = df["spx"].rolling(200).mean()
    df["ndx_sma"] = df["ndx"].rolling(200).mean()
    df["spx_dev"] = df["spx"] / df["spx_sma"] - 1
    df["ndx_dev"] = df["ndx"] / df["ndx_sma"] - 1
    return df.dropna(subset=["spx_sma", "ndx_sma", "qqq_ret"])


def run(df, entry=0.04, exit_=0.03, mode="cash", bodyguard=False,
        bg_delever=0.30, bg_sell=0.40, dca_months=12, lag=2, cost=0.0005, start_in=False):
    """Dollar-holdings simulation. Signal at close t, trade at close t+lag.

    mode: 'cash' -> out of TQQQ hold T-bills
          'qqq'  -> out of TQQQ hold QQQ
          'dca'  -> out of TQQQ go to cash, buy QQQ with 1/remaining of cash every
                    21 trading days over dca_months (Reddit "Change 2")
    bodyguard: while in TQQQ regime, NDX > +bg_delever above its 200SMA -> hold QQQ,
               > +bg_sell -> cash. Re-levers when back below.
    """
    dev = df["spx_dev"].values; ndev = df["ndx_dev"].values
    R = df[["tqqq_ret", "qqq_ret", "cash_ret"]].values
    n = len(df)
    # 1) decide regime/target per day (decided on close t)
    state = np.empty(n, dtype=object)
    in_lev = start_in
    for t in range(n):
        if in_lev and dev[t] < -exit_: in_lev = False
        elif not in_lev and dev[t] > entry: in_lev = True
        if in_lev:
            s = "T"
            if bodyguard:
                if ndev[t] > bg_sell: s = "C"
                elif ndev[t] > bg_delever: s = "Q"
            state[t] = s
        else:
            state[t] = "OUT"
    state = pd.Series(state).shift(lag).fillna("C").values
    # 2) dollar simulation
    h = np.array([0.0, 0.0, 1.0])  # tqqq, qqq, cash dollars
    out = np.zeros(n); W = np.zeros((n, 3))
    prev = None; days_out = 0
    for t in range(n):
        v0 = h.sum()
        h = h * (1 + R[t])          # returns earned on day t by holdings set at t-1 close
        v1 = h.sum()
        # rebalance at close t according to state[t+?]: holdings for next day
        s = state[t + 1] if t + 1 < n else state[t]
        tot = h.sum(); tgt = h.copy()
        if s == "T": tgt = np.array([tot, 0, 0])
        elif s == "Q": tgt = np.array([0, tot, 0])
        elif s == "C": tgt = np.array([0, 0, tot])
        else:  # OUT
            if prev != "OUT":
                days_out = 0
                tgt = np.array([0, tot, 0]) if mode == "qqq" else np.array([0, 0, tot])
            else:
                days_out += 1
                tgt = h.copy()
                if mode == "dca" and days_out % 21 == 0:
                    k = days_out // 21
                    rem = max(dca_months - k + 1, 1)
                    mv = h[2] / rem
                    tgt = np.array([0, h[1] + mv, h[2] - mv])
        turn = np.abs(tgt - h).sum() / 2
        h = tgt - (turn * cost) * (tgt / tgt.sum() if tgt.sum() else 0)
        prev = s
        out[t] = h.sum() / v0 - 1 if v0 else 0
        W[t] = h / h.sum()
    return pd.Series(out, index=df.index), pd.DataFrame(W, index=df.index, columns=["tqqq","qqq","cash"])


def stats(r, name="", rf=None):
    eq = (1 + r).cumprod()
    yrs = len(r) / TD
    cagr = eq.iloc[-1] ** (1 / yrs) - 1
    dd = (eq / eq.cummax() - 1).min()
    vol = r.std() * np.sqrt(TD)
    ex = r - (rf.reindex(r.index).fillna(0) if rf is not None else 0)
    sharpe = (ex.mean() * TD) / vol if vol else np.nan
    return dict(name=name, CAGR=cagr, MaxDD=dd, Vol=vol, Sharpe=sharpe,
                Final=eq.iloc[-1], Calmar=cagr / -dd if dd else np.nan)
