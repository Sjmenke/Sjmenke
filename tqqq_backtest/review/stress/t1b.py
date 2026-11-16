from common import *
import itertools
grid = list(itertools.product([0.0,0.02,0.04,0.06],[0.01,0.03,0.05],[None,0.35,0.40,0.50]))
Rs = {g: sim(df, states(df, entry=g[0], exit_=g[1], vol_cap=g[2])) for g in grid}
yrs = df.index.year.values
print([ (y, max(grid, key=lambda g: stats(Rs[g][yrs<y])["Calmar"])) for y in range(1995,2004)])
# neighbourhood: full-period CAGR/DD per grid point at vol 0.40 and None
for v in [None, 0.40]:
    t = pd.DataFrame({e: {x: f"{stats(Rs[(e,x,v)])['CAGR']*100:.0f}/{stats(Rs[(e,x,v)])['MaxDD']*100:.0f}" for x in [0.01,0.03,0.05]} for e in [0.0,0.02,0.04,0.06]})
    print("vol", v, "(rows exit, cols entry) CAGR/DD"); print(t.to_string())
