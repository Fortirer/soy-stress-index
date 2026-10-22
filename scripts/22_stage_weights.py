"""Stage weights: physiology prior vs crop-water literature vs fitted (issue #8).

    python scripts/22_stage_weights.py

The Turgor index weights reproductive-stage stress 0.75 and vegetative 0.25
(a physiology prior). This script tests that choice against:

  fao_ky      FAO Irrigation & Drainage Paper 33 (Doorenbos & Kassam 1979) yield
              response factors for soybean: vegetative 0.2, flowering 0.8, yield
              formation 1.0. The Turgor reproductive window covers flowering and
              pod/seed fill, so 0.2 vs 0.9 -> 0.18 / 0.82
  equal       0.5 / 0.5
  rep_only    0 / 1
  fitted      weight chosen on the data: for each season, the reproductive
              weight (0 to 1, step 0.05) with the highest AUC on the OTHER
              seasons (leave-one-season-out); 2024-2025 use the weight fitted on
              2001-2023

Everything else is the product index (typical windows, data latency, end of
season). Backtest 2001-2023 with year-bootstrap CIs against the prior;
holdout 2024-2025. Writes results/stage_weights.csv.

Calibration with Janaina's eCO2 x drought x warming experiments and the
meta-analysis comes on top of this, once data ownership is settled (#8, #17).
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ssi.config import RESULTS  # noqa: E402
from ssi.early import load_asof_features  # noqa: E402
from ssi.index import components, stage_scores  # noqa: E402
from ssi.uncertainty import point_metrics, year_bootstrap  # noqa: E402

FIXED = {"prior (0.25/0.75)": 0.75, "fao_ky (0.18/0.82)": 0.9 / 1.1, "equal (0.5/0.5)": 0.5, "rep_only (0/1)": 1.0}
GRID = np.round(np.arange(0, 1.0001, 0.05), 2)

f = load_asof_features()
ref = (f["year"] <= 2023).values
st = stage_scores(components(f, ref=ref))
f = f[["fips5", "year"]].assign(veg=st["vegetative"].values, rep=st["reproductive"].values)

v1 = pd.read_csv(RESULTS / "v1_scores_rs_pr.csv.gz")[["st", "fips5", "year", "area_harvested_ha", "rel_anom", "loss"]]
ms = pd.read_csv(RESULTS / "municipal_scores_2001_2025.csv.gz")
ms = ms[ms["year"] >= 2024][["st", "fips5", "year", "area_harvested_ha", "rel_anom", "loss"]]
d = pd.concat([v1, ms], ignore_index=True).merge(f, on=["fips5", "year"], how="inner").reset_index(drop=True)


def score(w):
    return (1 - w) * d["veg"].values + w * d["rep"].values


# fitted weight, leave-one-season-out (per state: RS and PR droughts differ)
fitted = np.full(len(d), np.nan)
chosen = []
for stt in ["RS", "PR"]:
    s_rows = d["st"].values == stt
    tr_years = sorted(d.loc[s_rows & (d["year"] <= 2023), "year"].unique())
    for yr in tr_years + [None]:
        if yr is None:   # holdout seasons: fit on all of 2001-2023
            fit_rows = s_rows & (d["year"] <= 2023).values
            apply_rows = s_rows & (d["year"] >= 2024).values
        else:
            fit_rows = s_rows & (d["year"] <= 2023).values & (d["year"] != yr).values
            apply_rows = s_rows & (d["year"] == yr).values
        aucs = [roc_auc_score(d["loss"].values[fit_rows], score(w)[fit_rows]) for w in GRID]
        w = GRID[int(np.argmax(aucs))]
        fitted[apply_rows] = score(w)[apply_rows]
        chosen.append({"st": stt, "left_out": yr or "2024-2025", "w_reproductive": w})
chosen = pd.DataFrame(chosen)

scores = {k: score(w) for k, w in FIXED.items()}
scores["fitted (leave-one-season-out)"] = fitted

rows = []
for region, sts in {"RS + PR": ["RS", "PR"], "RS": ["RS"], "PR": ["PR"]}.items():
    m = d["st"].isin(sts).values & (d["year"] <= 2023).values
    g = d[m].reset_index(drop=True)
    r = year_bootstrap(g, {k: v[m] for k, v in scores.items()}, n=1000, reference="prior (0.25/0.75)")
    r.insert(0, "test", "backtest 2001-2023")
    r.insert(1, "region", region)
    rows.append(r)
    m = d["st"].isin(sts).values & (d["year"] >= 2024).values
    g = d[m].reset_index(drop=True)
    for k, v in scores.items():
        pm = point_metrics(g, v[m])
        rows += [pd.DataFrame([{"test": "holdout 2024-2025", "region": region, "index": k, "metric": mt,
                                "estimate": pm[mt]} for mt in ("auc_loss", "basis_risk")])]
res = pd.concat(rows, ignore_index=True).round(3)
res.to_csv(RESULTS / "stage_weights.csv", index=False)
chosen.to_csv(RESULTS / "stage_weights_fitted.csv", index=False)

pd.set_option("display.width", 220)
show = res[res["metric"].isin(["auc_loss", "basis_risk"])]
print(show[["test", "region", "index", "metric", "estimate", "diff_vs_ref", "diff_ci_low", "diff_ci_high"]].to_string(index=False))
print(chosen.groupby("st")["w_reproductive"].describe())
print(chosen[chosen["left_out"] == "2024-2025"])
