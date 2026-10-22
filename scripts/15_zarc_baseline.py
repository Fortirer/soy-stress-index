"""ZARC risk classes as a baseline: backtest 2001-2023 and holdout 2024-2025.

    python scripts/15_zarc_baseline.py            # downloads ZARC tables once
    python scripts/15_zarc_baseline.py --offline  # use data/zarc/ only

Needs dados.agricultura.gov.br (MAPA open data, "Tábua de risco - Zoneamento
Agrícola de Risco Climático"). Writes:
  results/zarc_scores.csv.gz        ZARC risk per municipality-season
  results/baselines_ci.csv          Turgor vs ZARC vs rainfall vs NDVI, 95% CIs
"""
import argparse
import json
import re
import sys
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ssi.config import DATA, RESULTS  # noqa: E402
from ssi.satellite import stage_table  # noqa: E402
from ssi.uncertainty import point_metrics, year_bootstrap  # noqa: E402
from ssi.zarc import load_table, risk_lookup, zarc_scores  # noqa: E402

CKAN = "https://dados.agricultura.gov.br/api/3/action/package_show?id=tabua-de-risco-zoneamento-agricola-de-risco-climatico"
ZDIR = DATA / "zarc"
ZDIR.mkdir(parents=True, exist_ok=True)

ap = argparse.ArgumentParser()
ap.add_argument("--offline", action="store_true")
ap.add_argument("--n-boot", type=int, default=1000)
args = ap.parse_args()

# ---------------------------------------------------------------- 1. download tables
if not args.offline:
    pkg = json.load(urllib.request.urlopen(CKAN, timeout=120))["result"]
    for r in pkg["resources"]:
        m = re.search(r"(\d{4})\s*/\s*(\d{4})", r.get("name", "") + " " + r.get("url", ""))
        if not m or not r["url"].lower().endswith((".csv", ".zip")):
            continue
        fp = ZDIR / f"tabua_{m.group(1)}_{m.group(2)}{Path(r['url']).suffix.lower()}"
        if not fp.exists():
            print("downloading", fp.name, flush=True)
            urllib.request.urlretrieve(r["url"], fp)

tables = {}
for fp in sorted(ZDIR.glob("tabua_*")):
    y0 = int(fp.stem.split("_")[1])
    if fp.suffix == ".zip":
        import zipfile
        with zipfile.ZipFile(fp) as z:
            name = next(n for n in z.namelist() if n.lower().endswith(".csv"))
            out = ZDIR / f"tabua_{y0}_{y0 + 1}.csv"
            if not out.exists():
                out.write_bytes(z.read(name))
        continue
    tables[y0] = load_table(fp)
    print(f"safra {y0}/{y0 + 1}: {tables[y0]['fips5'].nunique()} municipalities, "
          f"soils {sorted(tables[y0]['soil'].unique())[:8]}", flush=True)
if not tables:
    raise SystemExit("no ZARC tables in data/zarc/")
lookups = risk_lookup(tables)

# ---------------------------------------------------------------- 2. sowing dates
st_tr = pd.read_csv(DATA / "ndvi_stages_2001_2023.csv.gz")[["fips5", "year", "green_up"]]
nd = pd.concat([pd.read_csv(DATA / f"modis_ndvi_{s}.csv.gz", parse_dates=["date"]) for s in ["RS", "PR"]])
st_te = stage_table(nd[nd["harvest_year"].isin([2024, 2025])])[["fips5", "year", "green_up"]]
seasons = pd.concat([st_tr, st_te], ignore_index=True)
seasons["zarc_risk"] = zarc_scores(seasons, lookups).values
seasons.to_csv(RESULTS / "zarc_scores.csv.gz", index=False)
print(seasons["zarc_risk"].value_counts(dropna=False).sort_index())

# tiny seeded jitter breaks ties among the 4 ZARC classes, so the payout rate
# of the trigger equals the loss rate (otherwise ties inflate basis risk)
rng = np.random.default_rng(0)
jit = lambda s: s + rng.uniform(0, 1e-3, len(s))  # noqa: E731

rows = []
# ---------------------------------------------------------------- 3. backtest 2001-2023
bt = pd.read_csv(RESULTS / "v1_scores_rs_pr.csv.gz").merge(
    seasons[["fips5", "year", "zarc_risk"]], on=["fips5", "year"], how="left")
bt = bt.dropna(subset=["zarc_risk"]).reset_index(drop=True)
names = {"Turgor index": "Turgor index", "ZARC risk class": "zarc_risk",
         "Rainfall index": "Rainfall index", "NDVI only": "NDVI only"}
for region, sts in {"RS + PR": ["RS", "PR"], "RS": ["RS"], "PR": ["PR"]}.items():
    d = bt[bt["st"].isin(sts)].reset_index(drop=True)
    sc = {k: (jit(d[c].values) if c == "zarc_risk" else d[c].values) for k, c in names.items()}
    r = year_bootstrap(d, sc, n=args.n_boot, reference="ZARC risk class")
    r.insert(0, "test", "backtest 2001-2023")
    r.insert(1, "region", region)
    rows.append(r)
    print(region, "backtest done", flush=True)

# ---------------------------------------------------------------- 4. holdout 2024-2025
ho = pd.read_csv(RESULTS / "municipal_scores_2001_2025.csv.gz")
ho = ho[ho["year"].isin([2024, 2025])].merge(seasons[["fips5", "year", "zarc_risk"]],
                                              on=["fips5", "year"], how="left")
ho = ho.dropna(subset=["zarc_risk"]).reset_index(drop=True)
hnames = {"Turgor index": "Turgor index", "ZARC risk class": "zarc_risk",
          "Rainfall index": "Rainfall index", "NDVI only": "NDVI only"}
for region, sts in {"RS + PR": ["RS", "PR"], "RS": ["RS"], "PR": ["PR"]}.items():
    d = ho[ho["st"].isin(sts)].reset_index(drop=True)
    sc = {k: (jit(d[c].values) if c == "zarc_risk" else d[c].values) for k, c in hnames.items()}
    # only 2 seasons: resample municipalities instead of years (narrower, optimistic CIs)
    boot = {k: [] for k in sc}
    idx_all = np.arange(len(d))
    for _ in range(args.n_boot):
        i = rng.choice(idx_all, len(idx_all), replace=True)
        if d["loss"].values[i].min() == d["loss"].values[i].max():
            continue
        g = d.iloc[i].reset_index(drop=True)
        for k, s in sc.items():
            pm = point_metrics(g, s[i])
            boot[k].append((pm["auc_loss"], pm["basis_risk"]))
    ref = np.array(boot["ZARC risk class"])
    for k, s in sc.items():
        pm = point_metrics(d, s)
        b = np.array(boot[k])
        for j, m in enumerate(["auc_loss", "basis_risk"]):
            diff = b[:, j] - ref[:, j]
            rows.append(pd.DataFrame([{
                "test": "holdout 2024-2025", "region": region, "index": k, "metric": m,
                "estimate": pm[m], "ci_low": np.percentile(b[:, j], 2.5), "ci_high": np.percentile(b[:, j], 97.5),
                "diff_vs_ref": pm[m] - point_metrics(d, sc["ZARC risk class"])[m] if k != "ZARC risk class" else np.nan,
                "diff_ci_low": np.percentile(diff, 2.5) if k != "ZARC risk class" else np.nan,
                "diff_ci_high": np.percentile(diff, 97.5) if k != "ZARC risk class" else np.nan,
                "p_better": (np.mean(diff < 0) if m == "basis_risk" else np.mean(diff > 0)) if k != "ZARC risk class" else np.nan}]))

res = pd.concat(rows, ignore_index=True).round(3)
res.to_csv(RESULTS / "baselines_ci.csv", index=False)
pd.set_option("display.width", 220)
show = res[res["metric"].isin(["auc_loss", "basis_risk"])]
print(show[["test", "region", "index", "metric", "estimate", "ci_low", "ci_high", "diff_vs_ref", "p_better"]].to_string(index=False))
