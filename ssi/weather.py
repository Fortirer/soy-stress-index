"""Daily weather per municipality (NASA POWER) and stress by crop stage.

For each municipality-season, the water and heat components are summed over
the vegetative and reproductive windows found from the satellite NDVI curve
(satellite.stage_windows), so stress counts when it hits sensitive stages.
"""
from __future__ import annotations

import time

import numpy as np
import pandas as pd
import requests

from .config import POWER_URL, POWER_VARS

AWC_MM = 100.0        # plant-available water in the root zone (default)
EDD_BASE_C = 30.0     # extreme-degree-day threshold for soybean


def fetch_power(lat: float, lon: float, start: str, end: str, retries: int = 4) -> pd.DataFrame:
    params = {"parameters": ",".join(POWER_VARS), "community": "AG",
              "latitude": round(lat, 4), "longitude": round(lon, 4),
              "start": start.replace("-", ""), "end": end.replace("-", ""), "format": "JSON"}
    for i in range(retries):
        try:
            r = requests.get(POWER_URL, params=params, timeout=120)
            r.raise_for_status()
            p = r.json()["properties"]["parameter"]
            df = pd.DataFrame(p)
            df.index = pd.to_datetime(df.index, format="%Y%m%d")
            return df.replace(-999.0, np.nan)
        except Exception:
            time.sleep(5 * (i + 1))
    raise RuntimeError(f"POWER request failed for {lat},{lon}")


def extraterrestrial_radiation(doy: np.ndarray, lat_deg: float) -> np.ndarray:
    """FAO-56 Ra in MJ m-2 day-1."""
    phi = np.radians(lat_deg)
    dr = 1 + 0.033 * np.cos(2 * np.pi * doy / 365)
    delta = 0.409 * np.sin(2 * np.pi * doy / 365 - 1.39)
    ws = np.arccos(np.clip(-np.tan(phi) * np.tan(delta), -1, 1))
    return 24 * 60 / np.pi * 0.082 * dr * (ws * np.sin(phi) * np.sin(delta)
                                            + np.cos(phi) * np.cos(delta) * np.sin(ws))


def daily_indicators(w: pd.DataFrame, lat: float) -> pd.DataFrame:
    """ET0 (Hargreaves-Samani), VPD, extreme degree days and a bucket water balance."""
    tmax, tmin = w["T2M_MAX"], w["T2M_MIN"]
    tmean = (tmax + tmin) / 2
    ra = extraterrestrial_radiation(w.index.dayofyear.values, lat)
    et0 = 0.0023 * 0.408 * ra * (tmean + 17.8) * np.sqrt((tmax - tmin).clip(lower=0))
    es = 0.6108 * np.exp(17.27 * tmax / (tmax + 237.3))
    vpd = es * (1 - w["RH2M"].clip(0, 100) / 100)
    edd = (tmax - EDD_BASE_C).clip(lower=0)
    # simple root-zone bucket; crop water use = ET0 scaled by available water
    store, deficit = AWC_MM, []
    for p, e in zip(w["PRECTOTCORR"].fillna(0), et0.fillna(0)):
        aet = e * min(1.0, store / (0.5 * AWC_MM))
        store = min(AWC_MM, max(0.0, store + p - aet))
        deficit.append(e - aet)              # unmet demand, mm/day
    return pd.DataFrame({"prcp": w["PRECTOTCORR"], "et0": et0, "vpd": vpd, "edd": edd,
                         "deficit": deficit}, index=w.index)


def window_sums(ind: pd.DataFrame, start, end) -> dict:
    d = ind.loc[start:end]
    return {"water_deficit_mm": float(d["deficit"].sum()), "edd": float(d["edd"].sum()),
            "prcp_mm": float(d["prcp"].sum()), "vpd_max": float(d["vpd"].max()),
            "et0_mm": float(d["et0"].sum())}


def stage_weather(ind: pd.DataFrame, stages: dict) -> dict:
    """Weather stress in the satellite-derived vegetative and reproductive windows."""
    out = {}
    for stage, (a, b) in {"veg": ("veg_start", "veg_end"), "rep": ("rep_start", "rep_end")}.items():
        for k, v in window_sums(ind, stages[a], stages[b]).items():
            out[f"{stage}_{k}"] = v
    return out
