"""MapBiomas soybean mask on the MODIS grid (issue #7).

MapBiomas Collection 9 publishes yearly 30 m land-use maps of Brazil
(1985-2023) as cloud-optimised GeoTIFFs with overviews; class 39 = soybean.
(Collection 10 adds 2024 but has no overviews, so it would mean reading the
full 30 m window; 2024 seasons use the 2023 map.) Only the
window over the area of interest is read, from the 4x overview (~120 m),
and the soybean share of every MODIS pixel is computed from it.
A MODIS pixel counts as soybean if at least MIN_SHARE of it is class 39.
"""
from __future__ import annotations

import numpy as np

from .config import DATA

SOY_CLASS = 39
MIN_SHARE = 0.5
URL = ("https://storage.googleapis.com/mapbiomas-public/initiatives/brasil/collection_9/"
       "lclu/coverage/brasil_coverage_{year}.tif")
FIRST, LAST = 1985, 2023
OVERVIEW_LEVEL = 1          # overviews are 2, 4, 8 ...; level 1 = 4x = ~120 m


def soy_share(geobox, year: int) -> np.ndarray:
    """Share of soybean (0-1) in each cell of geobox (EPSG:4326), cached on disk."""
    year = min(max(year, FIRST), LAST)
    cache = DATA / "rs_experiments" / "soymask"
    cache.mkdir(parents=True, exist_ok=True)
    w, s, e, n = geobox.extent.boundingbox
    fp = cache / f"{year}_{w:.3f}_{s:.3f}_{e:.3f}_{n:.3f}_{geobox.shape[0]}x{geobox.shape[1]}.npy"
    if fp.exists():
        return np.load(fp)
    import rasterio
    from rasterio.enums import Resampling
    from rasterio.warp import reproject
    from rasterio.windows import from_bounds
    with rasterio.open("/vsicurl/" + URL.format(year=year), overview_level=OVERVIEW_LEVEL) as ds:
        win = from_bounds(w, s, e, n, ds.transform).round_offsets().round_lengths()
        arr = ds.read(1, window=win)
        tr = ds.window_transform(win)
        crs = ds.crs
    soy = (arr == SOY_CLASS).astype("float32")
    share = np.zeros(geobox.shape, "float32")
    reproject(soy, share, src_transform=tr, src_crs=crs, dst_transform=geobox.transform,
              dst_crs="EPSG:4326", resampling=Resampling.average)
    np.save(fp, share)
    return share


def soy_mask_loader(year: int):
    """For modis_season_ndvi(extra_mask=...): geobox -> boolean soybean mask."""
    return lambda geobox: soy_share(geobox, year) >= MIN_SHARE
