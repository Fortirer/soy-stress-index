"""Download MODIS NDVI per municipality and derive crop stages.

    python scripts/04_download_modis.py --states RS PR --first 2001 --last 2023

Needs network access to planetarycomputer.microsoft.com and *.blob.core.windows.net.
Resumable: seasons already in data/modis_ndvi_<ST>.csv.gz are skipped.
"""
import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ssi.config import DATA  # noqa: E402
from ssi.data import load_boundaries  # noqa: E402
from ssi.satellite import modis_season_ndvi, stage_table  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--states", nargs="+", default=["RS", "PR"])
ap.add_argument("--first", type=int, default=2001)
ap.add_argument("--last", type=int, default=2023)
ap.add_argument("--resolution", type=float, default=0.01, help="degrees; 0.0025 = full 250 m")
args = ap.parse_args()

geo = load_boundaries()
all_series = []
for st in args.states:
    feats = [f for f in geo["features"] if f["properties"]["st"] == st]
    out = DATA / f"modis_ndvi_{st}.csv.gz"
    done = pd.read_csv(out, parse_dates=["date"]) if out.exists() else pd.DataFrame()
    have = set(done["harvest_year"]) if len(done) else set()
    for yr in range(args.first, args.last + 1):
        if yr in have:
            continue
        print(f"{st} harvest {yr} ...", flush=True)
        s = modis_season_ndvi(feats, yr, args.resolution)
        if len(s):
            done = pd.concat([done, s], ignore_index=True)
            done.to_csv(out, index=False)
    all_series.append(done)

series = pd.concat(all_series, ignore_index=True)
stages = stage_table(series)
stages.to_csv(DATA / "ndvi_stages.csv.gz", index=False)
print(f"stages for {len(stages):,} municipality-seasons -> data/ndvi_stages.csv.gz")
