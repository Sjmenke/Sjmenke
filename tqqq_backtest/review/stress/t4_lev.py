from common import *
from backtest import FIN_SPREAD, QQQ_ER
und = df.qqq_ret + QQQ_ER/TD; fin = (df.tbill + FIN_SPREAD)/TD
def lev(L, er=0.0095): return L*und - (L-1)*fin - er/TD
rows = []
for name, kw in [("tuned", TUNED), ("base", BASE)]:
    W = states(df, **kw)
    for lab, x in [("3x(spliced)", df.tqqq_ret), ("3x synthetic", lev(3,0.0084)), ("2x synthetic", lev(2)), ("50/50 3x+QQQ", 0.5*df.tqqq_ret+0.5*df.qqq_ret)]:
        d = df.copy(); d["tqqq_ret"] = x
        r = sim(d, W); rows.append(row(r, f"{name} {lab}"))
        if lab=="3x(spliced)": rows.append(row(r["2010":], f"{name} 3x 2010+"))
rows.append(row(df.qqq_ret, "QQQ B&H")); rows.append(row(lev(3,0.0084), "3x B&H")); rows.append(row(lev(2), "2x B&H"))
tab(rows)
# synthetic vs real tracking 2010+
m = df.tqqq_real.notna(); print("real vs syn 3x CAGR 2010+:", round(stats(df.tqqq_real[m])["CAGR"]*100,1), round(stats(lev(3,0.0084)[m])["CAGR"]*100,1))
