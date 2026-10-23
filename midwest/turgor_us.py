"""Turgor index for the US Midwest (Illinois first): the same method as the
Brazilian index, moved to the Northern Hemisphere calendar.

What is the same as in Brazil (ssi/):
  - water balance, extreme degree days above 30 °C, heat x dry interaction,
    NDVI per stage, local z-scores, stage weights 0.25 vegetative / 0.75
    reproductive, component weights (ssi/config.py) - all unchanged priors
  - the product index uses each county's typical stage windows (median of its
    other seasons) and real-time data latency (weather +3 days, MODIS +23 days)
  - evaluation: AUC for a loss > 10% below trend, basis risk, state-year r,
    year-block bootstrap

What changes:
  - season: 1 April to 31 October of the harvest year (planting late April-May,
    flowering July, seed fill August, harvest late September-October)
  - crop stages from the NDVI curve: canopy minimum searched 15 Apr-15 Jun,
    peak 1 Jul-31 Aug; reproductive window = peak - 16 d .. peak + 40 d
  - cropland mask: USDA Cropland Data Layer, pixels where corn + soybean cover
    at least half of the area (Illinois rotates corn and soybean field by field,
    so at 1 km the canopy signal is a corn-soybean mix; see README)
  - rainfall baseline: July-August rain, the window most US weather-index
    products use; plus the Palmer Drought Severity Index for August
"""
from __future__ import annotations

import sys
from datetime import timedelta
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.signal import savgol_filter

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))

DATA, RESULTS, FIGURES = HERE / "data", HERE / "results", HERE / "figures"
for p in (DATA, RESULTS, FIGURES):
    p.mkdir(exist_ok=True)

WINDOWS = ["veg_start", "veg_end", "rep_start", "rep_end"]
WEATHER_LAG_D, MODIS_LAG_D = 3, 16 + 7
DATES = ["06-15", "07-01", "07-15", "08-01", "08-15", "09-01", "09-15", "10-01"]
END_OF_SEASON = "10-01"
TRAIN, TEST = range(2001, 2024), [2024, 2025]
BU_TO_KG_SOY = 27.2155        # 1 bushel of soybean = 60 lb = 27.2 kg
ACRE_HA = 0.404686


def season_origin(year) -> pd.Timestamp:
    return pd.Timestamp(f"{int(year)}-04-01")


def season_dates(year: int) -> tuple[str, str]:
    return f"{year}-04-01", f"{year}-10-31"


# ---------------------------------------------------------------- stages
def stage_windows(dates, ndvi, year: int) -> dict | None:
    s = pd.Series(np.asarray(ndvi), index=pd.to_datetime(np.asarray(dates))).sort_index().dropna()
    s = s[f"{year}-04-01":f"{year}-10-31"]
    if len(s) < 6:
        return None
    daily = s.resample("D").mean().interpolate(limit_direction="both")
    win = min(31, len(daily) // 2 * 2 - 1)
    sm = pd.Series(savgol_filter(daily.values, win, 2), index=daily.index)
    early = sm[f"{year}-04-15":f"{year}-06-15"]
    mid = sm[f"{year}-07-01":f"{year}-08-31"]
    if len(early) == 0 or len(mid) == 0:
        return None
    base, top = float(early.min()), float(mid.max())
    if top - base < 0.10:
        return None
    base_date, peak = early.idxmin(), mid.idxmax()
    rising = sm[base_date:peak]
    above = rising[rising >= base + 0.5 * (top - base)]
    green_up = above.index[0] if len(above) else peak - timedelta(days=45)
    rep_start, rep_end = peak - timedelta(days=16), peak + timedelta(days=40)
    return {"green_up": green_up, "peak": peak, "veg_start": green_up, "veg_end": rep_start,
            "rep_start": rep_start, "rep_end": rep_end, "ndvi_peak": top,
            "ndvi_amplitude": top - base,
            "ndvi_vegetative": float(sm[green_up:rep_start].mean()),
            "ndvi_reproductive": float(sm[rep_start:rep_end].mean())}


def stage_table(series: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (code, yr), g in series.groupby(["fips5", "year"]):
        w = stage_windows(g["date"], g["ndvi"], int(yr))
        if w:
            rows.append({"fips5": code, "year": yr, **w})
    return pd.DataFrame(rows)


def typical_windows(stages: pd.DataFrame) -> pd.DataFrame:
    """Leave-one-season-out median window offsets (days after 1 April)."""
    s = stages[["fips5", "year"] + WINDOWS].copy()
    for c in WINDOWS:
        s[c] = (pd.to_datetime(s[c]) - pd.to_datetime(s["year"].astype(str) + "-04-01")).dt.days
    rows = []
    for code, g in s.groupby("fips5"):
        vals = g[WINDOWS].values
        for i, yr in enumerate(g["year"].values):
            other = np.delete(vals, i, axis=0) if len(g) > 1 else vals
            rows.append([code, yr, *np.median(other, axis=0)])
    return pd.DataFrame(rows, columns=["fips5", "year"] + WINDOWS)


# ---------------------------------------------------------------- features
def asof_features(ind: pd.DataFrame, ndvi: pd.DataFrame, code: int, years, dates_mmdd,
                  typ: pd.DataFrame, fallback: pd.Series) -> list[dict]:
    """Index inputs as they were known on each date (typical windows, latency)."""
    cum = ind[["deficit", "edd", "prcp", "vpd"]].fillna(0).cumsum()
    first, last = cum.index[0], cum.index[-1]

    def csum(col, a, b):
        if b < a:
            return 0.0
        a, b = max(a, first), min(b, last)
        before = cum[col].asof(a - pd.Timedelta(days=1)) if a > first else 0.0
        return float(cum[col].asof(b) - before)

    nd_by_year = {y: g for y, g in ndvi.groupby("year")} if len(ndvi) else {}
    out = []
    for yr in years:
        o = season_origin(yr)
        try:
            r = typ.loc[(code, yr)]
        except KeyError:
            r = fallback
        win = {k: o + pd.Timedelta(days=int(round(r[k]))) for k in WINDOWS}
        nd = nd_by_year.get(yr)
        for mmdd in dates_mmdd:
            d = pd.Timestamp(f"{yr}-{mmdd}")
            wx_end = d - pd.Timedelta(days=WEATHER_LAG_D)
            row = {"fips5": code, "year": yr, "asof": mmdd}
            for stage, (a, b) in {"veg": ("veg_start", "veg_end"), "win": ("rep_start", "rep_end")}.items():
                end = min(win[b], wx_end)
                row[f"{stage}_water_deficit_mm"] = csum("deficit", win[a], end)
                row[f"{stage}_edd"] = csum("edd", win[a], end)
                col = "ndvi_vegetative" if stage == "veg" else "ndvi_reproductive"
                if nd is not None:
                    centre = nd["date"] + pd.Timedelta(days=8)
                    ok = ((centre >= win[a]) & (centre <= win[b])
                          & (nd["date"] + pd.Timedelta(days=MODIS_LAG_D) <= d))
                    row[col] = float(nd.loc[ok, "ndvi"].mean()) if ok.any() else np.nan
                else:
                    row[col] = np.nan
            # rainfall-index baseline as of the same date: July-August rain so far
            ra, rb = pd.Timestamp(f"{yr}-07-01"), min(pd.Timestamp(f"{yr}-08-31"), wx_end)
            row["pcp_critical"] = csum("prcp", ra, rb)
            out.append(row)
    return out


def full_season_features(ind: pd.DataFrame, stages: pd.DataFrame, code: int, years) -> list[dict]:
    """Weather summed over each season's own satellite windows (v1, not real time)."""
    from ssi.weather import stage_weather
    st = stages.set_index("year") if len(stages) else pd.DataFrame()
    out = []
    for yr in years:
        if yr in getattr(st, "index", []):
            s = st.loc[yr]
            win = {k: s[k] for k in WINDOWS}
            src, nveg, nrep = "ndvi", s["ndvi_vegetative"], s["ndvi_reproductive"]
        else:
            win = {"veg_start": f"{yr}-05-15", "veg_end": f"{yr}-07-10",
                   "rep_start": f"{yr}-07-10", "rep_end": f"{yr}-09-05"}
            src, nveg, nrep = "calendar", np.nan, np.nan
        out.append({"fips5": code, "year": yr, "window_source": src, "ndvi_vegetative": nveg,
                    "ndvi_reproductive": nrep, **{f"sw_{k}": v for k, v in stage_weather(ind, win).items()}})
    return out


def centroid(f) -> tuple[float, float]:
    ring = np.array(f["geometry"]["coordinates"][0])
    return float(ring[:, 1].mean()), float(ring[:, 0].mean())
