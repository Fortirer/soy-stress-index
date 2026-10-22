"""Figures for the validation round: early warning and the 2024-2025 holdout.

    python scripts/14_validation_figures.py
"""
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ssi.config import FIGURES, RESULTS  # noqa: E402

TURGOR, RAIN, GREY = "#1E5B3A", "#2A78D6", "#8A9A90"
LABELS = {"12-01": "1 Dec", "12-15": "15 Dec", "01-01": "1 Jan", "01-15": "15 Jan", "02-01": "1 Feb",
          "02-15": "15 Feb", "03-01": "1 Mar", "03-15": "15 Mar", "04-01": "1 Apr", "04-15": "15 Apr"}
plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})

# ---- fig 6: skill by date, 2001-2023
ew = pd.read_csv(RESULTS / "early_warning.csv")
fig, axes = plt.subplots(1, 3, figsize=(12, 3.8), sharey=True)
for ax, region in zip(axes, ["RS + PR", "RS", "PR"]):
    r = ew[(ew.region == region) & (ew["asof"] != "end")]
    x = [LABELS[a] for a in r[r["index"] == "Turgor index (as of date)"]["asof"]]
    ax.plot(x, r[r["index"] == "Turgor index (as of date)"].auc_loss, "-o", color=TURGOR, lw=2, ms=4,
            label="Turgor index, data up to that date")
    rr = r[(r["index"] == "Rainfall index (as of date)")]
    ax.plot([LABELS[a] for a in rr["asof"]], rr.auc_loss, "-o", color=RAIN, lw=1.5, ms=3,
            label="Rainfall index (Jan-Feb rain so far)")
    final_rain = rr.auc_loss.iloc[-1]
    ax.axhline(final_rain, color=RAIN, ls=":", lw=1)
    ax.axhline(0.5, color=GREY, lw=0.8)
    ax.set_title(region)
    ax.tick_params(axis="x", rotation=60)
    ax.set_ylim(0.45, 0.95)
axes[0].set_ylabel("AUC, municipal loss > 10%")
fig.legend(*axes[0].get_legend_handles_labels(), loc="lower center", ncol=2, frameon=False)
fig.suptitle("How early the index finds losses (harvests 2001-2023, real-time data latency)", y=0.99)
fig.tight_layout(rect=(0, 0.08, 1, 0.97))
fig.savefig(FIGURES / "fig6_early_warning.png", dpi=200)

# ---- fig 7: holdout 2024-2025
h = pd.read_csv(RESULTS / "holdout_metrics.csv")
order = ["Rainfall index", "NDVI only", "Turgor full (+ NDVI)", "Turgor index"]
cols = [RAIN, GREY, "#6FA884", TURGOR]
fig, axes = plt.subplots(1, 2, figsize=(11, 3.8))
groups = [("RS + PR", "2024+2025"), ("RS + PR", "2024"), ("RS + PR", "2025"), ("RS", "2024+2025"), ("PR", "2024+2025")]
for ax, metric, title in [(axes[0], "auc_loss", "AUC (higher is better)"),
                          (axes[1], "basis_risk", "Losses missed, basis risk (lower is better)")]:
    for j, (idx, c) in enumerate(zip(order, cols)):
        vals = [h[(h.region == g) & (h.harvests == y) & (h["index"] == idx)][metric].iloc[0] for g, y in groups]
        ax.bar([i + (j - 1.5) * 0.2 for i in range(len(groups))], vals, 0.2, color=c,
               label={"Turgor full (+ NDVI)": "Turgor v1 (season's own windows)"}.get(idx, idx))
    ax.set_xticks(range(len(groups)))
    ax.set_xticklabels([f"{g}\n{y}" for g, y in groups])
    ax.set_title(title)
axes[0].set_ylim(0.3, 0.9)
axes[0].axhline(0.5, color=GREY, lw=0.8)
fig.legend(*axes[0].get_legend_handles_labels(), loc="lower center", ncol=4, frameon=False)
fig.suptitle("Out-of-sample test: harvests 2024 and 2025, never used to build the index", y=0.99)
fig.tight_layout(rect=(0, 0.08, 1, 0.97))
fig.savefig(FIGURES / "fig7_holdout_2024_2025.png", dpi=200)
print("written fig6, fig7")
