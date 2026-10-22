"""CHIRPS daily rainfall per RS municipality, July 2000 - May 2025 (issue #7).

    python scripts/21_chirps_rs.py [--workers 8]

CHIRPS v2.0 (UC Santa Barbara Climate Hazards Center): satellite + rain-gauge
daily rainfall at 0.05 deg (~5 km), against ~50 km for NASA POWER. Reads only
the RS window of each daily cloud-optimised GeoTIFF, then averages the cells
of each municipality (nearest cell for municipalities smaller than a cell).
Resumable: one file per year in data/chirps/parts/. Writes
data/chirps/chirps_rs_daily.csv.gz (rows = days, columns = IBGE codes).
"""
import argparse
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ssi.config import DATA  # noqa: E402
from ssi.data import load_boundaries  # noqa: E402

BASE = "https://data.chc.ucsb.edu/products/CHIRPS-2.0/global_daily/cogs/p05/{y}/chirps-v2.0.{y}.{m:02d}.{d:02d}.cog"
ap = argparse.ArgumentParser()
ap.add_argument("--start", default="2000-07-01")
ap.add_argument("--end", default="2025-05-31")
ap.add_argument("--workers", type=int, default=8)
args = ap.parse_args()

out_dir = DATA / "chirps" / "parts"
out_dir.mkdir(parents=True, exist_ok=True)
feats = [f for f in load_boundaries()["features"] if f["properties"]["st"] == "RS"]
lons = [x for f in feats for x, _ in f["geometry"]["coordinates"][0]]
lats = [y for f in feats for _, y in f["geometry"]["coordinates"][0]]
W, S, E, N = min(lons) - 0.1, min(lats) - 0.1, max(lons) + 0.1, max(lats) + 0.1


def zones_for(transform, shape):
    from rasterio.features import rasterize
    z = rasterize([(f["geometry"], int(f["id"])) for f in feats], out_shape=shape, transform=transform,
                  fill=0, dtype="int32")
    cells = {}
    for f in feats:
        code = int(f["id"])
        idx = np.flatnonzero(z.ravel() == code)
        if idx.size == 0:   # municipality smaller than a 0.05 deg cell: nearest cell to its centre
            r = np.array(f["geometry"]["coordinates"][0])
            col, row = ~transform * (r[:, 0].mean(), r[:, 1].mean())
            idx = np.array([int(row) * shape[1] + int(col)])
        cells[code] = idx
    return cells


def read_day(day):
    import rasterio
    from rasterio.windows import from_bounds
    url = "/vsicurl/" + BASE.format(y=day.year, m=day.month, d=day.day)
    for attempt in range(4):
        try:
            with rasterio.open(url) as ds:
                win = from_bounds(W, S, E, N, ds.transform).round_offsets().round_lengths()
                a = ds.read(1, window=win).astype("float32")
                a[a < 0] = np.nan
                return day, a, ds.window_transform(win)
        except Exception:
            import time
            time.sleep(3 * (attempt + 1))
    return day, None, None


days = pd.date_range(args.start, args.end, freq="D")
cells = None
for year, ds_year in pd.Series(days).groupby(pd.Series(days).dt.year):
    fp = out_dir / f"{year}.csv.gz"
    if fp.exists():
        continue
    rows = {}
    with ThreadPoolExecutor(args.workers) as pool:
        for day, a, tr in pool.map(read_day, list(ds_year)):
            if a is None:
                continue
            if cells is None:
                cells = zones_for(tr, a.shape)
            flat = a.ravel()
            rows[day] = {c: float(np.nanmean(flat[i])) if np.isfinite(flat[i]).any() else np.nan
                         for c, i in cells.items()}
    pd.DataFrame.from_dict(rows, orient="index").sort_index().round(2).to_csv(fp)
    print(year, len(rows), "days", flush=True)

parts = sorted(out_dir.glob("*.csv.gz"))
allp = pd.concat([pd.read_csv(p, index_col=0, parse_dates=True) for p in parts]).sort_index()
allp.to_csv(DATA / "chirps" / "chirps_rs_daily.csv.gz")
print("written", allp.shape)
