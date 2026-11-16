from common import *
nr = df.ndx.pct_change(); sr = df.spx.pct_change(); rows = []
for src, x in [("NDX", nr), ("SPX", sr)]:
    for w in [10, 20, 60]:
        v = (x.rolling(w).std()*np.sqrt(TD)).bfill()
        caps = [0.30, 0.40, 0.50] if src=="NDX" else [0.20, 0.25, 0.30]
        for c in caps:
            d = df.copy(); d["ndx_vol20"] = v
            r = sim(d, states(d, entry=0.04, exit_=0.03, vol_cap=c, vol_hys=c/8))
            rr = row(r, f"{src} {w}d cap{int(c*100)}"); rr["DD00-09"] = round(stats(r["2000":"2009"])["MaxDD"]*100); rows.append(rr)
tab(rows)
