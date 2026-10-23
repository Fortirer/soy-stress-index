"""Figures for the Illinois validation.

    python midwest/scripts/07_figures.py
"""
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from turgor_us import DATES, FIGURES, RESULTS  # noqa: E402

GREEN, BLUE, ORANGE, GREY, INK = "#1E5B3A", "#2A78D6", "#B4541A", "#8A968F", "#12291D"
plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})

# 1. early warning
ew = pd.read_csv(RESULTS / "il_early_warning.csv", dtype={"asof": str})
lab = [pd.Timestamp(f"2001-{d}").strftime("%-d %b") for d in DATES]
fig, ax = plt.subplots(figsize=(8, 4.2), dpi=150)
for name, c, lw in [("Turgor index (data up to date)", GREEN, 2.5),
                    ("Turgor weather only (data up to date)", GREY, 1.5),
                    ("Rainfall Jul-Aug (rain so far)", BLUE, 1.8)]:
    g = ew[ew["index"] == name].set_index("asof").loc[DATES]
    ax.plot(lab, g["auc_loss"], marker="o", color=c, lw=lw, label=name)
final_rain = ew[(ew["index"] == "Rainfall Jul-Aug (rain so far)") & (ew["asof"] == DATES[-1])]["auc_loss"].iloc[0]
ax.axhline(final_rain, color=BLUE, ls=":", lw=1)
ax.axhline(0.5, color="#999", lw=0.8)
ax.set_ylabel("AUC, county loss > 10%")
ax.set_title("Illinois: how early the index finds soybean losses (2001-2023, real-time data)")
ax.legend(frameon=False, fontsize=8.5, loc="lower right")
ax.set_ylim(0.45, 0.95)
fig.tight_layout()
fig.savefig(FIGURES / "il_early_warning.png")
plt.close(fig)

# 2. skill by index, backtest and holdout
m = pd.read_csv(RESULTS / "il_metrics.csv")
order = ["Turgor index", "Turgor full season (+NDVI)", "Turgor weather only", "NDVI only",
         "Rainfall Jul-Aug", "Palmer drought index, Aug"]
# 2025 MODIS July-October composites are missing from the archive: indices that
# need the season's own NDVI curve are not scored on the holdout
no_holdout = {"Turgor full season (+NDVI)", "NDVI only"}
fig, axs = plt.subplots(1, 2, figsize=(10.5, 4.4), dpi=150, sharey=True)
for ax, (metric, title) in zip(axs, [("auc_loss", "AUC, loss > 10% (higher is better)"),
                                     ("basis_risk", "Basis risk (lower is better)")]):
    y = np.arange(len(order))
    for test, c, dy in [("backtest 2001-2023", GREEN, -0.18), ("holdout 2024-2025", ORANGE, 0.18)]:
        v = m[m["test"] == test].set_index("index").loc[order, metric]
        for yy, (k, vv) in zip(y + dy, v.items()):
            if test.startswith("holdout") and k in no_holdout:
                ax.text(0.01, yy, "n/a (2025 NDVI incomplete)", va="center", fontsize=7, color=GREY)
                continue
            ax.barh(yy, vv, height=0.34, color=c, label=test if k == order[0] else None)
            ax.text(vv + 0.005, yy, f"{vv:.2f}", va="center", fontsize=7.5)
    ax.set_yticks(y, order)
    ax.set_title(title, fontsize=10)
    ax.set_xlim(0, 1.05)
axs[0].invert_yaxis()
h, l = axs[0].get_legend_handles_labels()
fig.legend(h, l, frameon=False, fontsize=8.5, loc="lower center", ncol=2)
fig.suptitle("Illinois counties: Turgor vs. rainfall, Palmer drought index and NDVI "
             "(holdout = 123 county-seasons, 17 losses)", fontsize=10.5)
fig.tight_layout(rect=(0, 0.06, 1, 1))
fig.savefig(FIGURES / "il_skill_by_index.png")
plt.close(fig)
print("figures written")
