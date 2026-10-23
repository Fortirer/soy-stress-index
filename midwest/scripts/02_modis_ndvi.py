"""MODIS NDVI per Illinois county, corn-soybean pixels only, and crop stages.

    python midwest/scripts/02_modis_ndvi.py --first 2001 --last 2025

Cropland mask: USDA Cropland Data Layer (CDL, 30 m) on Planetary Computer,
2019-2021. A 0.01° pixel is kept when corn (class 1) plus soybean (class 5)
cover at least half of it on average. The CDL in Planetary Computer stops at
2021, so one static mask is used for every season.
Then, like Brazil, only pixels with a clear summer canopy cycle (low NDVI in
mid-April to May, high in July-August) are averaged.
Writes midwest/data/modis_ndvi_IL.csv.gz and il_ndvi_stages.csv.gz. Resumable.
"""
import argparse
import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from turgor_us import DATA, season_dates, stage_table  # noqa: E402
from ssi.satellite import NDVI_BAND, QA_BAND, catalog, municipality_raster, zonal_mean  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--first", type=int, default=2001)
ap.add_argument("--last", type=int, default=2025)
ap.add_argument("--resolution", type=float, default=0.01)
ap.add_argument("--part", default="", help="write to a separate part file (parallel runs)")
ap.add_argument("--stages-only", action="store_true", help="merge part files and compute stages")
args = ap.parse_args()

feats = json.load(open(DATA / "il_counties.geojson"))["features"]
lons = [x for f in feats for x, _ in f["geometry"]["coordinates"][0]]
lats = [y for f in feats for _, y in f["geometry"]["coordinates"][0]]
bbox = [min(lons), min(lats), max(lons), max(lats)]

from odc.geo.geobox import GeoBox  # noqa: E402
import odc.stac  # noqa: E402

geobox = GeoBox.from_bbox(bbox, crs="EPSG:4326", resolution=args.resolution)
zones = municipality_raster(feats, geobox)
cat = catalog()

mask_file = DATA / "il_rowcrop_share.npy"
if not mask_file.exists():
    k = 5                                   # 0.002° CDL grid, 5 x 5 blocks per 0.01° pixel
    from affine import Affine
    fine = GeoBox((geobox.shape[0] * k, geobox.shape[1] * k), geobox.transform * Affine.scale(1 / k), geobox.crs)
    shares = []
    for yr in (2019, 2020, 2021):
        items = list(cat.search(collections=["usda-cdl"], bbox=bbox, datetime=str(yr)).items())
        items = [i for i in items if i.properties.get("usda_cdl:type") == "cropland"]
        ds = odc.stac.load(items, bands=["cropland"], geobox=fine, resampling="nearest", dtype="uint8")
        a = ds["cropland"].max("time").values
        row = np.isin(a, [1, 5]).astype("float32")
        h, w = geobox.shape
        row = row[: h * k, : w * k].reshape(h, k, w, k).mean(axis=(1, 3))
        shares.append(row)
        print(f"CDL {yr}: mean corn+soy share {row[zones > 0].mean():.2f}", flush=True)
    np.save(mask_file, np.mean(shares, axis=0))
rowcrop = np.load(mask_file) >= 0.5
print(f"row-crop pixels: {rowcrop[zones > 0].mean():.0%} of Illinois", flush=True)

out = DATA / f"modis_ndvi_IL{args.part}.csv.gz"
if args.stages_only:
    parts = sorted(DATA.glob("modis_ndvi_IL*.csv.gz"))
    allp = pd.concat([pd.read_csv(f, parse_dates=["date"]) for f in parts], ignore_index=True)
    allp = allp.drop_duplicates(["fips5", "date"]).sort_values(["fips5", "date"])
    for f in parts:
        f.unlink()
    allp.to_csv(DATA / "modis_ndvi_IL.csv.gz", index=False)
    args.first, args.last, out = 0, -1, DATA / "modis_ndvi_IL.csv.gz"
done = pd.read_csv(out, parse_dates=["date"]) if out.exists() else pd.DataFrame()
have = set(done["year"]) if len(done) else set()
for yr in range(args.first, args.last + 1):
    if yr in have:
        continue
    start, end = season_dates(yr)
    items = list(cat.search(collections=["modis-13Q1-061"], bbox=bbox, datetime=f"{start}/{end}").items())
    common = dict(geobox=geobox, groupby="solar_day")
    for attempt in range(4):
        try:
            nd_ds = odc.stac.load(items, bands=[NDVI_BAND], resampling="average", dtype="float32", **common)
            qa_ds = odc.stac.load(items, bands=[QA_BAND], resampling="nearest", dtype="int16", **common)
            break
        except Exception as e:     # transient 403 on signed URLs
            print("retry", yr, e, flush=True)
            cat = catalog()
            items = list(cat.search(collections=["modis-13Q1-061"], bbox=bbox, datetime=f"{start}/{end}").items())
    times = pd.to_datetime(nd_ds.time.values)
    nd = nd_ds[NDVI_BAND].values.astype("float32")
    qa = qa_ds[QA_BAND].values
    nd = np.where((qa >= 0) & (qa <= 1) & (nd > -2000), nd * 1e-4, np.nan)
    low = (times >= f"{yr}-04-15") & (times <= f"{yr}-05-31")
    high = (times >= f"{yr}-07-01") & (times <= f"{yr}-08-31")
    if low.sum() and high.sum():
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            amp = np.nanmax(nd[high], axis=0) - np.nanmin(nd[low], axis=0)
        mask = rowcrop & (np.nan_to_num(amp, nan=0) >= 0.15)
    else:      # 2025: July-October composites are missing from the archive
        print(f"{yr}: no July-August composites in the archive; row-crop mask only", flush=True)
        mask = rowcrop
    rows = []
    for i, t in enumerate(times):
        z = zonal_mean(np.where(mask, nd[i], np.nan), zones)
        z["date"] = t.normalize()
        rows.append(z)
    s = pd.concat(rows, ignore_index=True).assign(year=yr)
    done = pd.concat([done, s], ignore_index=True)
    done.to_csv(out, index=False)
    print(f"{yr}: {len(times)} composites, {s.fips5.nunique()} counties", flush=True)

stages = stage_table(done)
stages.to_csv(DATA / "il_ndvi_stages.csv.gz", index=False)
print(f"stages for {len(stages):,} county-seasons; median peak day-of-year "
      f"{pd.to_datetime(stages['peak']).dt.dayofyear.median():.0f}")
