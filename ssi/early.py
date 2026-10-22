"""Early warning: the index as it would have looked on a given date of the season.

In real time the crop stages of the current season are not known yet (the
NDVI peak has not happened). So the stage windows here are each
municipality's *typical* windows, the median of its other seasons (leave the
season itself out). On each as-of date, weather and NDVI are summed only over
the part of each window that has already passed, with data latency:

  - weather (NASA POWER): available 3 days after the day
  - MODIS 16-day composite: available 16 days after its start date + 7 days

Then the same z-scores and stage weights as the full index are applied.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .index import ssi

WINDOWS = ["veg_start", "veg_end", "rep_start", "rep_end"]
WEATHER_LAG_D = 3
MODIS_LAG_D = 16 + 7


def season_origin(harvest_year) -> pd.Timestamp:
    return pd.Timestamp(f"{int(harvest_year) - 1}-09-01")


def typical_windows(stages: pd.DataFrame) -> pd.DataFrame:
    """Leave-one-season-out median window offsets (days after Sep 1), per municipality-season."""
    s = stages[["fips5", "year"] + WINDOWS].copy()
    for c in WINDOWS:
        s[c] = (pd.to_datetime(s[c]) - pd.to_datetime((s["year"] - 1).astype(str) + "-09-01")).dt.days
    rows = []
    for code, g in s.groupby("fips5"):
        vals = g[WINDOWS].values
        for i, yr in enumerate(g["year"].values):
            other = np.delete(vals, i, axis=0) if len(g) > 1 else vals
            rows.append([code, yr, *np.median(other, axis=0)])
    return pd.DataFrame(rows, columns=["fips5", "year"] + WINDOWS)


def window_offsets(code: int, year: int, typ: pd.DataFrame, fallback: pd.Series) -> dict:
    try:
        r = typ.loc[(code, year)]
    except KeyError:
        r = fallback
    return {c: int(round(r[c])) for c in WINDOWS}


def asof_features(ind: pd.DataFrame, ndvi: pd.DataFrame, code: int, years, dates_mmdd,
                  typ: pd.DataFrame, fallback: pd.Series) -> list[dict]:
    """ind: daily indicators (deficit, edd, prcp) for one municipality.
    ndvi: MODIS composites (date, ndvi, harvest_year) for one municipality."""
    cum = ind[["deficit", "edd", "prcp", "vpd"]].fillna(0).cumsum()
    first = cum.index[0]

    def csum(col, a, b):
        if b < a:
            return 0.0
        a, b = max(a, first), min(b, cum.index[-1])
        before = cum[col].asof(a - pd.Timedelta(days=1)) if a > first else 0.0
        return float(cum[col].asof(b) - before)

    out = []
    nd_by_year = {y: g for y, g in ndvi.groupby("harvest_year")}
    for yr in years:
        o = season_origin(yr)
        w = window_offsets(code, yr, typ, fallback)
        win = {k: o + pd.Timedelta(days=v) for k, v in w.items()}
        nd = nd_by_year.get(yr)
        for mmdd in dates_mmdd:
            m = int(mmdd[:2])
            d = pd.Timestamp(f"{yr - 1 if m >= 9 else yr}-{mmdd}")
            wx_end = d - pd.Timedelta(days=WEATHER_LAG_D)
            row = {"fips5": code, "year": yr, "asof": mmdd}
            for stage, (a, b) in {"veg": ("veg_start", "veg_end"), "win": ("rep_start", "rep_end")}.items():
                end = min(win[b], wx_end)
                row[f"{stage}_water_deficit_mm"] = csum("deficit", win[a], end)
                row[f"{stage}_edd"] = csum("edd", win[a], end)
                row[f"{stage}_vpd_sum"] = csum("vpd", win[a], end)
                ndvi_col = "ndvi_vegetative" if stage == "veg" else "ndvi_reproductive"
                if nd is not None:
                    centre = nd["date"] + pd.Timedelta(days=8)
                    ok = ((centre >= win[a]) & (centre <= win[b])
                          & (nd["date"] + pd.Timedelta(days=MODIS_LAG_D) <= d))
                    row[ndvi_col] = float(nd.loc[ok, "ndvi"].mean()) if ok.any() else np.nan
                else:
                    row[ndvi_col] = np.nan
            # rainfall-index baseline as of the same date: Jan-Feb rain so far
            ra, rb = pd.Timestamp(f"{yr}-01-01"), min(pd.Timestamp(f"{yr}-02-28"), wx_end)
            row["pcp_critical"] = csum("prcp", ra, rb)
            out.append(row)
    return out


def asof_scores(feat: pd.DataFrame) -> pd.Series:
    """Index for rows that share one as-of date (z-scores within that date)."""
    f = feat.copy()
    # before a window starts every season is 0 -> z undefined -> component 0
    return ssi(f)


# ---------------------------------------------------------------- the product index
PRODUCT_INDEX = "Turgor index"
END_OF_SEASON = "04-15"   # every typical window has closed by mid-April in RS and PR


def load_asof_features(asof: str = END_OF_SEASON) -> pd.DataFrame:
    """As-of features (scripts 11 and 12) for one date, all available harvests."""
    from .config import DATA
    files = [DATA / "asof_features.csv.gz", DATA / "asof_features_2024_2025.csv.gz"]
    f = pd.concat([pd.read_csv(p) for p in files if p.exists()], ignore_index=True)
    f = f[f["asof"] == asof].drop(columns="asof")
    return f.drop_duplicates(["fips5", "year"], keep="last").reset_index(drop=True)


def turgor_index(feat: pd.DataFrame, ref=None) -> pd.Series:
    """THE Turgor index: the real-time Stage-weighted Stress Index.

    feat: one row per municipality-season with as-of features (typical stage
    windows, data latency; see asof_features). With asof = END_OF_SEASON it is
    the end-of-season value; with an earlier date it is the in-season warning.
    ref: rows that define each municipality's normal (training seasons only
    when scoring new seasons). Higher = more stress."""
    return ssi(feat, ref=ref)


def add_turgor_index(df: pd.DataFrame, asof: str = END_OF_SEASON, ref=None) -> np.ndarray:
    """Turgor index aligned to the rows of df (needs fips5, year)."""
    f = df[["fips5", "year"]].merge(load_asof_features(asof), on=["fips5", "year"], how="left")
    return turgor_index(f, ref=ref).values
