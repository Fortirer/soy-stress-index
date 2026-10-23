"""Illinois validation: backtest 2001-2023 with confidence intervals, holdout
2024-2025, early warning, named drought years, expected loss.

    python midwest/scripts/05_validate.py --price 10.50

Writes midwest/results/il_*.csv. Same rules as the Brazilian validation:
priors unchanged, year-block bootstrap (1,000 resamples), holdout seasons
scored against 2001-2023 normals and a 1990-2023 yield trend.
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from turgor_us import DATA, DATES, END_OF_SEASON, RESULTS, TEST, TRAIN  # noqa: E402
from ssi.expected_loss import brier, calibration, fit_tables, loyo_predict, predict  # noqa: E402
from ssi.index import local_z, ssi  # noqa: E402
from ssi.uncertainty import point_metrics, year_bootstrap  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--price", type=float, default=10.50, help="US$ per bushel of soybean")
args = ap.parse_args()

panel = pd.read_csv(DATA / "il_panel.csv.gz")
panel = panel[panel["year"].between(2001, 2025)]
full = pd.read_csv(DATA / "il_full_features.csv.gz")
asof = pd.read_csv(DATA / "il_asof_features.csv.gz")
end = asof[asof["asof"] == END_OF_SEASON].drop(columns="asof")
rain = end[["fips5", "year", "pcp_critical"]]

df = panel.merge(full, on=["fips5", "year"], how="inner").merge(rain, on=["fips5", "year"], how="left")
df = df.reset_index(drop=True)
PRODUCT = "Turgor index"


def v1(d):
    x = d.copy()
    x["veg_water_deficit_mm"], x["win_water_deficit_mm"] = x["sw_veg_water_deficit_mm"], x["sw_rep_water_deficit_mm"]
    x["veg_edd"], x["win_edd"] = x["sw_veg_edd"], x["sw_rep_edd"]
    return x


def all_scores(d, ref=None):
    x = v1(d)
    prod = d[["fips5", "year"]].merge(end, on=["fips5", "year"], how="left")
    return {
        "Rainfall Jul-Aug": (-local_z(d, "pcp_critical", ref=ref)).fillna(0).values,
        "Palmer drought index, Aug": (-local_z(d, "pdsi08", ref=ref)).fillna(0).values,
        "NDVI only": (-local_z(d, "ndvi_reproductive", ref=ref)).fillna(0).values,
        "Turgor weather only": ssi(x.drop(columns=["ndvi_vegetative", "ndvi_reproductive"]), ref=ref).values,
        "Turgor full season (+NDVI)": ssi(x, ref=ref).values,
        PRODUCT: ssi(prod, ref=ref).values,
    }


# ---------------------------------------------------------------- backtest
bt = df[df["year"].isin(TRAIN)].reset_index(drop=True)
sc = all_scores(bt)
rows = [{"test": "backtest 2001-2023", "index": k, "n": len(bt), "loss_rate": bt["loss"].mean(),
         **point_metrics(bt, v)} for k, v in sc.items()]
ci = year_bootstrap(bt, sc, n=1000, reference="Rainfall Jul-Aug")
ci.round(3).to_csv(RESULTS / "il_backtest_ci.csv", index=False)
keep = bt[["fips5", "year", "acres_harvested", "yield_bu_ac", "yield_trend", "rel_anom", "loss"]].copy()
for k, v in sc.items():
    keep[k] = v

# ---------------------------------------------------------------- holdout
ref = df["year"].isin(TRAIN).values
sc_all = all_scores(df, ref=ref)
te = df["year"].isin(TEST).values
ho = df[te].reset_index(drop=True)
for k, v in sc_all.items():
    rows.append({"test": "holdout 2024-2025", "index": k, "n": len(ho), "loss_rate": ho["loss"].mean(),
                 **point_metrics(ho, v[te])})
res = pd.DataFrame(rows).round(3)
res.to_csv(RESULTS / "il_metrics.csv", index=False)
scores_all = df[["fips5", "year", "acres_harvested", "yield_bu_ac", "yield_trend", "rel_anom", "loss"]].copy()
for k, v in sc_all.items():
    scores_all[k] = v
scores_all.round(4).to_csv(RESULTS / "il_county_scores_2001_2025.csv.gz", index=False)

# ---------------------------------------------------------------- early warning (2001-2023)
ew = []
base = panel[panel["year"].isin(TRAIN)][["st", "fips5", "year", "area_harvested_ha", "rel_anom", "loss"]]
for d in DATES:
    f = base.merge(asof[asof["asof"] == d], on=["fips5", "year"], how="inner").reset_index(drop=True)
    for name, s in [("Turgor index (data up to date)", ssi(f).values),
                    ("Turgor weather only (data up to date)", ssi(f.drop(columns=["ndvi_vegetative", "ndvi_reproductive"])).values),
                    ("Rainfall Jul-Aug (rain so far)", (-local_z(f, "pcp_critical")).fillna(0).values)]:
        ew.append({"asof": d, "index": name, "n": len(f), **point_metrics(f, s)})
ew = pd.DataFrame(ew).round(3)
ew.to_csv(RESULTS / "il_early_warning.csv", index=False)

# ---------------------------------------------------------------- named drought years
yrs = []
w = bt["acres_harvested"]
obs = bt.assign(w=w).groupby("year").apply(lambda g: np.average(g.rel_anom, weights=g.w), include_groups=False)
for k, v in sc.items():
    agg = bt.assign(s=v, w=w).groupby("year").apply(lambda g: np.average(g.s, weights=g.w), include_groups=False)
    pct = agg.rank(pct=True) * 100
    for y in [2002, 2003, 2007, 2009, 2011, 2012]:
        yrs.append({"year": y, "observed_yield_vs_trend_%": round(obs[y] * 100, 1), "index": k,
                    "stress_percentile": round(pct[y])})
yrs = pd.DataFrame(yrs).pivot_table(index=["year", "observed_yield_vs_trend_%"], columns="index",
                                    values="stress_percentile").reset_index()
yrs.to_csv(RESULTS / "il_drought_years.csv", index=False)

# ---------------------------------------------------------------- expected loss
el = df.assign(score=sc_all[PRODUCT])[["st", "fips5", "year", "rel_anom", "yield_trend", "score"]].copy()
el["loss"] = (el["rel_anom"] < -0.10).astype(float)
tr = el[el["year"].isin(TRAIN)]
lo = loyo_predict(tr)
clim_tr = np.full(len(tr), tr["loss"].mean())
m = [{"test": "leave-one-season-out 2001-2023", "brier": brier(lo["p_loss"].values, tr["loss"].values),
      "brier_climatology": brier(clim_tr, tr["loss"].values),
      "expected_yield_r": np.corrcoef(lo["expected_anomaly"], tr["rel_anom"])[0, 1]}]
tab = fit_tables(tr)
tab.to_csv(RESULTS / "il_expected_loss_models.csv", index=False)
tt = el[el["year"].isin(TEST)]
pr = predict(tab, tt)
m.append({"test": "holdout 2024-2025", "brier": brier(pr["p_loss"].values, tt["loss"].values),
          "brier_climatology": brier(np.full(len(tt), tr["loss"].mean()), tt["loss"].values),
          "expected_yield_r": np.corrcoef(pr["expected_anomaly"], tt["rel_anom"])[0, 1]})
m = pd.DataFrame(m)
m["brier_skill"] = 1 - m["brier"] / m["brier_climatology"]
m.round(3).to_csv(RESULTS / "il_expected_loss_metrics.csv", index=False)
calibration(lo["p_loss"], tr["loss"]).round(3).to_csv(RESULTS / "il_expected_loss_calibration.csv", index=False)
# dollars: expected shortfall x trend yield x price
allp = pd.concat([lo.assign(year=tr["year"].values, yield_trend=tr["yield_trend"].values),
                  pr.assign(year=tt["year"].values, yield_trend=tt["yield_trend"].values)])
allp["expected_shortfall_usd_ac"] = allp["expected_shortfall"] * allp["yield_trend"] * args.price
real = el.assign(short=np.clip(-el["rel_anom"], 0, None) * el["yield_trend"] * args.price)
anchors = pd.DataFrame([{
    "seasons": "2016-2025", "price_usd_bu": args.price,
    "mean_shortfall_usd_ac": real[real.year >= 2016]["short"].mean(),
    "p90_season_shortfall_usd_ac": real.groupby("year")["short"].mean().loc[2001:].quantile(0.9),
    "worst_season": int(real.groupby("year")["short"].mean().idxmax()),
    "worst_season_shortfall_usd_ac": real.groupby("year")["short"].mean().max(),
    "revenue_at_trend_usd_ac": (real[real.year >= 2016]["yield_trend"] * args.price).mean()}]).round(2)
anchors.to_csv(RESULTS / "il_value_anchors.csv", index=False)

pd.set_option("display.width", 220)
print(res.to_string(index=False))
print(ci[ci.metric != "state_year_r"].round(3).to_string(index=False))
print(ew.pivot_table(index="asof", columns="index", values="auc_loss", sort=False))
print(yrs.round(0).to_string(index=False))
print(m.round(3).to_string(index=False))
print(anchors.to_string(index=False))
