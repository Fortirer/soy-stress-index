"""Expected yield loss (%), P(loss > 10%) and R$/ha from the Turgor index.

    python scripts/18_expected_loss.py [--price 153.49]

Tests the maps honestly:
  - 2001-2023: leave-one-season-out (each season predicted by maps fitted on the others)
  - 2024-2025: maps fitted on 2001-2023 only
Then fits the final maps on 2001-2025:
  - end of season (Turgor index, scripts 06/12)  -> results/expected_loss_models.csv
  - every weekly anchor of the live monitor       -> results/expected_loss_models_anchors.csv
Writes per municipality-season predictions, calibration tables and figure 8.

Price: soybean, R$ per 60 kg bag. Default = CEPEA/ESALQ Paraná indicator on
28 Sep 2026 (R$ 153.49). Change with --price for a portfolio report.
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import theilslopes

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ssi.config import DATA, FIGURES, RESULTS  # noqa: E402
from ssi.early import turgor_index  # noqa: E402
from ssi.expected_loss import (brier, calibration, fit_tables, loyo_predict, predict,  # noqa: E402
                               shortfall_rs_per_ha)

ap = argparse.ArgumentParser()
ap.add_argument("--price", type=float, default=153.49, help="R$ per 60 kg bag")
args = ap.parse_args()

ms = pd.read_csv(RESULTS / "municipal_scores_2001_2025.csv.gz")
ms = ms.rename(columns={"Turgor index": "score"}).dropna(subset=["score", "rel_anom"]).reset_index(drop=True)
ms["trend_kg_ha"] = ms["yield_kg_ha"] / (1 + ms["rel_anom"])
train = ms[ms["year"] <= 2023].reset_index(drop=True)
test = ms[ms["year"] >= 2024].reset_index(drop=True)

# ---------------------------------------------------------------- 1. honest predictions
p_tr = loyo_predict(train)
p_te = predict(fit_tables(train), test)
pred = pd.concat([pd.concat([train, p_tr], axis=1).assign(test="loyo 2001-2023"),
                  pd.concat([test, p_te], axis=1).assign(test="holdout 2024-2025")], ignore_index=True)

rows, cal = [], []
for (name, st), d in pred.groupby(["test", "st"]):
    pass
for name, d0 in pred.groupby("test"):
    for region, sts in {"RS + PR": ["RS", "PR"], "RS": ["RS"], "PR": ["PR"]}.items():
        d = d0[d0["st"].isin(sts)]
        y = d["loss"].values
        clim = train[train["st"].isin(sts)].groupby("st")["loss"].mean()
        p_clim = d["st"].map(clim).values               # baseline: each state's past loss rate
        b, b0 = brier(d["p_loss"].values, y), brier(p_clim, y)
        rows.append({"test": name, "region": region, "n": len(d),
                     "brier": round(b, 4), "brier_climatology": round(b0, 4), "brier_skill": round(1 - b / b0, 3),
                     "anomaly_mae": round(float(np.mean(np.abs(d["expected_anomaly"] - d["rel_anom"]))), 4),
                     "anomaly_mae_no_model": round(float(np.mean(np.abs(d["rel_anom"] - train["rel_anom"].mean()))), 4),
                     "anomaly_r": round(float(np.corrcoef(d["expected_anomaly"], d["rel_anom"])[0, 1]), 3),
                     "shortfall_mae": round(float(np.mean(np.abs(d["expected_shortfall"] - np.clip(-d["rel_anom"], 0, None)))), 4)})
        if region == "RS + PR":
            for tgt, obs in [("p_loss", d["loss"]), ("expected_anomaly", d["rel_anom"])]:
                c = calibration(d[tgt], obs)
                cal.append(c.assign(test=name, target=tgt))
metrics = pd.DataFrame(rows)
metrics.to_csv(RESULTS / "expected_loss_metrics.csv", index=False)
cal = pd.concat(cal, ignore_index=True).round(4)
cal.to_csv(RESULTS / "expected_loss_calibration.csv", index=False)

# ---------------------------------------------------------------- 2. final maps
final = fit_tables(ms)
final.to_csv(RESULTS / "expected_loss_models.csv", index=False)
pf = predict(final, ms)
out = pd.concat([ms[["st", "fips5", "year", "score", "yield_kg_ha", "trend_kg_ha", "rel_anom", "loss"]], pf], axis=1)
out["expected_shortfall_rs_ha"] = shortfall_rs_per_ha(out["expected_shortfall"], out["trend_kg_ha"], args.price)
# honest columns too (what the model would have said without that season)
hon = pred.set_index(["fips5", "year"])[["p_loss", "expected_anomaly", "expected_shortfall"]].add_suffix("_out_of_sample")
out = out.merge(hon, left_on=["fips5", "year"], right_index=True, how="left")
out.rename(columns={"score": "turgor_index"}).round(4).to_csv(RESULTS / "expected_loss_2001_2025.csv.gz", index=False)

# per weekly anchor, for the live monitor (index from the monitor reference)
ref = pd.read_csv(DATA / "monitor_reference.csv.gz")
y = ms[["fips5", "year", "st", "rel_anom"]]
parts = []
for a, g in ref.groupby("anchor"):
    g = g.reset_index(drop=True)
    s = g[["fips5", "year"]].assign(score=turgor_index(g).values).merge(y, on=["fips5", "year"], how="inner")
    parts.append(fit_tables(s).assign(anchor=a))
pd.concat(parts, ignore_index=True).round(5).to_csv(RESULTS / "expected_loss_models_anchors.csv", index=False)

# trend yield for the next season (Theil-Sen on 2001-2025 yields), for R$/ha in the monitor
tr = []
for code, g in ms.groupby("fips5"):
    if len(g) >= 10:
        sl, ic, *_ = theilslopes(g["yield_kg_ha"], g["year"])
        tr.append({"fips5": code, "intercept": ic, "slope": sl})
pd.DataFrame(tr).round(4).to_csv(RESULTS / "yield_trend_next.csv", index=False)

# ---------------------------------------------------------------- 3. figure
import matplotlib  # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})
fig, axes = plt.subplots(1, 3, figsize=(13, 4))
col = {"loyo 2001-2023": "#1E5B3A", "holdout 2024-2025": "#2A78D6"}
for name, c in cal[cal["target"] == "p_loss"].groupby("test"):
    axes[0].plot(c["predicted"], c["observed"], "-o", color=col[name], label=name, ms=4)
axes[0].plot([0, 1], [0, 1], color="#8A9A90", lw=0.8, ls=":")
axes[0].set(xlabel="Predicted P(loss > 10%)", ylabel="Observed share with loss > 10%",
            title="Probability of loss: calibration", xlim=(0, 1), ylim=(0, 1))
axes[0].legend(frameon=False, loc="upper left")
for name, c in cal[cal["target"] == "expected_anomaly"].groupby("test"):
    axes[1].plot(100 * c["predicted"], 100 * c["observed"], "-o", color=col[name], label=name, ms=4)
lim = (-45, 20)
axes[1].plot(lim, lim, color="#8A9A90", lw=0.8, ls=":")
axes[1].set(xlabel="Predicted yield vs trend (%)", ylabel="Observed yield vs trend (%)",
            title="Expected yield: calibration by decile", xlim=lim, ylim=lim)
for st, c in [("RS", "#B4541A"), ("PR", "#2A78D6")]:
    t = final[(final["st"] == st) & (final["target"] == "expected_anomaly")]
    axes[2].plot(t["x"], 100 * t["y"], color=c, lw=2, label=f"{st}: expected yield vs trend")
    t = final[(final["st"] == st) & (final["target"] == "p_loss")]
    axes[2].plot(t["x"], 100 * t["y"], color=c, lw=1.2, ls="--", label=f"{st}: P(loss > 10%)")
axes[2].axhline(0, color="#8A9A90", lw=0.8)
axes[2].set(xlabel="Turgor index (end of season)", ylabel="%", title="Final maps (fitted on 2001-2025)", xlim=(-4, 10))
axes[2].legend(frameon=False, fontsize=8)
fig.tight_layout()
fig.savefig(FIGURES / "fig8_expected_loss.png", dpi=200)

pd.set_option("display.width", 200)
print(metrics.to_string(index=False))
print(cal[cal["target"] == "p_loss"].to_string(index=False))
