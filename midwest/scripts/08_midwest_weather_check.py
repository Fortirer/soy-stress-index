"""Does the stage-weighted idea travel? A weather-only check on 12 Midwest states.

    python midwest/scripts/08_midwest_weather_check.py

No satellite data here (MODIS for ~1,000 counties is the next step). The
Modelling-soybean panel already has, per county-season, water deficit and
extreme degree days in each county's own R3-R6 window (crop-model stage
dates from daily weather) and the season water deficit. So:

  Turgor weather-only = 0.25 x vegetative water deficit (season minus R3-R6)
                      + 0.75 x [water deficit + 0.5 heat + 0.5 heat x dry] in R3-R6
  (same priors as Brazil; vegetative heat is not in the panel and is left out)

Baselines: July-August rainfall (the usual weather-index insurance window)
and the Palmer Drought Severity Index for August (lower = drier).
Trend: Theil-Sen 1990-2023 per county; loss = yield > 10% below trend.
Backtest 2001-2023 with year-block bootstrap; holdout 2024-2025 with
z-scores from 2001-2023 only. Writes midwest/results/midwest_weather_check*.csv.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import theilslopes

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from turgor_us import RESULTS  # noqa: E402
from ssi.index import local_z, ssi  # noqa: E402
from ssi.uncertainty import point_metrics, year_bootstrap  # noqa: E402

SRC = Path("/home/claude/soystress-mvp/data/us_panel.csv.gz")
p = pd.read_csv(SRC)
rows = []
for code, g in p.groupby("fips5"):
    tr = g[g["year"].between(1990, 2023)]
    if len(tr) < 15:
        continue
    slope, icpt, *_ = theilslopes(tr["yield_bu_ac"], tr["year"])
    rows.append(g.assign(yield_trend=icpt + slope * g["year"]))
p = pd.concat(rows)
p = p[p["yield_trend"] > 0]
p["rel_anom"] = p["yield_bu_ac"] / p["yield_trend"] - 1
p["loss"] = (p["rel_anom"] < -0.10).astype(int)
p["area_harvested_ha"] = p["acres_harvested"] * 0.404686
p["veg_water_deficit_mm"] = (p["wb_season_deficit_mm"] - p["win_water_deficit_mm"]).clip(lower=0)
p["veg_edd"] = 0.0
p["pcp_jul_aug"] = p["pcp07"] + p["pcp08"]
need = ["win_water_deficit_mm", "win_edd", "wb_season_deficit_mm", "pcp_jul_aug", "pdsi08"]
p = p[p["year"].between(2001, 2025)].dropna(subset=need).reset_index(drop=True)


def scores(df, ref=None):
    return {"Turgor weather-only": ssi(df, ref=ref).fillna(0).values,
            "Rainfall Jul-Aug": (-local_z(df, "pcp_jul_aug", ref=ref)).fillna(0).values,
            "Palmer drought index, Aug": (-local_z(df, "pdsi08", ref=ref)).fillna(0).values}


# backtest 2001-2023 (z-scores on the same seasons, as in Brazil)
bt = p[p["year"] <= 2023].reset_index(drop=True)
out, ci = [], []
for region in ["All 12 states"] + sorted(bt["st"].unique()):
    d = bt if region == "All 12 states" else bt[bt["st"] == region].reset_index(drop=True)
    sc = scores(d)
    for k, v in sc.items():
        out.append({"test": "backtest 2001-2023", "region": region, "index": k, "n": len(d),
                    "loss_rate": d["loss"].mean(), **point_metrics(d, v)})
    if region in ("All 12 states", "IL", "IA"):
        b = year_bootstrap(d, sc, n=1000, reference="Rainfall Jul-Aug")
        ci.append(b.assign(region=region))

# holdout 2024-2025, normals from 2001-2023
ref = (p["year"] <= 2023).values
sc_all = scores(p, ref=ref)
te = p["year"] >= 2024
for region in ["All 12 states"] + sorted(p["st"].unique()):
    m = te & ((p["st"] == region) if region != "All 12 states" else True)
    d = p[m].reset_index(drop=True)
    if d["loss"].nunique() < 2:
        continue
    for k, v in sc_all.items():
        out.append({"test": "holdout 2024-2025", "region": region, "index": k, "n": len(d),
                    "loss_rate": d["loss"].mean(), **point_metrics(d, v[m.values])})

res = pd.DataFrame(out).round(3)
res.to_csv(RESULTS / "midwest_weather_check.csv", index=False)
pd.concat(ci).round(3).to_csv(RESULTS / "midwest_weather_check_ci.csv", index=False)
pd.set_option("display.width", 200)
print(res.pivot_table(index=["test", "region"], columns="index", values="auc_loss", sort=False).round(3))
print(res.pivot_table(index=["test", "region"], columns="index", values="basis_risk", sort=False).round(3))
print(pd.concat(ci).round(3).query("metric != 'state_year_r'").to_string(index=False))
