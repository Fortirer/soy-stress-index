"""Version 1 of the index: satellite stages + NDVI + daily weather by stage.

    python scripts/06_full_index.py

Needs data/ndvi_stages.csv.gz (script 04) and data/stage_weather.csv.gz
(script 05). Compares on the same municipality-seasons (harvests 2001-2023):
  - Rainfall index           low Jan-Feb rain
  - SSI v0                   calendar windows (Jan-Feb), weather only
  - NDVI only                reproductive-window NDVI anomaly
  - SSI v1, weather only     daily weather summed over satellite-detected stages
  - SSI v1, full             + NDVI in each stage
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ssi.config import DATA, DROUGHT_HARVESTS, FOCUS_STATES, RESULTS  # noqa: E402
from ssi.data import load_panel  # noqa: E402
from ssi.evaluate import drought_year_table, metrics  # noqa: E402
from ssi.index import local_z, rainfall_index, ssi  # noqa: E402

panel = load_panel()
panel = panel[panel["st"].isin(FOCUS_STATES) & (panel["year"] >= 2001)]
stg = pd.read_csv(DATA / "ndvi_stages.csv.gz")
wx = pd.read_csv(DATA / "stage_weather.csv.gz")
ALL = panel.merge(stg[["fips5", "year", "ndvi_vegetative", "ndvi_reproductive", "ndvi_peak"]],
                  on=["fips5", "year"], how="inner").merge(wx, on=["fips5", "year"], how="inner")


def score_all(df: pd.DataFrame) -> dict:
    no_ndvi = df.drop(columns=[c for c in df if c.startswith("ndvi_")])
    v1_in = df.copy()
    v1_in["veg_water_deficit_mm"] = df["sw_veg_water_deficit_mm"]
    v1_in["win_water_deficit_mm"] = df["sw_rep_water_deficit_mm"]
    v1_in["veg_edd"] = df["sw_veg_edd"]
    v1_in["win_edd"] = df["sw_rep_edd"]
    return {"Rainfall index": rainfall_index(df).values,
            "SSI v0 (calendar windows)": ssi(no_ndvi).values,
            "NDVI only": (-local_z(df, "ndvi_reproductive")).fillna(0).values,
            "SSI v1 weather (satellite stages)": ssi(v1_in.drop(columns=[c for c in v1_in if c.startswith("ndvi_")])).values,
            "SSI v1 full (+ NDVI)": ssi(v1_in).values}


rows, keep = [], {}
for region, states in {"RS + PR": FOCUS_STATES, "RS": ["RS"], "PR": ["PR"]}.items():
    df = ALL[ALL["st"].isin(states)].reset_index(drop=True)
    scores = score_all(df)
    rows += [{"region": region, "index": k, **metrics(v, df)} for k, v in scores.items()]
    if region == "RS + PR":
        keep = (df, scores)

res = pd.DataFrame(rows).round(3)
res.to_csv(RESULTS / "v1_metrics.csv", index=False)
df, scores = keep
drought = drought_year_table(df, scores, DROUGHT_HARVESTS)
drought.to_csv(RESULTS / "v1_drought_years.csv", index=False)
out = df[["st", "fips5", "county", "year", "area_harvested_ha", "rel_anom", "loss"]].copy()
for k, v in scores.items():
    out[k] = v
out.round(4).to_csv(RESULTS / "v1_scores_rs_pr.csv.gz", index=False)

pd.set_option("display.width", 180)
print(res.to_string(index=False))
print()
print(drought.to_string(index=False))
