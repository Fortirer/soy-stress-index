"""MODIS NDVI for RS at full 250 m (issue #7), optionally limited to a soybean mask.

    python scripts/20_modis_rs_highres.py --years 2001 2025            # 250 m
    python scripts/20_modis_rs_highres.py --years 2001 2025 --soymask  # + MapBiomas soybean pixels

Resumable: one file per season in data/rs_experiments/modis250[_soy]/, then
merged into data/modis_ndvi_RS_250m.csv.gz (or _soy).
"""
import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ssi.config import DATA  # noqa: E402
from ssi.data import load_boundaries  # noqa: E402
from ssi.satellite import modis_season_ndvi  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--years", nargs=2, type=int, default=[2001, 2025])
ap.add_argument("--step", type=int, default=1)
ap.add_argument("--offset", type=int, default=0)
ap.add_argument("--soymask", action="store_true")
args = ap.parse_args()

tag = "modis250_soy" if args.soymask else "modis250"
parts = DATA / "rs_experiments" / tag
parts.mkdir(parents=True, exist_ok=True)
fs = [f for f in load_boundaries()["features"] if f["properties"]["st"] == "RS"]
for yr in range(args.years[0] + args.offset, args.years[1] + 1, args.step):
    fp = parts / f"{yr}.csv.gz"
    if fp.exists():
        continue
    extra = {}
    if args.soymask:
        from ssi.mapbiomas import soy_mask_loader
        extra["extra_mask"] = soy_mask_loader(yr - 1)
    s = modis_season_ndvi(fs, yr, 0.0025, **extra)
    s.to_csv(fp, index=False)
    print(tag, yr, len(s), flush=True)

done = sorted(parts.glob("*.csv.gz"))
if len(done) == args.years[1] - args.years[0] + 1:
    out = DATA / ("modis_ndvi_RS_soy.csv.gz" if args.soymask else "modis_ndvi_RS_250m.csv.gz")
    pd.concat([pd.read_csv(p) for p in done]).to_csv(out, index=False)
    print("merged ->", out)
