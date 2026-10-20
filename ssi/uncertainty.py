"""Confidence intervals by resampling whole harvest years.

Municipalities in the same season share the same weather, so they are not
independent. Resampling years (not rows) keeps that dependence and gives
honest, wider intervals. 2001-2023 has 23 harvests, so intervals stay wide.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score


def _basis_risk(s: np.ndarray, loss: np.ndarray) -> float:
    rate = loss.mean()
    thr = np.quantile(s, 1 - rate)
    return 1 - ((s >= thr) & (loss == 1)).sum() / max(loss.sum(), 1)


def _state_year(df: pd.DataFrame, s: np.ndarray) -> pd.DataFrame:
    w = df["area_harvested_ha"].fillna(1).values
    t = pd.DataFrame({"st": df["st"].values, "year": df["year"].values,
                      "ws": s * w, "wy": df["rel_anom"].values * w, "w": w})
    g = t.groupby(["st", "year"]).sum()
    return pd.DataFrame({"s": g.ws / g.w, "y": g.wy / g.w}).reset_index()


def point_metrics(df: pd.DataFrame, s: np.ndarray) -> dict:
    loss = df["loss"].values
    sy = _state_year(df, s)
    return {"auc_loss": roc_auc_score(loss, s), "basis_risk": _basis_risk(s, loss),
            "state_year_r": -np.corrcoef(sy.s, sy.y)[0, 1]}


def year_bootstrap(df: pd.DataFrame, scores: dict[str, np.ndarray], n: int = 1000,
                   seed: int = 0, reference: str | None = None) -> pd.DataFrame:
    """Percentile 95% intervals per index; with `reference`, also for the
    difference index minus reference (paired: same resampled years)."""
    rng = np.random.default_rng(seed)
    years = np.sort(df["year"].unique())
    rows_by_year = {y: np.flatnonzero(df["year"].values == y) for y in years}
    loss = df["loss"].values
    sy = {k: _state_year(df, v) for k, v in scores.items()}
    sy_rows = {k: {y: np.flatnonzero(t["year"].values == y) for y in years} for k, t in sy.items()}
    draws = {k: [] for k in scores}
    for _ in range(n):
        pick = rng.choice(years, size=len(years), replace=True)
        idx = np.concatenate([rows_by_year[y] for y in pick])
        if loss[idx].min() == loss[idx].max():
            continue
        for k, s in scores.items():
            t = sy[k]
            j = np.concatenate([sy_rows[k][y] for y in pick])
            draws[k].append((roc_auc_score(loss[idx], s[idx]), _basis_risk(s[idx], loss[idx]),
                             -np.corrcoef(t.s.values[j], t.y.values[j])[0, 1]))
    names = ["auc_loss", "basis_risk", "state_year_r"]
    out = []
    for k, s in scores.items():
        d = np.array(draws[k])
        pt = point_metrics(df, s)
        for i, m in enumerate(names):
            row = {"index": k, "metric": m, "estimate": pt[m],
                   "ci_low": np.percentile(d[:, i], 2.5), "ci_high": np.percentile(d[:, i], 97.5)}
            if reference and k != reference:
                diff = d[:, i] - np.array(draws[reference])[:, i]
                row.update({"diff_vs_ref": pt[m] - point_metrics(df, scores[reference])[m],
                            "diff_ci_low": np.percentile(diff, 2.5),
                            "diff_ci_high": np.percentile(diff, 97.5),
                            # share of resamples where this index is better than the reference
                            "p_better": float(np.mean(diff < 0) if m == "basis_risk" else np.mean(diff > 0))})
            out.append(row)
    return pd.DataFrame(out)
