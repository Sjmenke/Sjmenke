from common import *
def taxed(W, st=0.35, lt=0.238, cash_t=0.35):
    r = sim(df, W); k = W.argmax(1); k = pd.Series(k, index=df.index).shift(1).fillna(2).astype(int).values
    run = np.r_[0, np.cumsum(k[1:] != k[:-1])]
    w = 1.0; cf = 0.0; ws = []; n_lt = n_st = 0
    for i in np.unique(run):
        m = run == i; g = np.prod(1 + r.values[m]) - 1; gain = w * g
        if k[m][0] == 2: tax = cash_t * max(gain, 0)
        else:
            longterm = m.sum() > TD; rate = lt if longterm else st
            n_lt += longterm and gain > 0; n_st += (not longterm) and gain > 0
            net = gain - cf
            if net > 0: tax, cf = rate * net, 0.0
            else: tax, cf = 0.0, -net if gain > 0 else cf - gain
        w = w * (1 + g) - tax; ws.append(w)
    yrs = len(r) / TD
    return round((w ** (1/yrs) - 1) * 100, 1), n_st, n_lt
q = df.qqq_ret; wq = (1 + q).prod(); yrs = len(q)/TD
rows = []
for name, kw in [("tuned", TUNED), ("base", BASE)]:
    W = states(df, **kw)
    pre = stats(sim(df, W))["CAGR"]*100
    a = taxed(W); b = taxed(W, lt=0.35)
    rows.append(dict(name=name, pretax=round(pre,1), tax_LT238_ST35=a[0], tax_all35=b[0], gain_exits_ST=a[1], gain_exits_LT=a[2]))
rows.append(dict(name="QQQ B&H", pretax=round(stats(q)["CAGR"]*100,1), tax_LT238_ST35=round(((wq-(wq-1)*0.238))**(1/yrs)*100-100,1), tax_all35=np.nan))
tab(rows)
