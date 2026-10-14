"""Stage-weighted Stress Index (SSI) for soybean.

SSI = sum over stages s of  w_s * [ a_water * Z(water deficit)_s
                                   + a_heat * Z(extreme heat)_s
                                   + a_hxd * max(Z water, 0) * max(Z heat, 0)
                                   - a_ndvi * Z(NDVI)_s ]

Z(.) is a standardized anomaly against each municipality's own climatology,
so the index measures stress relative to what is normal *there*. Higher SSI
means more stress. The heat x dry term encodes the physiology that heat is
mostly harmless when water is available, and damaging when it is not.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .config import COMPONENT_WEIGHTS, STAGE_WEIGHTS

# Weather inputs per stage, with sign so that + means "more stress".
STAGE_INPUTS = {
    "vegetative": {"water": "veg_water_deficit_mm", "heat": "veg_edd"},
    "reproductive": {"water": "win_water_deficit_mm", "heat": "win_edd"},
}


def local_z(df: pd.DataFrame, col: str, by: str = "fips5") -> pd.Series:
    """Standardized anomaly against each municipality's own record."""
    g = df.groupby(by)[col]
    sd = g.transform("std").replace(0, np.nan)
    return (df[col] - g.transform("mean")) / sd


def components(df: pd.DataFrame) -> pd.DataFrame:
    """Per-stage stress components (z-scores)."""
    out = pd.DataFrame(index=df.index)
    for stage, cols in STAGE_INPUTS.items():
        zw = local_z(df, cols["water"])
        zh = local_z(df, cols["heat"])
        out[f"{stage}_water"] = zw
        out[f"{stage}_heat"] = zh
        out[f"{stage}_heat_x_dry"] = zw.clip(lower=0) * zh.clip(lower=0)
        ndvi_col = f"ndvi_{stage}"
        if ndvi_col in df.columns:            # filled in once satellite data exists
            out[f"{stage}_ndvi"] = -local_z(df, ndvi_col)
    return out.fillna(0.0)


def stage_scores(comp: pd.DataFrame, a: dict | None = None) -> pd.DataFrame:
    a = a or COMPONENT_WEIGHTS
    scores = pd.DataFrame(index=comp.index)
    for stage in STAGE_INPUTS:
        s = (a["water"] * comp[f"{stage}_water"]
             + a["heat"] * comp[f"{stage}_heat"]
             + a["heat_x_dry"] * comp[f"{stage}_heat_x_dry"])
        if f"{stage}_ndvi" in comp:
            s = s + a["ndvi"] * comp[f"{stage}_ndvi"]
        scores[stage] = s
    return scores


def ssi(df: pd.DataFrame, stage_weights: dict | None = None, a: dict | None = None) -> pd.Series:
    """The a-priori Stage-weighted Stress Index."""
    w = stage_weights or STAGE_WEIGHTS
    sc = stage_scores(components(df), a)
    return sum(w[s] * sc[s] for s in w)


def unweighted_index(df: pd.DataFrame) -> pd.Series:
    """Same inputs, but every stage counts equally (tests whether stage weighting helps)."""
    return ssi(df, stage_weights={"vegetative": 0.5, "reproductive": 0.5})


def rainfall_index(df: pd.DataFrame) -> pd.Series:
    """What a rainfall-index insurance product uses: low Jan-Feb rain = stress."""
    return -local_z(df, "pcp_critical").fillna(0.0)
