"""95% confidence intervals for the v1 backtest, resampling harvest years.

    python scripts/10_confidence_intervals.py

Reads results/v1_scores_rs_pr.csv.gz (script 06). Writes results/v1_ci.csv.
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ssi.config import RESULTS  # noqa: E402
from ssi.uncertainty import year_bootstrap  # noqa: E402

INDICES = ["Rainfall index", "SSI v0 (calendar windows)", "NDVI only",
           "SSI v1 weather (satellite stages)", "SSI v1 full (+ NDVI)", "Turgor index"]
REF = "Rainfall index"

sc = pd.read_csv(RESULTS / "v1_scores_rs_pr.csv.gz")
out = []
for region, states in {"RS + PR": ["RS", "PR"], "RS": ["RS"], "PR": ["PR"]}.items():
    df = sc[sc["st"].isin(states)].reset_index(drop=True)
    res = year_bootstrap(df, {k: df[k].values for k in INDICES}, n=1000, reference=REF)
    res.insert(0, "region", region)
    out.append(res)
    print(region, "done", flush=True)
res = pd.concat(out).round(3)
res.to_csv(RESULTS / "v1_ci.csv", index=False)
pd.set_option("display.width", 220)
print(res[res["index"].isin([REF, "SSI v1 full (+ NDVI)", "Turgor index"])].to_string(index=False))
