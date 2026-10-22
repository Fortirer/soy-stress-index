"""Live season monitor: the Turgor index for the current season, every week.

Weekly anchors (as-of dates) run from 1 December to 15 April. The index on an
anchor is compared with the same anchor in every past season (2001-2025),
using the same data latency, so a value means "how unusual is this season so
far, at this point of the season, in this municipality".
"""
from __future__ import annotations

import numpy as np
import pandas as pd

ANCHORS = ["12-01", "12-08", "12-15", "12-22", "01-01", "01-08", "01-15", "01-22",
           "02-01", "02-08", "02-15", "02-22", "03-01", "03-08", "03-15", "03-22",
           "04-01", "04-08", "04-15"]

# stress class from the municipality's own percentile at that anchor
CLASSES = [(95, "severe"), (85, "high"), (70, "watch"), (0, "normal")]
CLASS_COLORS = {"normal": "#DCE9E0", "watch": "#F2D27A", "high": "#E8893A", "severe": "#B4271F",
                "no data": "#FFFFFF"}


def harvest_year_of(date) -> int:
    d = pd.Timestamp(date)
    return d.year + 1 if d.month >= 9 else d.year


def anchor_for(date) -> str | None:
    """Latest anchor on or before date, within the season; None before 1 Dec."""
    d = pd.Timestamp(date)
    hy = harvest_year_of(d)
    best = None
    for a in ANCHORS:
        m = int(a[:2])
        ad = pd.Timestamp(f"{hy - 1 if m >= 9 else hy}-{a}")
        if ad <= d:
            best = a
    return best


def anchor_date(anchor: str, harvest_year: int) -> pd.Timestamp:
    m = int(anchor[:2])
    return pd.Timestamp(f"{harvest_year - 1 if m >= 9 else harvest_year}-{anchor}")


def stress_class(pct: float) -> str:
    if pd.isna(pct):
        return "no data"
    for thr, name in CLASSES:
        if pct >= thr:
            return name
    return "normal"


def own_percentile(score: pd.Series, codes: pd.Series, is_current: np.ndarray) -> pd.Series:
    """Percentile of the current season's score among each municipality's past seasons."""
    out = pd.Series(np.nan, index=score.index)
    hist = pd.DataFrame({"c": codes, "s": score})[~is_current]
    groups = {c: np.sort(g["s"].values) for c, g in hist.groupby("c")}
    for i in np.flatnonzero(is_current):
        h = groups.get(codes.iloc[i])
        if h is not None and len(h) >= 10 and pd.notna(score.iloc[i]):
            out.iloc[i] = 100.0 * np.searchsorted(h, score.iloc[i], side="right") / len(h)
    return out


def loss_rate_table(ref: pd.DataFrame, n_bins: int = 10) -> pd.DataFrame:
    """Share of past municipality-seasons with yield > 10% below trend, by index decile
    (all municipalities pooled, one table per anchor). ref: anchor, score, loss."""
    rows = []
    for a, g in ref.dropna(subset=["score", "loss"]).groupby("anchor"):
        edges = np.unique(np.quantile(g["score"], np.linspace(0, 1, n_bins + 1)))
        b = np.clip(np.searchsorted(edges, g["score"], side="right") - 1, 0, len(edges) - 2)
        t = g.assign(bin=b).groupby("bin")["loss"].agg(["mean", "size"]).reset_index()
        t["lo"], t["hi"] = edges[t["bin"]], edges[t["bin"] + 1]
        t["anchor"] = a
        rows.append(t)
    return pd.concat(rows, ignore_index=True).rename(columns={"mean": "loss_rate", "size": "n"})


def lookup_loss_rate(table: pd.DataFrame, anchor: str, score: float) -> float:
    t = table[table["anchor"] == anchor].sort_values("bin")
    if t.empty or pd.isna(score):
        return np.nan
    i = int(np.clip(np.searchsorted(t["hi"].values, score, side="left"), 0, len(t) - 1))
    return float(t["loss_rate"].iloc[i])
