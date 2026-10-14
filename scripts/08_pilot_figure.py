"""Figure for the Sentinel-2 field pilot.

    python scripts/08_pilot_figure.py
"""
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ssi.config import FIGURES, RESULTS  # noqa: E402

INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e4e3df"
GOOD, DRY = "#9a9890", "#eb6834"
plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.edgecolor": MUTED, "xtick.color": MUTED, "ytick.color": MUTED})

s = pd.read_csv(RESULTS / "pilot_field_series.csv", parse_dates=["date"])
ch = pd.read_csv(RESULTS / "pilot_field_change.csv")
order = ["Dom Pedrito", "Cruz Alta", "Tupanciretã"]
fig, axes = plt.subplots(1, 3, figsize=(12, 3.9), sharey=True)
for ax, m in zip(axes, order):
    for yr, color in [(2021, GOOD), (2022, DRY)]:
        g = s[(s.municipality == m) & (s.harvest_year == yr)]
        for f, gf in g.groupby("field"):
            doy = (gf.date - pd.Timestamp(f"{yr - 1}-10-01")).dt.days
            keep = (doy >= 0) & (doy <= 211)
            ax.plot(doy[keep], gf.ndvi[keep], color=color, lw=1.1, alpha=0.8,
                    label=("2020/21" if yr == 2021 else "2021/22 drought") if f == 1 else None)
    c = ch[ch.municipality == m].iloc[0]
    ax.set_title(f"{m}\nIBGE yield vs trend: {c.ibge_yield_vs_trend_2021_pct:+.0f}% to "
                 f"{c.ibge_yield_vs_trend_2022_pct:+.0f}%", loc="left", fontsize=10, color=INK)
    ax.set_xticks([0, 61, 123, 182], ["Oct", "Dec", "Feb", "Apr"])
    ax.grid(axis="y", color=GRID, lw=0.6)
axes[0].set_ylabel("Field NDVI (Sentinel-2, median of plot)")
axes[0].legend(frameon=False, fontsize=9, loc="upper left")
fig.suptitle("Five ~35 ha soybean plots per municipality: drought damage differs field by field",
             x=0.02, ha="left", fontsize=12, color=INK)
fig.tight_layout()
fig.savefig(FIGURES / "fig5_sentinel2_fields.png", dpi=160)
print("ok")
