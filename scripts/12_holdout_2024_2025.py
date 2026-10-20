"""Out-of-sample test on the 2024 and 2025 harvests (never used before).

    python scripts/04_download_modis.py --states RS --first 2024 --last 2025   # and PR
    python scripts/09_extend_weather.py
    python scripts/12_holdout_2024_2025.py

Rules, so that nothing from the test seasons leaks in:
  - yields: IBGE PAM (SIDRA table 1612), downloaded fresh, data/ibge/
  - yield trend: per municipality, Theil-Sen line fitted on 2001-2023 only,
    extrapolated to 2024 and 2025; loss = yield > 10% below that trend
  - z-scores: mean and SD of each municipality's 2001-2023 seasons only
  - stage weights and component weights: unchanged physiology priors
  - early-warning windows: each municipality's median 2001-2023 windows
Writes results/holdout_*.csv.
"""
import json
import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import theilslopes

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ssi.config import DATA, LOSS_THRESHOLD, RESULTS  # noqa: E402
from ssi.data import load_boundaries  # noqa: E402
from ssi.early import WINDOWS, asof_features, typical_windows  # noqa: E402
from ssi.index import local_z, rainfall_index, ssi  # noqa: E402
from ssi.satellite import stage_table  # noqa: E402
from ssi.uncertainty import point_metrics  # noqa: E402
from ssi.weather import daily_indicators, stage_weather  # noqa: E402

TRAIN = range(2001, 2024)
TEST = [2024, 2025]
DATES = ["01-01", "01-15", "02-01", "02-15", "03-01", "03-15", "04-01"]
UF = {"43": "RS", "41": "PR"}


# ---------------------------------------------------------------- 1. yields
def ibge_panel() -> pd.DataFrame:
    rows = []
    for uf in UF:
        d = pd.DataFrame(json.load(open(DATA / "ibge" / f"pam_soja_{uf}.json"))[1:])
        d["V"] = pd.to_numeric(d["V"], errors="coerce")
        w = d.pivot_table(index=["D1C", "D3C"], columns="D2C", values="V").reset_index()
        w.columns = ["fips5", "year", "yield_kg_ha", "area_harvested_ha"]
        rows.append(w)
    p = pd.concat(rows)
    p["fips5"], p["year"] = p["fips5"].astype(int), p["year"].astype(int)
    p = p[(p["year"] >= 2001) & (p["yield_kg_ha"] > 0)]
    p["st"] = p["fips5"].astype(str).str[:2].map(UF)
    out = []
    for code, g in p.groupby("fips5"):
        tr = g[g["year"].isin(TRAIN)]
        if len(tr) < 12:
            continue
        slope, icpt, *_ = theilslopes(tr["yield_kg_ha"], tr["year"])
        g = g.assign(yield_trend=icpt + slope * g["year"])
        out.append(g)
    p = pd.concat(out)
    p = p[p["yield_trend"] > 0]
    p["rel_anom"] = p["yield_kg_ha"] / p["yield_trend"] - 1
    p["loss"] = (p["rel_anom"] < LOSS_THRESHOLD).astype(int)
    return p


# ---------------------------------------------------------------- 2. weather by stage
feats = [f for f in load_boundaries()["features"] if f["properties"]["st"] in ("RS", "PR")]
st_train = pd.read_csv(DATA / "ndvi_stages_2001_2023.csv.gz")
ndvi_all = pd.concat([pd.read_csv(DATA / f"modis_ndvi_{s}.csv.gz", parse_dates=["date"]) for s in ["RS", "PR"]])
ndvi_test = ndvi_all[ndvi_all["harvest_year"].isin(TEST)]
nd_by_code = {c: g for c, g in ndvi_test.groupby("fips5")}
# typical windows for the test seasons = median of all 2001-2023 seasons
tw = st_train[["fips5", "year"] + WINDOWS].copy()
for c in WINDOWS:
    tw[c] = (pd.to_datetime(tw[c]) - pd.to_datetime((tw["year"] - 1).astype(str) + "-09-01")).dt.days
med = tw.groupby("fips5")[WINDOWS].median()
typ = pd.concat([med.assign(year=y) for y in TEST]).reset_index().set_index(["fips5", "year"])
fallback = typical_windows(st_train).assign(st=lambda d: d.fips5.astype(str).str[:2]).groupby("st")[WINDOWS].median()


def one(f):
    code = int(f["id"])
    lat = float(np.array(f["geometry"]["coordinates"][0])[:, 1].mean())
    w = pd.concat([pd.read_csv(DATA / "power" / f"{code}.csv.gz", index_col=0, parse_dates=True),
                   pd.read_csv(DATA / "power_ext" / f"{code}.csv.gz", index_col=0, parse_dates=True)])
    ind = daily_indicators(w[~w.index.duplicated()].sort_index(), lat)
    nd = nd_by_code.get(code, pd.DataFrame(columns=["date", "ndvi", "harvest_year"]))
    asof = asof_features(ind, nd, code, TEST, DATES + ["04-15"], typ, fallback.loc[str(code)[:2]])
    full = []
    stg = stage_table(nd) if len(nd) else pd.DataFrame()
    for yr in TEST:
        s = stg[stg["year"] == yr] if len(stg) else stg
        if len(s):
            s = s.iloc[0]
            win, src = {k: s[k] for k in ["veg_start", "veg_end", "rep_start", "rep_end"]}, "ndvi"
            nveg, nrep = s["ndvi_vegetative"], s["ndvi_reproductive"]
        else:
            win = {"veg_start": f"{yr - 1}-11-01", "veg_end": f"{yr - 1}-12-31",
                   "rep_start": f"{yr}-01-01", "rep_end": f"{yr}-02-28"}
            src, nveg, nrep = "calendar", np.nan, np.nan
        full.append({"fips5": code, "year": yr, "window_source": src,
                     "ndvi_vegetative": nveg, "ndvi_reproductive": nrep,
                     **{f"sw_{k}": v for k, v in stage_weather(ind, win).items()}})
    return asof, full


def v1_inputs(df):
    d = df.copy()
    d["veg_water_deficit_mm"], d["win_water_deficit_mm"] = d["sw_veg_water_deficit_mm"], d["sw_rep_water_deficit_mm"]
    d["veg_edd"], d["win_edd"] = d["sw_veg_edd"], d["sw_rep_edd"]
    return d


if __name__ == "__main__":
    yields = ibge_panel()
    with Pool(2) as p:
        res = p.map(one, feats, chunksize=16)
    asof_test = pd.DataFrame([r for a, _ in res for r in a])
    full_test = pd.DataFrame([r for _, f in res for r in f])
    asof_test.to_csv(DATA / "asof_features_2024_2025.csv.gz", index=False)
    full_test.to_csv(DATA / "stage_features_2024_2025.csv.gz", index=False)

    # training features (2001-2023), same definitions
    wx_tr = pd.read_csv(DATA / "stage_weather.csv.gz")
    full_tr = wx_tr.merge(st_train[["fips5", "year", "ndvi_vegetative", "ndvi_reproductive"]],
                          on=["fips5", "year"], how="left")
    asof_tr = pd.read_csv(DATA / "asof_features.csv.gz")

    # ---- full season, real satellite windows
    full = pd.concat([full_tr, full_test], ignore_index=True)
    full = yields.merge(full, on=["fips5", "year"], how="inner").reset_index(drop=True)
    # rainfall baseline from POWER Jan-Feb rain (as of 15 Apr = whole window)
    rain = pd.concat([asof_tr, asof_test])
    rain = rain[rain["asof"] == "04-15"][["fips5", "year", "pcp_critical"]]
    full = full.merge(rain, on=["fips5", "year"], how="left")
    ref = full["year"].isin(TRAIN).values
    d = v1_inputs(full)
    scores = {
        "Rainfall index": rainfall_index(full, ref=ref).values,
        "NDVI only": (-local_z(full, "ndvi_reproductive", ref=ref)).fillna(0).values,
        "Turgor weather only": ssi(d.drop(columns=["ndvi_vegetative", "ndvi_reproductive"]), ref=ref).values,
        "Turgor full (+ NDVI)": ssi(d, ref=ref).values,
    }
    keep = full[["st", "fips5", "year", "area_harvested_ha", "yield_kg_ha", "rel_anom", "loss"]].copy()
    for k, v in scores.items():
        keep[k] = v
    keep.round(4).to_csv(RESULTS / "municipal_scores_2001_2025.csv.gz", index=False)
    test = ~ref
    rows = []
    for region, sts in {"RS + PR": ["RS", "PR"], "RS": ["RS"], "PR": ["PR"]}.items():
        for yrs in [TEST, [2024], [2025]]:
            m = test & full["st"].isin(sts).values & full["year"].isin(yrs).values
            g = full[m].reset_index(drop=True)
            if g["loss"].nunique() < 2:
                continue
            for k, s in scores.items():
                pm = point_metrics(g, s[m])
                rows.append({"region": region, "harvests": "+".join(map(str, yrs)), "index": k,
                             "n": len(g), "loss_rate": round(g["loss"].mean(), 3),
                             "auc_loss": pm["auc_loss"], "basis_risk": pm["basis_risk"]})
    hold = pd.DataFrame(rows).round(3)
    hold.to_csv(RESULTS / "holdout_metrics.csv", index=False)

    # state-level view: observed loss vs index percentile among all 2001-2025 seasons
    full["w"] = full["area_harvested_ha"].fillna(1)
    st_rows = []
    for k, s in scores.items():
        t = full.assign(s=s)
        agg = t.groupby(["st", "year"]).apply(lambda g: pd.Series({
            "obs": np.average(g.rel_anom, weights=g.w), "s": np.average(g.s, weights=g.w)}), include_groups=False)
        agg["pct"] = agg.groupby("st")["s"].rank(pct=True) * 100
        for (st, yr), r in agg.iterrows():
            if yr in TEST:
                st_rows.append({"st": st, "harvest": yr, "yield_vs_trend_%": round(100 * r.obs, 1),
                                "index": k, "stress_percentile_2001_2025": round(r.pct)})
    stt = pd.DataFrame(st_rows).pivot_table(index=["st", "harvest", "yield_vs_trend_%"], columns="index",
                                            values="stress_percentile_2001_2025").reset_index()
    stt.to_csv(RESULTS / "holdout_state_years.csv", index=False)

    # ---- early warning on the test seasons
    ew = []
    for dt in DATES:
        a = pd.concat([asof_tr, asof_test])
        a = yields.merge(a[a["asof"] == dt], on=["fips5", "year"], how="inner").reset_index(drop=True)
        r = a["year"].isin(TRAIN).values
        s_t = ssi(a, ref=r).values
        s_r = rainfall_index(a, ref=r).values
        for region, sts in {"RS + PR": ["RS", "PR"], "RS": ["RS"], "PR": ["PR"]}.items():
            m = ~r & a["st"].isin(sts).values
            g = a[m].reset_index(drop=True)
            for k, s in [("Turgor (as of date)", s_t), ("Rainfall index (as of date)", s_r)]:
                pm = point_metrics(g, s[m])
                ew.append({"asof": dt, "region": region, "index": k, "auc_loss": pm["auc_loss"],
                           "basis_risk": pm["basis_risk"]})
    ew = pd.DataFrame(ew).round(3)
    ew.to_csv(RESULTS / "holdout_early_warning.csv", index=False)

    pd.set_option("display.width", 220)
    print(hold.to_string(index=False))
    print(stt.to_string(index=False))
    print(ew.pivot_table(index=["region", "asof"], columns="index", values="auc_loss", sort=False))
