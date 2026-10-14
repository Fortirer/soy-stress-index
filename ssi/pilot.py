"""Field-scale pilot with Sentinel-2: detect soybean field blocks from the
imagery itself and follow their NDVI through two seasons.

No public field boundaries are used. A "field block" is a contiguous patch of
pixels with a clear soybean cycle in the reference season (bare or low
cover in Oct-Nov, dense canopy in Jan-Feb), at least MIN_HA in size. Blocks
can join neighbouring fields of the same crop; real farm polygons (CAR or
co-op data) would replace this step in a commercial pilot.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import ndimage

from .config import SENTINEL2
from .satellite import catalog, stage_windows

RES_M = 20                      # 20 m is plenty for fields and keeps reads small
CRS = "EPSG:32722"              # UTM 22S covers the RS soybean belt
CLEAR_SCL = [4, 5]              # vegetation, not-vegetated (bare soil)
MIN_HA = 20


def load_season(bbox: list[float], harvest_year: int, max_cloud: int = 70):
    """NDVI stack (time, y, x) for Oct-Apr of one season, clouds masked."""
    import odc.stac
    cat = catalog()
    items = list(cat.search(collections=[SENTINEL2], bbox=bbox,
                            datetime=f"{harvest_year - 1}-10-01/{harvest_year}-04-30",
                            query={"eo:cloud_cover": {"lt": max_cloud}}).items())
    ds = odc.stac.load(items, bands=["B04", "B08", "SCL"], bbox=bbox, crs=CRS,
                       resolution=RES_M, groupby="solar_day", dtype="float32",
                       resampling={"SCL": "nearest", "*": "average"})
    red, nir, scl = ds["B04"].values, ds["B08"].values, ds["SCL"].values
    ndvi = np.where(np.isin(scl, CLEAR_SCL), (nir - red) / (nir + red + 1e-6), np.nan)
    ndvi[(ndvi < -0.2) | (ndvi > 1)] = np.nan
    return pd.to_datetime(ds.time.values), ndvi.astype("float32"), ds


def soybean_mask(times, ndvi, harvest_year: int) -> np.ndarray:
    y0 = harvest_year - 1
    early = (times >= f"{y0}-10-15") & (times <= f"{y0}-11-30")
    peak = (times >= f"{harvest_year}-01-01") & (times <= f"{harvest_year}-02-28")
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        low = np.nanmin(ndvi[early], axis=0)
        high = np.nanpercentile(ndvi[peak], 75, axis=0)
    return (low < 0.45) & (high > 0.75)


def field_blocks(mask: np.ndarray, n: int = 5, cell_m: int = 600,
                 min_share: float = 0.9, seed: int = 0) -> np.ndarray:
    """Field-size sample plots: square cells (~36 ha at 600 m) that are at least
    90% soybean in the reference season, spread across the window.

    Contiguous soybean in the RS belt runs for kilometres, so connected
    patches merge many farms; equal-size cells give comparable field-scale
    units instead. Cells are picked at random among qualifying ones,
    no two adjacent."""
    m = ndimage.binary_opening(mask, iterations=1)
    c = cell_m // RES_M
    ny, nx = m.shape[0] // c, m.shape[1] // c
    share = m[:ny * c, :nx * c].reshape(ny, c, nx, c).mean(axis=(1, 3))
    cand = list(zip(*np.where(share >= min_share)))
    rng = np.random.default_rng(seed)
    rng.shuffle(cand)
    chosen = []
    for (i, j) in cand:
        if all(abs(i - a) > 1 or abs(j - b) > 1 for a, b in chosen):
            chosen.append((i, j))
        if len(chosen) == n:
            break
    out = np.zeros(mask.shape, int)
    for k, (i, j) in enumerate(chosen, 1):
        cell = np.zeros(mask.shape, bool)
        cell[i * c:(i + 1) * c, j * c:(j + 1) * c] = True
        out[cell & m] = k
    return out


def field_series(times, ndvi, fields: np.ndarray, min_clear: float = 0.5) -> pd.DataFrame:
    rows = []
    for f in range(1, fields.max() + 1):
        sel = fields == f
        for i, t in enumerate(times):
            v = ndvi[i][sel]
            ok = np.isfinite(v)
            if ok.mean() >= min_clear:
                rows.append({"field": f, "date": t.normalize(), "ndvi": float(np.median(v[ok]))})
    return pd.DataFrame(rows)


def field_area_ha(fields: np.ndarray) -> dict:
    return {f: float((fields == f).sum() * RES_M ** 2 / 10_000) for f in range(1, fields.max() + 1)}


def field_polygons(fields: np.ndarray, tr, name: str) -> list[dict]:
    """GeoJSON polygons (WGS84) of the field plots; tr = affine transform of the grid."""
    from rasterio.features import shapes
    from rasterio.warp import transform_geom
    out = []
    for geom, val in shapes(fields.astype("int32"), mask=fields > 0, transform=tr):
        g = transform_geom(CRS, "EPSG:4326", geom)
        out.append({"type": "Feature", "properties": {"municipality": name, "field": int(val)},
                    "geometry": g})
    return out


def stage_summary(series: pd.DataFrame, harvest_year: int) -> dict | None:
    return stage_windows(series["date"], series["ndvi"], harvest_year)
