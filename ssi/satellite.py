"""Satellite component: MODIS NDVI per municipality, crop stages from the
NDVI curve itself, and Sentinel-2 NDVI for field-scale checks.

Data come from Microsoft Planetary Computer (free; anonymous SAS signing).
MODIS MOD13Q1 gives a consistent record back to 2000, needed to backtest
past droughts; Sentinel-2 (2017-) gives 10 m detail for fields.

Crop stages are read from each municipality-season's own NDVI curve:
  green-up  = NDVI first rises above 50% of the season's amplitude
  peak      = maximum smoothed NDVI (close to R2-R3 in soybean)
  vegetative window   = green-up .. peak - 16 days
  reproductive window = peak - 16 days .. peak + 40 days (flowering to seed fill)
These dates also anchor the weather windows (see weather.py), so heat and
drought are counted when they hit the crop's sensitive stages, not by calendar.
"""
from __future__ import annotations

from datetime import date, timedelta

import numpy as np
import pandas as pd
from scipy.signal import savgol_filter

from .config import (CROPLAND_CLASSES, MODIS_LC, MODIS_NDVI, SENTINEL2, STAC_URL)

NDVI_BAND = "250m_16_days_NDVI"
QA_BAND = "250m_16_days_pixel_reliability"   # 0 good, 1 marginal


# ---------------------------------------------------------------- access
def catalog():
    import planetary_computer
    import pystac_client
    return pystac_client.Client.open(STAC_URL, modifier=planetary_computer.sign_inplace)


def season_dates(harvest_year: int) -> tuple[str, str]:
    """Soybean season in southern Brazil: Sep of Y-1 to May of Y."""
    return f"{harvest_year - 1}-09-01", f"{harvest_year}-05-31"


def municipality_raster(features: list[dict], geobox) -> np.ndarray:
    """Burn municipality codes onto the analysis grid (0 = outside)."""
    from rasterio.features import rasterize
    shapes = [(f["geometry"], int(f["id"])) for f in features]
    return rasterize(shapes, out_shape=geobox.shape, transform=geobox.transform,
                     fill=0, dtype="int32")


def zonal_mean(values: np.ndarray, zones: np.ndarray) -> pd.DataFrame:
    ok = (zones > 0) & np.isfinite(values)
    z, v = zones[ok], values[ok]
    s = pd.DataFrame({"fips5": z, "v": v}).groupby("fips5")["v"].agg(["mean", "size"])
    return s.rename(columns={"mean": "ndvi", "size": "n_px"}).reset_index()


def cropland_mask(cat, bbox, year: int, geobox) -> np.ndarray:
    """MODIS land cover (IGBP) croplands for the given year, on the analysis grid."""
    import odc.stac
    items = list(cat.search(collections=[MODIS_LC], bbox=bbox,
                            datetime=f"{min(year, 2023)}").items())
    if not items:
        return np.ones(geobox.shape, bool)
    lc = odc.stac.load(items, bands=["LC_Type1"], geobox=geobox, resampling="mode")
    arr = lc["LC_Type1"].max("time").values
    return np.isin(arr, CROPLAND_CLASSES)


def modis_season_ndvi(features: list[dict], harvest_year: int,
                      resolution_deg: float = 0.01) -> pd.DataFrame:
    """Mean cropland NDVI per municipality for every 16-day composite of one season.

    resolution_deg=0.01 (~1 km) keeps downloads small by reading COG overviews;
    0.0025 (~250 m) uses full resolution.
    """
    import odc.stac
    from odc.geo.geobox import GeoBox

    lons = [x for f in features for x, _ in f["geometry"]["coordinates"][0]]
    lats = [y for f in features for _, y in f["geometry"]["coordinates"][0]]
    bbox = [min(lons), min(lats), max(lons), max(lats)]
    geobox = GeoBox.from_bbox(bbox, crs="EPSG:4326", resolution=resolution_deg)
    zones = municipality_raster(features, geobox)

    cat = catalog()
    start, end = season_dates(harvest_year)
    items = list(cat.search(collections=[MODIS_NDVI], bbox=bbox,
                            datetime=f"{start}/{end}").items())
    if not items:
        return pd.DataFrame()
    crop = cropland_mask(cat, bbox, harvest_year - 1, geobox)
    common = dict(geobox=geobox, groupby="solar_day")
    ndvi_ds = odc.stac.load(items, bands=[NDVI_BAND], resampling="average", dtype="float32", **common)
    qa_ds = odc.stac.load(items, bands=[QA_BAND], resampling="nearest", dtype="int16", **common)
    ds = ndvi_ds.assign({QA_BAND: qa_ds[QA_BAND]})
    times = pd.to_datetime(ds.time.values)
    nd = ds[NDVI_BAND].values.astype("float32")
    qa = ds[QA_BAND].values
    nd = np.where((qa >= 0) & (qa <= 1) & (nd > -2000), nd * 1e-4, np.nan)
    mask = crop & summer_crop_mask(nd, times, harvest_year)
    rows = []
    for i, t in enumerate(times):
        z = zonal_mean(np.where(mask, nd[i], np.nan), zones)
        z["date"] = t.normalize()
        rows.append(z)
    out = pd.concat(rows, ignore_index=True)
    out["harvest_year"] = harvest_year
    return out


def summer_crop_mask(nd: np.ndarray, times: pd.DatetimeIndex, harvest_year: int,
                     min_amplitude: float = 0.15) -> np.ndarray:
    """Pixels with a summer crop cycle: low NDVI in Oct-Nov (after winter crops
    are harvested), high in Jan-Mar. Removes pasture, forest and pixels that
    only carry winter wheat, which share the IGBP cropland class in the south."""
    y0 = harvest_year - 1
    low = (times >= f"{y0}-10-01") & (times <= f"{y0}-11-30")
    high = (times >= f"{harvest_year}-01-01") & (times <= f"{harvest_year}-03-31")
    if low.sum() == 0 or high.sum() == 0:
        return np.ones(nd.shape[1:], bool)
    with np.errstate(all="ignore"):
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            amp = np.nanmax(nd[high], axis=0) - np.nanmin(nd[low], axis=0)
    return np.nan_to_num(amp, nan=0) >= min_amplitude


# ---------------------------------------------------------------- stages
def stage_windows(dates: pd.Series, ndvi: pd.Series, harvest_year: int | None = None) -> dict | None:
    """Green-up, peak and stage windows from one season's NDVI series.

    Southern Brazil soybean: the canopy minimum falls in Oct-mid Dec (sowing),
    the peak in Dec-Mar. Searching only there keeps winter wheat out."""
    s = pd.Series(ndvi.values, index=pd.to_datetime(dates.values)).sort_index().dropna()
    if harvest_year is None:
        harvest_year = s.index.max().year
    y0 = harvest_year - 1
    s = s[f"{y0}-10-01":f"{harvest_year}-04-30"]
    if len(s) < 6:
        return None
    daily = s.resample("D").mean().interpolate(limit_direction="both")
    win = min(31, len(daily) // 2 * 2 - 1)
    sm = pd.Series(savgol_filter(daily.values, win, 2), index=daily.index)
    early = sm[f"{y0}-10-01":f"{y0}-12-20"]
    mid = sm[f"{y0}-12-01":f"{harvest_year}-03-31"]
    if len(early) == 0 or len(mid) == 0:
        return None
    base, top = float(early.min()), float(mid.max())
    if top - base < 0.10:            # no clear summer crop cycle
        return None
    base_date, peak = early.idxmin(), mid.idxmax()
    rising = sm[base_date:peak]
    above = rising[rising >= base + 0.5 * (top - base)]
    green_up = above.index[0] if len(above) else peak - timedelta(days=45)
    rep_start, rep_end = peak - timedelta(days=16), peak + timedelta(days=40)
    return {"green_up": green_up, "peak": peak,
            "veg_start": green_up, "veg_end": rep_start,
            "rep_start": rep_start, "rep_end": rep_end,
            "ndvi_peak": top, "ndvi_amplitude": top - base,
            "ndvi_vegetative": float(sm[green_up:rep_start].mean()),
            "ndvi_reproductive": float(sm[rep_start:rep_end].mean()),
            "ndvi_integral": float(sm[green_up:rep_end].sum() / 100)}


def stage_table(series: pd.DataFrame) -> pd.DataFrame:
    """Apply stage_windows to every municipality-season."""
    rows = []
    for (code, yr), g in series.groupby(["fips5", "harvest_year"]):
        w = stage_windows(g["date"], g["ndvi"], int(yr))
        if w:
            rows.append({"fips5": code, "year": yr, **w})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- Sentinel-2
def sentinel2_ndvi(bbox: list[float], start: str, end: str, max_cloud: int = 60) -> pd.DataFrame:
    """Field-scale NDVI time series (10 m) for a small area, clouds masked with SCL."""
    import odc.stac
    cat = catalog()
    items = list(cat.search(collections=[SENTINEL2], bbox=bbox, datetime=f"{start}/{end}",
                            query={"eo:cloud_cover": {"lt": max_cloud}}).items())
    if not items:
        return pd.DataFrame()
    ds = odc.stac.load(items, bands=["B04", "B08", "SCL"], bbox=bbox, crs="EPSG:4326",
                       resolution=0.0001, groupby="solar_day", chunks={})
    rows = []
    for t in ds.time.values:
        red = ds["B04"].sel(time=t).values.astype("float32")
        nir = ds["B08"].sel(time=t).values.astype("float32")
        scl = ds["SCL"].sel(time=t).values
        clear = np.isin(scl, [4, 5])          # vegetation, bare soil
        nd = np.where(clear, (nir - red) / (nir + red + 1e-6), np.nan)
        if np.isfinite(nd).mean() > 0.3:
            rows.append({"date": pd.Timestamp(t).normalize(), "ndvi": float(np.nanmedian(nd)),
                         "clear_share": float(np.isfinite(nd).mean())})
    return pd.DataFrame(rows)
