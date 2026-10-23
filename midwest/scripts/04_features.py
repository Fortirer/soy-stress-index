"""Index inputs for every Illinois county-season, 2001-2025.

    python midwest/scripts/04_features.py

1. Full-season features (v1): daily weather summed over each season's own
   NDVI-detected windows, plus stage NDVI.
2. As-of features (the product): typical windows and data latency, on
   15 Jun ... 1 Oct. For 2001-2023 the typical windows leave the season out;
   for the 2024-2025 holdout they are the median of 2001-2023 only.
Writes midwest/data/il_full_features.csv.gz and il_asof_features.csv.gz.
"""
import json
import sys
from multiprocessing import Pool
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from turgor_us import (DATA, DATES, TEST, TRAIN, WINDOWS, asof_features, centroid,  # noqa: E402
                       full_season_features, typical_windows)
from ssi.weather import daily_indicators  # noqa: E402

stages = pd.read_csv(DATA / "il_ndvi_stages.csv.gz")
ndvi = pd.read_csv(DATA / "modis_ndvi_IL.csv.gz", parse_dates=["date"])
st_tr = stages[stages["year"].isin(TRAIN)]

typ_tr = typical_windows(st_tr)
tw = st_tr[["fips5", "year"] + WINDOWS].copy()
for c in WINDOWS:
    tw[c] = (pd.to_datetime(tw[c]) - pd.to_datetime(tw["year"].astype(str) + "-04-01")).dt.days
med = tw.groupby("fips5")[WINDOWS].median()
typ_te = pd.concat([med.assign(year=y) for y in TEST]).reset_index()
typ = pd.concat([typ_tr, typ_te]).set_index(["fips5", "year"])
fallback = med.median()
print("typical windows, days after 1 April (state median):", fallback.round(0).to_dict())

feats = json.load(open(DATA / "il_counties.geojson"))["features"]
nd_by = {c: g for c, g in ndvi.groupby("fips5")}
st_by = {c: g for c, g in stages.groupby("fips5")}
YEARS = list(TRAIN) + TEST


def one(f):
    code = int(f["id"])
    lat, _ = centroid(f)
    w = pd.read_csv(DATA / "power" / f"{code}.csv.gz", index_col=0, parse_dates=True)
    ind = daily_indicators(w, lat)
    nd = nd_by.get(code, pd.DataFrame(columns=["date", "ndvi", "year"]))
    a = asof_features(ind, nd, code, YEARS, DATES, typ, fallback)
    full = full_season_features(ind, st_by.get(code, pd.DataFrame()), code, YEARS)
    return a, full


if __name__ == "__main__":
    with Pool(8) as p:
        res = p.map(one, feats)
    pd.DataFrame([r for a, _ in res for r in a]).to_csv(DATA / "il_asof_features.csv.gz", index=False)
    full = pd.DataFrame([r for _, f in res for r in f])
    full.to_csv(DATA / "il_full_features.csv.gz", index=False)
    print(full["window_source"].value_counts().to_dict())
