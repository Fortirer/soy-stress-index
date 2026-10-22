"""Validate the index against a partner's real field yields (co-op pilot).

    python scripts/13_field_validation.py --fields partner/fields.geojson --yields partner/yields.csv

fields.geojson : polygons with property "field_id"
yields.csv     : field_id, harvest_year, yield_kg_ha [, fips5]
Seasons 2018-2025 work (Sentinel-2 L2A from 2017). At least 3 seasons per field.

Outputs (in --out, default results/field_validation/):
  field_features.csv   stages, NDVI and weather per field-season
  field_scores.csv     field index, municipal index, yields, loss flags
  field_metrics.csv    AUC, basis risk and within-season ranking, field vs municipal index

--demo runs the whole pipeline on 4 pilot plots with SYNTHETIC yields, only
to check that it works end to end. Demo numbers are not results.
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ssi.config import DATA, RESULTS  # noqa: E402
from ssi.fieldval import (SEASONS_MIN, field_index, field_season_features,  # noqa: E402
                          validate, yield_anomaly)
from ssi.pilot import load_season  # noqa: E402
from ssi.weather import daily_indicators, fetch_power  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--fields")
ap.add_argument("--yields")
ap.add_argument("--out", default=str(RESULTS / "field_validation"))
ap.add_argument("--demo", action="store_true")
args = ap.parse_args()
out = Path(args.out)
cache = DATA / "field_cache"
cache.mkdir(parents=True, exist_ok=True)

if args.demo:
    out = RESULTS / "field_validation_demo"
    gj = json.loads((DATA / "pilot_fields.geojson").read_text())
    feats = []
    for f in gj["features"]:
        if f["properties"]["municipality"] == "Cruz Alta" and f["properties"]["field"] <= 4:
            f["properties"]["field_id"] = f"CA{f['properties']['field']}"
            feats.append(f)
    fields = {"type": "FeatureCollection", "features": feats}
    yields = None                      # filled in after NDVI is read (synthetic)
    years = [2021, 2022, 2023]
else:
    fields = json.loads(Path(args.fields).read_text())
    yields = pd.read_csv(args.yields)
    years = sorted(yields["harvest_year"].unique())
out.mkdir(parents=True, exist_ok=True)
# one polygon per field: if a field comes in several parts, keep the largest
_best = {}
for f in fields["features"]:
    ring = np.array(f["geometry"]["coordinates"][0])
    area = 0.5 * abs(np.dot(ring[:, 0], np.roll(ring[:, 1], 1)) - np.dot(ring[:, 1], np.roll(ring[:, 0], 1)))
    fid = f["properties"]["field_id"]
    if fid not in _best or area > _best[fid][0]:
        _best[fid] = (area, f)
fields["features"] = [f for _, f in _best.values()]


def field_series(feature, yr):
    """Median Sentinel-2 NDVI over the field polygon for every clear date of a season."""
    from rasterio.features import geometry_mask
    from rasterio.warp import transform_geom
    from affine import Affine
    fid = feature["properties"]["field_id"]
    fp = cache / f"{fid}_{yr}.npz"
    ring = np.array(feature["geometry"]["coordinates"][0])
    pad = 0.002
    bbox = [ring[:, 0].min() - pad, ring[:, 1].min() - pad, ring[:, 0].max() + pad, ring[:, 1].max() + pad]
    if fp.exists():
        z = np.load(fp)
        t, nd, tr = pd.to_datetime(z["times"]), z["ndvi"], Affine(*z["transform"][:6])
    else:
        t, nd, ds = load_season(bbox, yr)
        tr = ds.odc.geobox.transform
        np.savez_compressed(fp, times=t.values, ndvi=nd, transform=np.array(list(tr)[:6], dtype=float))
    geom = transform_geom("EPSG:4326", "EPSG:32722", feature["geometry"])
    inside = ~geometry_mask([geom], out_shape=nd.shape[1:], transform=tr)
    rows = []
    for i, d in enumerate(t):
        v = nd[i][inside]
        ok = np.isfinite(v)
        if inside.sum() and ok.mean() >= 0.5:
            rows.append((d.normalize(), float(np.median(v[ok]))))
    return pd.DataFrame(rows, columns=["date", "ndvi"])


def field_weather(feature):
    fid = feature["properties"]["field_id"]
    fp = cache / f"{fid}_power.csv.gz"
    ring = np.array(feature["geometry"]["coordinates"][0])
    lat, lon = ring[:, 1].mean(), ring[:, 0].mean()
    if fp.exists():
        w = pd.read_csv(fp, index_col=0, parse_dates=True)
    else:
        w = fetch_power(lat, lon, f"{min(years) - 1}-07-01", f"{max(years)}-05-31")
        w.to_csv(fp)
    return daily_indicators(w, lat)


rows = []
for f in fields["features"]:
    fid = f["properties"]["field_id"]
    ind = field_weather(f)
    for yr in years:
        s = field_series(f, yr)
        feat = field_season_features(s["date"], s["ndvi"], ind, yr) if len(s) >= 6 else None
        rows.append({"field_id": fid, "harvest_year": yr, "n_clear_dates": len(s), **(feat or {})})
        print(fid, yr, "ok" if feat else "no clear season", flush=True)
feat = pd.DataFrame(rows)
feat.to_csv(out / "field_features.csv", index=False)

if args.demo:
    # SYNTHETIC yields: 3,600 kg/ha scaled by reproductive NDVI plus noise. Pipeline test only.
    rng = np.random.default_rng(0)
    yields = feat[["field_id", "harvest_year"]].copy()
    yields["yield_kg_ha"] = 3600 * (feat["ndvi_reproductive"].fillna(0.6) / 0.8) + rng.normal(0, 250, len(feat))
    yields["fips5"] = 4306106

d = feat.merge(yields, on=["field_id", "harvest_year"], how="inner")
n_seasons = d.dropna(subset=["ndvi_reproductive"]).groupby("field_id").size()
d = d[d["field_id"].isin(n_seasons[n_seasons >= SEASONS_MIN].index)].reset_index(drop=True)
d = yield_anomaly(d)
d["field_index"] = field_index(d).values

# municipal index for the same seasons (what a partner could buy without field data)
muni_fp = RESULTS / "municipal_scores_2001_2025.csv.gz"
cols = {"Turgor field index": "field_index"}
if "fips5" in d.columns and muni_fp.exists():
    m = pd.read_csv(muni_fp)[["fips5", "year", "Turgor index"]]
    m = m.rename(columns={"year": "harvest_year", "Turgor index": "municipal_index"})
    d = d.merge(m, on=["fips5", "harvest_year"], how="left")
    cols["Turgor municipal index"] = "municipal_index"
d.to_csv(out / "field_scores.csv", index=False)
res = validate(d, cols).round(3)
res.to_csv(out / "field_metrics.csv", index=False)
print(res.to_string(index=False))
if args.demo:
    print("\nDEMO: yields are synthetic. These numbers only show the pipeline runs.")
