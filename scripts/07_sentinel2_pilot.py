"""Sentinel-2 field pilot: 2020/21 (good) vs 2021/22 (drought) in three RS municipalities.

    python scripts/07_sentinel2_pilot.py

For each municipality, a 10 x 10 km window at the municipality centre:
  1. detect soybean field blocks from the 2020/21 season itself (Sentinel-2, 20 m)
  2. follow each block's NDVI through both seasons
  3. read crop stages from each block's curve and compare reproductive-stage NDVI
Writes results/pilot_*.csv, data/pilot_fields.geojson.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ssi.config import DATA, RESULTS  # noqa: E402
from ssi.data import load_boundaries, load_panel  # noqa: E402
from ssi.pilot import (field_area_ha, field_blocks, field_polygons, field_series,  # noqa: E402
                       load_season, soybean_mask, stage_summary)

MUNICIPALITIES = {4322202: "Tupanciretã", 4306106: "Cruz Alta", 4306601: "Dom Pedrito"}
HALF = 0.045            # ~10 km window
N_FIELDS = 5
REF, DRY = 2021, 2022   # harvest years: 2020/21 good, 2021/22 drought

CACHE = DATA / "s2_cache"
CACHE.mkdir(exist_ok=True)


def cached_season(code, bbox, yr):
    """Sentinel-2 stacks are slow to load, so keep them as .npz between runs."""
    from affine import Affine
    fp = CACHE / f"{code}_{yr}.npz"
    if fp.exists():
        z = np.load(fp)
        return pd.to_datetime(z["times"]), z["ndvi"], Affine(*z["transform"][:6])
    t, nd, ds = load_season(bbox, yr)
    tr = ds.odc.geobox.transform
    np.savez_compressed(fp, times=t.values, ndvi=nd, transform=np.array(list(tr)[:6], dtype=float))
    return t, nd, tr


geo = {f["id"]: f for f in load_boundaries()["features"]}
panel = load_panel()
series_rows, field_rows, polys = [], [], []

for code, name in MUNICIPALITIES.items():
    ring = np.array(geo[code]["geometry"]["coordinates"][0])
    lon, lat = ring[:, 0].mean(), ring[:, 1].mean()
    bbox = [lon - HALF, lat - HALF, lon + HALF, lat + HALF]
    print(f"{name}: loading {REF} season", flush=True)
    t_ref, nd_ref, tr_ref = cached_season(code, bbox, REF)
    fields = field_blocks(soybean_mask(t_ref, nd_ref, REF), N_FIELDS)
    areas = field_area_ha(fields)
    print(f"  {fields.max()} field plots, {sum(areas.values()):.0f} ha", flush=True)
    polys += field_polygons(fields, tr_ref, name)
    print(f"{name}: loading {DRY} season", flush=True)
    t_dry, nd_dry, _ = cached_season(code, bbox, DRY)
    assert nd_dry.shape[1:] == nd_ref.shape[1:]
    for yr, t, nd in [(REF, t_ref, nd_ref), (DRY, t_dry, nd_dry)]:
        s = field_series(t, nd, fields)
        s["municipality"], s["harvest_year"] = name, yr
        series_rows.append(s)
        for f, g in s.groupby("field"):
            st = stage_summary(g, yr)
            field_rows.append({"municipality": name, "fips5": code, "field": f,
                               "area_ha": round(areas[f], 1), "harvest_year": yr,
                               "n_clear_dates": len(g), **(st or {})})

series = pd.concat(series_rows, ignore_index=True)
fields_df = pd.DataFrame(field_rows)
series.to_csv(RESULTS / "pilot_field_series.csv", index=False)
fields_df.to_csv(RESULTS / "pilot_field_stages.csv", index=False)
(DATA / "pilot_fields.geojson").write_text(json.dumps({"type": "FeatureCollection", "features": polys}))

# field change 2022 vs 2021, next to municipal MODIS and IBGE yield
w = fields_df.pivot_table(index=["municipality", "fips5", "field", "area_ha"], columns="harvest_year",
                          values=["ndvi_reproductive", "ndvi_peak"]).reset_index()
w.columns = ["_".join(str(c) for c in col if c != "") for col in w.columns]
w["rep_ndvi_change"] = w[f"ndvi_reproductive_{DRY}"] - w[f"ndvi_reproductive_{REF}"]
w["rep_ndvi_change_pct"] = 100 * w["rep_ndvi_change"] / w[f"ndvi_reproductive_{REF}"]
stg = pd.read_csv(DATA / "ndvi_stages.csv.gz")
mod = stg[stg.fips5.isin(MUNICIPALITIES)].pivot(index="fips5", columns="year", values="ndvi_reproductive")
y = panel[panel.fips5.isin(MUNICIPALITIES)].pivot(index="fips5", columns="year", values="rel_anom")
muni = pd.DataFrame({
    "modis_rep_ndvi_change_pct": 100 * (mod[DRY] - mod[REF]) / mod[REF],
    "ibge_yield_vs_trend_2021_pct": 100 * y[REF], "ibge_yield_vs_trend_2022_pct": 100 * y[DRY]})
w = w.merge(muni, left_on="fips5", right_index=True)
w.round(3).to_csv(RESULTS / "pilot_field_change.csv", index=False)
pd.set_option("display.width", 200)
print(w[["municipality", "field", "area_ha", "rep_ndvi_change_pct", "modis_rep_ndvi_change_pct",
         "ibge_yield_vs_trend_2021_pct", "ibge_yield_vs_trend_2022_pct"]].round(1).to_string(index=False))
