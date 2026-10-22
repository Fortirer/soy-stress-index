"""From index to money: expected yield loss and probability of a loss.

Three monotone (isotonic) maps from the Turgor index, one set per state:

  expected_anomaly   mean yield vs trend (%)            decreasing in the index
  p_loss             P(yield > 10% below trend)          increasing
  expected_shortfall mean max(0, trend - yield) (% of trend), the part an
                     insurer or lender loses; increasing

Isotonic regression assumes only that more stress never means a better
expected outcome, with no other shape, so it cannot be overfitted into a
curve the data do not support. Models are stored as plain threshold tables
(x, y), applied with linear interpolation, so they need no pickle.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.isotonic import IsotonicRegression

from .config import LOSS_THRESHOLD

TARGETS = {"expected_anomaly": False, "p_loss": True, "expected_shortfall": True}  # increasing?


def _targets(df: pd.DataFrame) -> dict[str, np.ndarray]:
    a = df["rel_anom"].values
    return {"expected_anomaly": a, "p_loss": (a < LOSS_THRESHOLD).astype(float),
            "expected_shortfall": np.clip(-a, 0, None)}


def fit_tables(df: pd.DataFrame, score: str = "score", by: str = "st") -> pd.DataFrame:
    """Threshold tables: group, target, x, y."""
    rows = []
    for g, d in df.dropna(subset=[score, "rel_anom"]).groupby(by):
        x = d[score].values
        for t, y in _targets(d).items():
            m = IsotonicRegression(increasing=TARGETS[t], out_of_bounds="clip").fit(x, y)
            rows.append(pd.DataFrame({by: g, "target": t, "x": m.X_thresholds_, "y": m.y_thresholds_}))
    return pd.concat(rows, ignore_index=True)


def predict(tables: pd.DataFrame, df: pd.DataFrame, score: str = "score", by: str = "st") -> pd.DataFrame:
    out = pd.DataFrame(index=df.index, columns=list(TARGETS), dtype=float)
    for g, idx in df.groupby(by).groups.items():
        for t in TARGETS:
            tb = tables[(tables[by] == g) & (tables["target"] == t)]
            if tb.empty:
                continue
            v = np.interp(df.loc[idx, score].astype(float), tb["x"], tb["y"])
            if t == "p_loss":   # never report certainty from a handful of extreme seasons
                v = np.clip(v, 0.02, 0.98)
            out.loc[idx, t] = v
    return out


def loyo_predict(df: pd.DataFrame, score: str = "score", by: str = "st") -> pd.DataFrame:
    """Leave-one-season-out predictions: each season predicted by models fitted on the others."""
    parts = []
    for yr in sorted(df["year"].unique()):
        te = df["year"] == yr
        parts.append(predict(fit_tables(df[~te], score, by), df[te], score, by))
    return pd.concat(parts).loc[df.index]


def calibration(pred: pd.Series, obs: pd.Series, n: int = 10) -> pd.DataFrame:
    q = pd.qcut(pred.rank(method="first"), n, labels=False)
    return pd.DataFrame({"pred": pred, "obs": obs, "decile": q}).groupby("decile").agg(
        predicted=("pred", "mean"), observed=("obs", "mean"), n=("obs", "size")).reset_index()


def brier(p: np.ndarray, y: np.ndarray) -> float:
    return float(np.mean((p - y) ** 2))


def shortfall_rs_per_ha(expected_shortfall: pd.Series, trend_kg_ha: pd.Series, price_per_bag: float) -> pd.Series:
    """Expected shortfall (fraction of trend yield) -> R$/ha, bags of 60 kg."""
    return expected_shortfall * trend_kg_ha / 60.0 * price_per_bag
