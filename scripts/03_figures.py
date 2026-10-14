"""Figures for the v0 weather + stage index.

    python scripts/03_figures.py
"""
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ssi.config import DATA, DROUGHT_HARVESTS, FIGURES, RESULTS  # noqa: E402

FIGURES.mkdir(exist_ok=True)
INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e4e3df"
BLUE, ORANGE = "#2a78d6", "#eb6834"
plt.rcParams.update({"font.size": 10, "axes.edgecolor": MUTED, "axes.labelcolor": INK,
                     "xtick.color": MUTED, "ytick.color": MUTED, "axes.spines.top": False,
                     "axes.spines.right": False})

s = pd.read_csv(RESULTS / "v0_scores_rs_pr.csv.gz")
s["w"] = s["area_harvested_ha"].fillna(1)


def state_year(df, col):
    return df.groupby(["st", "year"]).apply(lambda g: np.average(g[col], weights=g.w),
                                            include_groups=False)


obs = state_year(s, "rel_anom") * 100

# --- Figure 1: state-year stress vs yield, SSI next to the rainfall index
fig, axes = plt.subplots(2, 2, figsize=(10, 8), sharey="row")
for r, st in enumerate(["RS", "PR"]):
    for c, (col, color) in enumerate([("Rainfall index", ORANGE), ("SSI a priori", BLUE)]):
        ax = axes[r, c]
        x = state_year(s, col).loc[st]
        y = obs.loc[st]
        ax.axhline(0, color=GRID, lw=1, zorder=0)
        ax.axhline(-10, color=GRID, lw=1, ls="--", zorder=0)
        ax.scatter(x, y, s=46, color=color, edgecolor="white", linewidth=1.5, zorder=3)
        for yr in DROUGHT_HARVESTS[st]:
            if yr in x.index:
                ax.annotate(str(yr), (x[yr], y[yr]), xytext=(6, -3), textcoords="offset points",
                            fontsize=9, color=INK)
        rr = np.corrcoef(x, y)[0, 1]
        ax.set_title(f"{st} - {col}   r = {rr:.2f}", loc="left", fontsize=10.5, color=INK)
        ax.grid(axis="y", color=GRID, lw=0.6)
        if c == 0:
            ax.set_ylabel("Harvest yield vs trend (%)")
        if r == 1:
            ax.set_xlabel("Stress score (state, area-weighted; higher = more stress)")
fig.suptitle("Stage-weighted stress tracks soybean losses better than rainfall alone\n"
             "Each dot is one harvest, 1981-2023; dashed line = 10% loss", x=0.02, ha="left",
             fontsize=12, color=INK)
fig.tight_layout()
fig.savefig(FIGURES / "fig1_state_year_stress_vs_yield.png", dpi=160)

# --- Figure 2: skill summary (one measure across indices and regions)
m = pd.read_csv(RESULTS / "v0_weather_metrics.csv")
m = m[m["region"].isin(["RS", "PR", "All 10 states"])]
order = ["Rainfall index", "Unweighted stress", "SSI a priori", "SSI fitted (LOYO)"]
regions = ["RS", "PR", "All 10 states"]
fig, ax = plt.subplots(figsize=(9, 4.2))
w = 0.2
colors = {"Rainfall index": ORANGE, "Unweighted stress": "#9a9890",
          "SSI a priori": BLUE, "SSI fitted (LOYO)": "#1baf7a"}
for i, idx in enumerate(order):
    vals = [m[(m.region == r) & (m["index"] == idx)]["auc_loss"].iloc[0] for r in regions]
    xs = np.arange(len(regions)) + (i - 1.5) * w
    ax.bar(xs, vals, width=w - 0.02, color=colors[idx], label=idx)
    for xx, v in zip(xs, vals):
        ax.text(xx, v + 0.005, f"{v:.2f}", ha="center", fontsize=8, color=MUTED)
ax.set_xticks(range(len(regions)), regions)
ax.set_ylim(0.5, 0.86)
ax.set_ylabel("AUC, municipal loss > 10%")
ax.grid(axis="y", color=GRID, lw=0.6)
ax.legend(frameon=False, ncol=4, loc="upper left", fontsize=9)
ax.set_title("Detecting municipal loss events (leave-one-year-out where fitted)",
             loc="left", fontsize=11, color=INK)
fig.tight_layout()
fig.savefig(FIGURES / "fig2_skill_by_index.png", dpi=160)
print("figures written to", FIGURES)

# --- Figures 3-4: v1 (satellite) results, if available
v1 = RESULTS / "v1_metrics.csv"
if v1.exists():
    m1 = pd.read_csv(v1)
    order1 = ["Rainfall index", "SSI v0 (calendar windows)", "NDVI only",
              "SSI v1 weather (satellite stages)", "SSI v1 full (+ NDVI)"]
    col1 = {"Rainfall index": ORANGE, "SSI v0 (calendar windows)": "#9a9890",
            "NDVI only": "#1baf7a", "SSI v1 weather (satellite stages)": "#9fc3ee",
            "SSI v1 full (+ NDVI)": BLUE}
    regions1 = ["RS", "PR", "RS + PR"]
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.4))
    for ax, (metric, label, lim) in zip(axes, [
            ("state_year_r", "Correlation with state yield, by harvest", (0.4, 1.0)),
            ("basis_risk", "Basis risk: share of real losses missed (lower is better)", (0.2, 0.65))]):
        w1 = 0.16
        for i, idx in enumerate(order1):
            vals = [m1[(m1.region == r) & (m1["index"] == idx)][metric].iloc[0] for r in regions1]
            xs = np.arange(len(regions1)) + (i - 2) * w1
            ax.bar(xs, vals, width=w1 - 0.02, color=col1[idx], label=idx)
            for xx, v in zip(xs, vals):
                ax.text(xx, v + 0.006, f"{v:.2f}", ha="center", fontsize=7, color=MUTED)
        ax.set_xticks(range(len(regions1)), regions1)
        ax.set_ylim(*lim)
        ax.grid(axis="y", color=GRID, lw=0.6)
        ax.set_title(label, loc="left", fontsize=10.5, color=INK)
    h, l = axes[0].get_legend_handles_labels()
    fig.legend(h, l, frameon=False, fontsize=8.5, loc="lower center", ncol=5)
    fig.suptitle("Satellite NDVI by crop stage cuts basis risk (harvests 2001-2023)",
                 x=0.02, ha="left", fontsize=12, color=INK)
    fig.tight_layout(rect=(0, 0.07, 1, 1))
    fig.savefig(FIGURES / "fig3_v1_skill.png", dpi=160)

    # NDVI season curves, RS: drought 2022 vs good 2021 (area-weighted median municipality)
    nd = pd.read_csv(DATA / "modis_ndvi_RS.csv.gz", parse_dates=["date"])
    fig, ax = plt.subplots(figsize=(8, 4))
    for yr, color, lab in [(2021, "#9a9890", "2020/21 (yield +23% vs trend)"),
                           (2022, ORANGE, "2021/22 drought (yield -43%)")]:
        g = nd[nd.harvest_year == yr]
        g = g[(g.date >= f"{yr - 1}-10-01") & (g.date <= f"{yr}-04-30")]
        c = g.groupby("date").apply(lambda d: np.average(d.ndvi, weights=d.n_px), include_groups=False)
        doy = (c.index - pd.Timestamp(f"{yr - 1}-10-01")).days
        ax.plot(doy, c.values, color=color, lw=2, marker="o", ms=4, label=lab)
    ax.set_xticks([0, 31, 61, 92, 123, 151, 182], ["Oct", "Nov", "Dec", "Jan", "Feb", "Mar", "Apr"])
    ax.axvspan(92, 151, color=GRID, alpha=0.5, lw=0)
    ax.text(94, ax.get_ylim()[0] + 0.005, "typical flowering - pod fill", fontsize=8, color=MUTED, va="bottom")
    ax.set_ylabel("Mean NDVI, summer-crop pixels")
    ax.grid(axis="y", color=GRID, lw=0.6)
    ax.legend(frameon=False, fontsize=9, loc="lower right")
    ax.set_title("Rio Grande do Sul soybean canopy from MODIS: the 2022 drought shows from December",
                 loc="left", fontsize=10.5, color=INK)
    fig.tight_layout()
    fig.savefig(FIGURES / "fig4_rs_ndvi_2021_vs_2022.png", dpi=160)
    print("v1 figures written")
