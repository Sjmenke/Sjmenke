from common import *
from backtest import FIN_SPREAD, QQQ_ER, TQQQ_ER
rng = np.random.default_rng(0)
src = pd.DataFrame({"s": df.spx.pct_change(), "n": df.ndx.pct_change(), "q": df.qqq_ret, "tb": df.tbill}).dropna().values
N, B, YRS, WARM = 500, 252, 20, 252
def path(blk):
    n_blocks = (YRS*TD + WARM)//blk + 1
    st = rng.integers(0, len(src)-blk, n_blocks)
    x = np.concatenate([src[s:s+blk] for s in st])[:YRS*TD+WARM]
    d = pd.DataFrame(x, columns=["s","n","q","tb"])
    d["spx"] = (1+d.s).cumprod(); d["ndx"] = (1+d.n).cumprod()
    d["spx_dev"] = d.spx/d.spx.rolling(200).mean()-1; d["ndx_dev"] = d.ndx/d.ndx.rolling(200).mean()-1
    d["ndx_vol20"] = d.n.rolling(20).std()*np.sqrt(TD)
    d["qqq_ret"] = d.q; d["cash_ret"] = d.tb/TD
    d["tqqq_ret"] = 3*(d.q+QQQ_ER/TD) - 2*(d.tb+FIN_SPREAD)/TD - TQQQ_ER/TD
    return d.iloc[WARM:].reset_index(drop=True)
def st(r): s = stats(r); return s["CAGR"], s["MaxDD"]
for blk in [252, 63]:
    res = {"tuned": [], "base": [], "QQQ": [], "3xB&H": []}
    for i in range(N):
        d = path(blk)
        res["tuned"].append(st(sim(d, states(d, **TUNED)))); res["base"].append(st(sim(d, states(d, **BASE))))
        res["QQQ"].append(st(d.qqq_ret)); res["3xB&H"].append(st(d.tqqq_ret))
    rows = []
    for k, v in res.items():
        a = np.array(v); rows.append(dict(name=f"{k} blk{blk}", medCAGR=round(np.median(a[:,0])*100,1), p5CAGR=round(np.percentile(a[:,0],5)*100,1),
              medDD=round(np.median(a[:,1])*100), P_DDlt60=round((a[:,1]<-0.6).mean(),2), P_DDlt80=round((a[:,1]<-0.8).mean(),2)))
    if blk == 252:
        t = np.array(res["tuned"]); q = np.array(res["QQQ"]); b = np.array(res["base"])
        print("P(tuned CAGR > QQQ)", (t[:,0]>q[:,0]).mean(), " P(tuned DD better than base)", (t[:,1]>b[:,1]).mean(), " P(tuned CAGR<0)", (t[:,0]<0).mean())
    tab(rows)
