"""Honest evaluation: leave-one-year-out, basis risk, named drought years."""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score

from .index import components


def trigger_basis_risk(score: np.ndarray, loss: np.ndarray) -> dict:
    """Use the index as a parametric trigger that pays in the same share of
    municipality-seasons as losses really occur. Basis risk = share of real
    losses the trigger misses (equal to the share of payouts that are false)."""
    rate = loss.mean()
    thr = np.quantile(score, 1 - rate)
    pay = score >= thr
    paid = (pay & (loss == 1)).sum() / max(loss.sum(), 1)
    # With payout rate = loss rate, missed losses and false payouts are equal
    # in number, so one figure describes both.
    return {"basis_risk": 1 - paid}


def metrics(score, df: pd.DataFrame) -> dict:
    s = np.asarray(score, dtype=float)
    ok = ~np.isnan(s)
    s, d = s[ok], df.loc[ok]
    loss = d["loss"].values
    # municipality level
    out = {"n": int(ok.sum()),
           "auc_loss": roc_auc_score(loss, s),
           "spearman_yield": -spearmanr(s, d["rel_anom"]).statistic}
    out.update(trigger_basis_risk(s, loss))
    # portfolio level: area-weighted state-year
    t = d.assign(s=s, w=d["area_harvested_ha"].fillna(1))
    sy = t.groupby(["st", "year"]).apply(
        lambda g: pd.Series({"s": np.average(g.s, weights=g.w),
                             "y": np.average(g.rel_anom, weights=g.w)}), include_groups=False)
    out["state_year_r"] = -np.corrcoef(sy.s, sy.y)[0, 1]
    return out


def fitted_weights_loyo(df: pd.DataFrame) -> tuple[np.ndarray, pd.Series]:
    """Learn component weights with logistic regression, leave-one-year-out.
    Returns out-of-fold scores and the weights fitted on all years."""
    comp = components(df)
    X, y, years = comp.values, df["loss"].values, df["year"].values
    oof = np.full(len(df), np.nan)
    for yr in np.unique(years):
        te = years == yr
        m = LogisticRegression(max_iter=1000, C=1.0).fit(X[~te], y[~te])
        oof[te] = m.decision_function(X[te])
    full = LogisticRegression(max_iter=1000, C=1.0).fit(X, y)
    return oof, pd.Series(full.coef_[0], index=comp.columns)


def drought_year_table(df: pd.DataFrame, scores: dict[str, np.ndarray], years: dict) -> pd.DataFrame:
    """For each named drought harvest: observed loss and each index's
    percentile rank among all years for that state (100 = most stressed)."""
    rows = []
    for st, yrs in years.items():
        d = df[df["st"] == st]
        w = d["area_harvested_ha"].fillna(1)
        obs = d.assign(w=w).groupby("year").apply(
            lambda g: np.average(g.rel_anom, weights=g.w), include_groups=False)
        for name, s in scores.items():
            sy = pd.Series(s, index=df.index).loc[d.index]
            agg = d.assign(s=sy, w=w).groupby("year").apply(
                lambda g: np.average(g.s, weights=g.w), include_groups=False)
            pct = agg.rank(pct=True) * 100
            for yr in yrs:
                if yr in agg.index:
                    rows.append({"st": st, "harvest": yr, "index": name,
                                 "observed_yield_vs_trend_%": round(obs[yr] * 100, 1),
                                 "stress_percentile": round(pct[yr], 0)})
    t = pd.DataFrame(rows)
    return t.pivot_table(index=["st", "harvest", "observed_yield_vs_trend_%"],
                         columns="index", values="stress_percentile").reset_index()
