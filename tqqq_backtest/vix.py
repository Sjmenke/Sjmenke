"""VIX overlays on the +4/-3 S&P signal. All results use next-close fills (lag=2)."""
import numpy as np, pandas as pd
from engine import add_features, states, sim
from backtest import load, stats

def data():
    df = add_features(load())
    v = pd.read_csv("data/vix.csv", index_col=0, parse_dates=True)
    df["vix"] = v["^VIX"].reindex(df.index).ffill()
    df["vix3m"] = v["^VIX3M"].reindex(df.index).ffill()
    df["vxn"] = v["^VXN"].reindex(df.index).ffill()
    return df.loc["1990-02":]

def overlay(df, base_W, kind, hi=30, lo=None, entry_max=None):
    """Modify days where base says TQQQ. kind: 'qqq' | 'cash' | 'grade' | 'term'."""
    W = base_W.copy(); vix = df.vix.values; lo = hi - 5 if lo is None else lo
    term = (df.vix > df.vix3m).values
    on = False
    for t in range(len(W)):
        if W[t, 0] < .5: on = False; continue
        if kind == "grade":
            W[t] = (1, 0, 0) if vix[t] < 20 else ((.5, .5, 0) if vix[t] < 30 else (0, 1, 0)); continue
        if kind == "term":
            if term[t]: W[t] = (0, 1, 0)
            continue
        if on and vix[t] < lo: on = False
        elif not on and vix[t] > hi: on = True
        if on: W[t] = (0, 1, 0) if kind == "qqq" else (0, 0, 1)
    return W

def row(df, name, W):
    r = sim(df, W); out = {"rule": name}
    for a, b in [("1990", "2026"), ("2000", "2009"), ("2010", "2026")]:
        s = stats(r.loc[a:b]); out[f"{a}-{b[2:]}"] = f"{s['CAGR']*100:5.1f}% / {s['MaxDD']*100:4.0f}%"
    out["$10k 1990→"] = f"${(1+r).prod()*1e4:,.0f}"
    return out, r

if __name__ == "__main__":
    df = data()
    B = states(df)                 # base +4/-3
    V = states(df, vol_cap=0.40)   # tuned (NDX realized vol cap)
    rows = []
    def add(n, W): rows.append(row(df, n, W)[0])
    add("QQQ buy&hold", np.tile([0, 1, 0], (len(df), 1)).astype(float))
    add("Base +4/-3", B); add("Tuned (NDX vol cap 40%)", V)
    for h in (25, 30, 35): add(f"Base + VIX>{h} → QQQ", overlay(df, B, "qqq", h))
    for h in (30, 40): add(f"Base + VIX>{h} → cash", overlay(df, B, "cash", h))
    add("Base + VIX graded (<20 3x, 20-30 2x, >30 1x)", overlay(df, B, "grade"))
    add("Base + VIX>VIX3M → QQQ (2006+ data)", overlay(df, B, "term"))
    for m in (20, 25):
        add(f"Base, entry only if VIX<{m}", states(df, entry_gate=(df.vix < m).values))
    pd.set_option("display.width", 250)
    print("CAGR / max drawdown, next-day fills\n" + pd.DataFrame(rows).set_index("rule").to_string())
    l = df.iloc[-1]
    print(f"\nToday: VIX {l.vix:.1f}, VIX3M {l.vix3m:.1f} (term {'INVERTED' if l.vix>l.vix3m else 'normal'}), VXN {l.vxn:.1f}")
