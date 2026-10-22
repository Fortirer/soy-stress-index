"""Field-level validation against a partner's real yields (co-op pilot).

Input from the partner:
  fields.geojson  one polygon per field, property "field_id" (CAR or internal id)
  yields.csv      field_id, harvest_year, yield_kg_ha   (optional: municipality code fips5)

For every field and season, the field's own Sentinel-2 NDVI curve gives its
crop stages; NASA POWER weather at the field centroid is summed over those
stages; the index is the same Stage-weighted Stress Index, with z-scores
against the field's own seasons. Validation asks two questions:

  1. Does the field index find the fields that lost yield?   (AUC, basis risk)
  2. Does it beat the municipal index the partner could buy today?
     (same metrics, on the same field-seasons)
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

from .config import LOSS_THRESHOLD
from .index import ssi
from .satellite import stage_windows
from .weather import stage_weather

SEASONS_MIN = 3   # fewer seasons per field and the field's own z-score is meaningless


def field_season_features(dates, ndvi_median: pd.Series, ind: pd.DataFrame, harvest_year: int) -> dict | None:
    """Stage windows from the field's NDVI curve + weather in those windows."""
    st = stage_windows(pd.Series(dates), ndvi_median, harvest_year)
    if st is None:
        return None
    wx = stage_weather(ind, {k: st[k] for k in ["veg_start", "veg_end", "rep_start", "rep_end"]})
    return {**{k: st[k] for k in ["veg_start", "veg_end", "rep_start", "rep_end"]},
            "peak": st["peak"], "ndvi_vegetative": st["ndvi_vegetative"],
            "ndvi_reproductive": st["ndvi_reproductive"],
            "veg_water_deficit_mm": wx["veg_water_deficit_mm"], "win_water_deficit_mm": wx["rep_water_deficit_mm"],
            "veg_edd": wx["veg_edd"], "win_edd": wx["rep_edd"]}


def yield_anomaly(y: pd.DataFrame) -> pd.DataFrame:
    """Each field's yield relative to its own linear trend; loss = >10% below."""
    out = []
    for f, g in y.groupby("field_id"):
        if len(g) >= 5:          # a trend line on fewer seasons absorbs the signal
            b = np.polyfit(g["harvest_year"], g["yield_kg_ha"], 1)
            trend = np.polyval(b, g["harvest_year"])
        else:
            trend = np.full(len(g), g["yield_kg_ha"].mean())
        out.append(g.assign(yield_trend=trend))
    y = pd.concat(out)
    y["rel_anom"] = y["yield_kg_ha"] / y["yield_trend"] - 1
    y["loss"] = (y["rel_anom"] < LOSS_THRESHOLD).astype(int)
    return y


def field_index(feat: pd.DataFrame) -> pd.Series:
    f = feat.drop(columns=["fips5"], errors="ignore").rename(columns={"field_id": "fips5"})  # z-scores per field
    return ssi(f)


def _basis_risk(s, loss):
    """Pay exactly as many field-seasons as had a loss (ties broken at random,
    so a flat index cannot look perfect by paying everyone)."""
    k = int(loss.sum())
    if k == 0:
        return 0.0
    rng = np.random.default_rng(0)
    order = np.lexsort((rng.random(len(s)), -np.asarray(s, float)))
    pay = np.zeros(len(s), bool)
    pay[order[:k]] = True
    return 1 - (pay & (loss == 1)).sum() / k


def validate(df: pd.DataFrame, cols: dict[str, str]) -> pd.DataFrame:
    """df: one row per field-season with loss, rel_anom and the score columns."""
    rows = []
    for name, c in cols.items():
        d = df.dropna(subset=[c])
        if d["loss"].nunique() < 2:
            continue
        s, loss = d[c].values, d["loss"].values
        # within-season ranking: which fields lost more in the same year
        within = d.groupby("harvest_year").apply(
            lambda g: -g[c].corr(g["rel_anom"], method="spearman") if len(g) > 3 else np.nan,
            include_groups=False).mean()
        rows.append({"index": name, "n_field_seasons": len(d), "loss_rate": loss.mean(),
                     "auc_loss": roc_auc_score(loss, s), "basis_risk": _basis_risk(s, loss),
                     "within_season_rank_r": within})
    return pd.DataFrame(rows)
