from common import *
import itertools
grid = list(itertools.product([0.0,0.02,0.04,0.06],[0.01,0.03,0.05],[None,0.35,0.40,0.50]))
Ws = {g: states(df, entry=g[0], exit_=g[1], vol_cap=g[2]) for g in grid}
Rs = {g: sim(df, W) for g, W in Ws.items()}
yrs = df.index.year.values
for obj in ["Calmar", "CAGR"]:
    Wst = Ws[(0.04,0.03,0.40)].copy(); picks = []
    for y in range(1995, yrs.max()+1):
        m = yrs < y
        best = max(grid, key=lambda g: stats(Rs[g][m])[obj])
        picks.append(best); Wst[yrs == y] = Ws[best][yrs == y]
    rs = sim(df, Wst)
    o = slice("1995", None)
    tab([row(rs[o], f"WF {obj}"), row(Rs[(0.04,0.03,0.40)][o], "tuned fixed"), row(Rs[(0.04,0.03,None)][o], "base fixed"), row(df.qqq_ret[o], "QQQ B&H")])
    print(pd.Series([str(p) for p in picks]).value_counts().head(5).to_string())
# rank of tuned among grid, per subperiod
for a,b in [("1986","1999"),("2000","2012"),("2013","2026")]:
    c = pd.Series({g: stats(Rs[g][a:b])["Calmar"] for g in grid}).rank(ascending=False)
    print(a,b,"tuned Calmar rank", int(c[(0.04,0.03,0.40)]), "/", len(grid), " base rank", int(c[(0.04,0.03,None)]))
