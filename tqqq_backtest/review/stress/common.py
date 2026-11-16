import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
import numpy as np, pandas as pd
from engine import add_features, states, sim, evaluate
from backtest import load, stats, TD
df = add_features(load()).loc["1986":]
TUNED = dict(entry=0.04, exit_=0.03, vol_cap=0.40, vol_hys=0.05)
BASE = dict(entry=0.04, exit_=0.03)
def row(r, name):
    s = stats(r); return dict(name=name, CAGR=round(s["CAGR"]*100,1), DD=round(s["MaxDD"]*100), Calmar=round(s["Calmar"],2))
def tab(rows): print(pd.DataFrame(rows).set_index("name").to_string())
