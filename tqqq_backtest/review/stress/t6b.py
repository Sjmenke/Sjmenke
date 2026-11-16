from common import *
rt = sim(df, states(df, **TUNED)); rb = sim(df, states(df, **BASE))
y = pd.DataFrame({"tuned": (1+rt).groupby(df.index.year).prod()-1, "base": (1+rb).groupby(df.index.year).prod()-1})
y["diff"] = y.tuned - y.base; print((y[y["diff"].abs()>0.01]*100).round(0).T.to_string())
