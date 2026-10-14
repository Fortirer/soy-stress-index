"""Load municipal soybean yields and season weather from Modelling-soybean.

Important alignment fix
-----------------------
In the source repo, Brazilian weather aggregates are keyed by *crop year*
(the year the season starts: Sep of year Y to Apr of Y+1), while IBGE PAM
yields are keyed by *harvest year* (Y+1). Joining them on the same year
pairs each harvest with the previous season's weather. In Rio Grande do Sul
that drops the correlation between Jan-Feb water deficit and yield from
about -0.48 to about -0.08. Here weather from crop year Y is matched to the
harvest of Y+1.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from .config import DATA, LOSS_THRESHOLD, STATES

YIELD_COLS = ["state", "county", "municipio_codigo", "fips5", "year",
              "area_harvested_ha", "yield_kg_ha", "yield_trend", "yield_anom"]

WEATHER_COLS = ["pcp_grow", "pcp_critical", "tmp_grow", "tmp_critical",
                "tmax_critical", "tmax_grow", "tmin_grow", "tmp_grow_sd",
                "hot_days_critical", "dry_days_critical", "heat_x_dry"]

PHENO_COLS = ["season_gdd", "season_edd", "season_hot_days", "season_prcp_mm",
              "season_et0_mm", "season_water_deficit_mm", "win_gdd", "win_edd",
              "win_hot_days", "win_prcp_mm", "win_et0_mm", "win_vpd_mean",
              "win_vpd_max", "win_tmax_mean", "win_water_deficit_mm"]


def build_panel(src: str | Path) -> pd.DataFrame:
    """Municipality x harvest-year panel with correctly aligned weather."""
    src = Path(src)
    frames = []
    for st in STATES:
        f = src / f"data/final/BR/{st}/soja_mt_climate_1981_2024.csv"
        if not f.exists():
            continue
        raw = pd.read_csv(f)
        yields = raw[[c for c in YIELD_COLS if c in raw.columns]].copy()
        # weather in the final file carries the crop (season-start) year
        wx = raw[["fips5", "year"] + [c for c in WEATHER_COLS if c in raw.columns]].copy()
        ph_file = src / f"data/processed/BR/{st}/phenology_features.csv"
        if ph_file.exists():
            ph = pd.read_csv(ph_file)
            wx = wx.merge(ph[["fips5", "year"] + [c for c in PHENO_COLS if c in ph.columns]],
                          on=["fips5", "year"], how="outer")
        wx["year"] = wx["year"] + 1          # crop year Y -> harvest year Y+1
        df = yields.merge(wx, on=["fips5", "year"], how="inner")
        df.insert(0, "st", st)
        frames.append(df)
    panel = pd.concat(frames, ignore_index=True)
    panel = panel[panel["yield_trend"] > 0].copy()
    panel["rel_anom"] = panel["yield_anom"] / panel["yield_trend"]
    panel["loss"] = (panel["rel_anom"] < LOSS_THRESHOLD).astype(int)
    # vegetative-phase aggregates = whole season minus the Jan-Feb window
    panel["veg_water_deficit_mm"] = panel["season_water_deficit_mm"] - panel["win_water_deficit_mm"]
    panel["veg_edd"] = panel["season_edd"] - panel["win_edd"]
    return panel


def build_boundaries(src: str | Path) -> dict:
    """GeoJSON of municipality outlines (used for maps and satellite zonal stats)."""
    src = Path(src)
    feats = []
    for st in STATES:
        f = src / f"data/raw/BR/{st}/mt_municipio_boundaries.txt"
        if not f.exists():
            continue
        for line in f.read_text().strip().splitlines():
            code, coords = line.split("|", 1)
            ring = [[float(x) for x in p.split(",")] for p in coords.split()]
            if ring[0] != ring[-1]:
                ring.append(ring[0])
            feats.append({"type": "Feature", "id": int(code), "properties": {"st": st},
                          "geometry": {"type": "Polygon", "coordinates": [ring]}})
    return {"type": "FeatureCollection", "features": feats}


def load_panel() -> pd.DataFrame:
    return pd.read_csv(DATA / "panel.csv.gz")


def load_boundaries() -> dict:
    return json.loads((DATA / "municipalities.geojson").read_text())
