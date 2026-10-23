"""Replay the 2012 Illinois drought as the weekly monitor would have shown it.

    python midwest/scripts/06_replay_2012.py

On 1 August and 15 August 2012, with only the data available then (typical
windows, data latency) and with 2012 left out of every county's normal:
each county's stress is ranked against its own other seasons on the same
date (severe > 95th percentile, high > 85th, watch > 70th), as in the
Brazilian monitor. Then the classes are compared with the final NASS yields.
Also replays 2023 (June flash drought, good final yields) as a false-alarm check.
Writes midwest/results/il_replay_*.csv and midwest/figures/il_replay_*.png.
"""
import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Patch, Polygon
from sklearn.metrics import roc_auc_score

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from turgor_us import DATA, FIGURES, RESULTS  # noqa: E402
from ssi.index import ssi  # noqa: E402

CLASSES = [("severe", 95, "#B2241E"), ("high", 85, "#E68A3A"), ("watch", 70, "#F2CF7A"), ("normal", -1, "#DDE8E0")]
panel = pd.read_csv(DATA / "il_panel.csv.gz")
asof = pd.read_csv(DATA / "il_asof_features.csv.gz")
geo = json.load(open(DATA / "il_counties.geojson"))["features"]
summary = []


def replay(year, mmdd):
    f = asof[(asof["asof"] == mmdd) & asof["year"].between(2001, 2025)].reset_index(drop=True)
    ref = (f["year"] != year).values
    f["score"] = ssi(f, ref=ref).values
    pct = {}
    for code, g in f.groupby("fips5"):
        other = g.loc[g["year"] != year, "score"]
        now = g.loc[g["year"] == year, "score"]
        if len(now) and len(other) >= 10:
            pct[code] = 100 * (other < now.iloc[0]).mean()
    t = pd.DataFrame({"fips5": list(pct), "percentile": list(pct.values())})
    t["class"] = t["percentile"].apply(lambda p: next(c for c, thr, _ in CLASSES if p > thr))
    t = t.merge(panel[panel["year"] == year][["fips5", "county", "yield_bu_ac", "yield_trend", "rel_anom", "loss"]],
                on="fips5", how="left")
    t.round(3).to_csv(RESULTS / f"il_replay_{year}_{mmdd}.csv", index=False)
    by = t.dropna(subset=["rel_anom"]).groupby("class").agg(
        counties=("fips5", "size"), mean_yield_vs_trend=("rel_anom", "mean"), share_loss_gt10=("loss", "mean"))
    y = t.dropna(subset=["rel_anom"])
    auc = roc_auc_score(y["loss"], y["percentile"]) if y["loss"].nunique() > 1 else np.nan
    for c, r in by.iterrows():
        summary.append({"season": year, "asof": mmdd, "class": c, **r.to_dict(), "auc": auc})

    fig, ax = plt.subplots(figsize=(5.6, 8), dpi=150)
    col = dict((c, k) for c, _, k in CLASSES)
    cls = t.set_index("fips5")["class"]
    for ft in geo:
        ring = np.array(ft["geometry"]["coordinates"][0])
        c = cls.get(int(ft["id"]))
        ax.add_patch(Polygon(ring, closed=True, facecolor=col[c] if c else "#FFFFFF", edgecolor="#7A8A80", lw=0.3))
    ax.autoscale_view()
    ax.set_aspect(1 / np.cos(np.radians(40)))
    ax.axis("off")
    n = cls.value_counts()
    ax.legend(handles=[Patch(facecolor=k, edgecolor="#7A8A80", label=f"{c} ({n.get(c, 0)})") for c, _, k in CLASSES],
              title="Stress vs. past seasons", loc="lower left", frameon=False, fontsize=9)
    d = pd.Timestamp(f"{year}-{mmdd}").strftime("%-d %b %Y")
    ax.set_title(f"Turgor index, Illinois soybean\ndata up to {d}", fontsize=11)
    fig.text(0.02, 0.01, f"{year} excluded from each county's normal. Severe > 95th percentile of the county's own\n"
             "seasons at this date; high > 85th; watch > 70th. MODIS + NASA POWER, real-time latency.",
             fontsize=6.5, color="#56695E")
    fig.savefig(FIGURES / f"il_replay_{year}_{mmdd}.png", bbox_inches="tight")
    plt.close(fig)


for yr, dates in {2012: ["07-15", "08-01", "08-15"], 2023: ["07-15", "08-01"]}.items():
    for d in dates:
        replay(yr, d)
s = pd.DataFrame(summary)
s.round(3).to_csv(RESULTS / "il_replay_summary.csv", index=False)
pd.set_option("display.width", 200)
print(s.round(3).to_string(index=False))
