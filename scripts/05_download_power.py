"""Daily NASA POWER weather per municipality and stress by crop stage.

    python scripts/05_download_power.py --states RS PR

Needs network access to power.larc.nasa.gov. Daily series are cached in
data/power/<code>.csv.gz. Stage windows come from data/ndvi_stages.csv.gz
(run script 04 first); seasons without a clear NDVI curve fall back to a
calendar window (vegetative Nov-Dec, reproductive Jan-Feb).
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ssi.config import DATA  # noqa: E402
from ssi.data import load_boundaries  # noqa: E402
from ssi.weather import daily_indicators, fetch_power, stage_weather  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--states", nargs="+", default=["RS", "PR"])
ap.add_argument("--start", default="2000-09-01")
ap.add_argument("--end", default="2023-05-31")
ap.add_argument("--workers", type=int, default=6)
ap.add_argument("--prefetch-only", action="store_true",
                help="only download daily weather (can run before script 04 finishes)")
args = ap.parse_args()

cache = DATA / "power"
cache.mkdir(parents=True, exist_ok=True)
geo = load_boundaries()
feats = [f for f in geo["features"] if f["properties"]["st"] in args.states]


def centroid(f):
    ring = np.array(f["geometry"]["coordinates"][0])
    return ring[:, 1].mean(), ring[:, 0].mean()


def prefetch(f):
    fp = cache / f"{int(f['id'])}.csv.gz"
    if not fp.exists():
        lat, lon = centroid(f)
        fetch_power(lat, lon, args.start, args.end).to_csv(fp)
    return fp


from concurrent.futures import ThreadPoolExecutor  # noqa: E402

with ThreadPoolExecutor(args.workers) as pool:
    for i, _ in enumerate(pool.map(prefetch, feats), 1):
        if i % 50 == 0:
            print(f"downloaded {i}/{len(feats)}", flush=True)
if args.prefetch_only:
    sys.exit(0)

stages = pd.read_csv(DATA / "ndvi_stages.csv.gz",
                     parse_dates=["veg_start", "veg_end", "rep_start", "rep_end"])
stages = stages.set_index(["fips5", "year"])
rows = []
for i, f in enumerate(feats, 1):
    code = int(f["id"])
    lat, _ = centroid(f)
    w = pd.read_csv(cache / f"{code}.csv.gz", index_col=0, parse_dates=True)
    ind = daily_indicators(w, lat)
    for yr in range(int(args.start[:4]) + 1, int(args.end[:4]) + 1):
        if (code, yr) in stages.index:
            st = stages.loc[(code, yr)]
            win, source = {k: st[k] for k in ["veg_start", "veg_end", "rep_start", "rep_end"]}, "ndvi"
        else:
            win = {"veg_start": f"{yr - 1}-11-01", "veg_end": f"{yr - 1}-12-31",
                   "rep_start": f"{yr}-01-01", "rep_end": f"{yr}-02-28"}
            source = "calendar"
        rows.append({"fips5": code, "year": yr, "window_source": source,
                     **{f"sw_{k}": v for k, v in stage_weather(ind, win).items()}})
    if i % 25 == 0:
        print(f"{i}/{len(feats)} municipalities", flush=True)

pd.DataFrame(rows).to_csv(DATA / "stage_weather.csv.gz", index=False)
print("-> data/stage_weather.csv.gz")
