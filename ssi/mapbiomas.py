"""MapBiomas soybean mask on the MODIS grid (issue #7, not run yet).

MapBiomas publishes yearly 30 m land-use maps of Brazil; class 39 = soybean.
Put the yearly coverage GeoTIFFs (or COG URLs) in data/mapbiomas/ as
brasil_coverage_<year>.tif, e.g. from the public bucket
storage.googleapis.com/mapbiomas-public (collection 9 or 10).
A MODIS pixel counts as soybean if at least MIN_SHARE of its area is class 39.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np

from .config import DATA

SOY_CLASS = 39
MIN_SHARE = 0.5


def soy_mask_loader(year: int, src: str | Path | None = None):
    """Return a function geobox -> boolean mask, for modis_season_ndvi(extra_mask=...)."""
    src = src or DATA / "mapbiomas" / f"brasil_coverage_{year}.tif"
    if not str(src).startswith("http") and not Path(src).exists():
        raise FileNotFoundError(f"MapBiomas map for {year} not found at {src}")

    def mask(geobox) -> np.ndarray:
        import rasterio
        from rasterio.enums import Resampling
        from rasterio.warp import reproject
        with rasterio.open(src) as ds:
            frac = np.zeros(geobox.shape, "float32")
            soy = (ds.read(1, out_shape=None) == SOY_CLASS).astype("float32")
            reproject(soy, frac, src_transform=ds.transform, src_crs=ds.crs,
                      dst_transform=geobox.transform, dst_crs="EPSG:4326", resampling=Resampling.average)
        return frac >= MIN_SHARE

    return mask
