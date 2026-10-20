"""How early does the index warn? Skill on each date of the season.

    python scripts/11_early_warning.py

For harvests 2001-2023 in RS and PR, rebuilds the index as it would have
looked on 1 Dec, 15 Dec, ..., 15 Apr, using only data available by then
(see ssi/early.py), and scores it against the final IBGE yield loss.
Writes data/asof_features.csv.gz and results/early_warning.csv.
"""
import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ssi.config import DATA, RESULTS  # noqa: E402
from ssi.data import load_boundaries  # noqa: E402
from ssi.early import asof_features, typical_windows, WINDOWS  # noqa: E402
from ssi.index import rainfall_index, ssi  # noqa: E402
from ssi.uncertainty import point_metrics  # noqa: E402
from ssi.weather import daily_indicators  # noqa: E402

DATES = ["12-01", "12-15", "01-01", "01-15", "02-01", "02-15", "03-01", "03-15", "04-01", "04-15"]
YEARS = range(2001, 2024)

stages = pd.read_csv(DATA / "ndvi_stages_2001_2023.csv.gz")
typ = typical_windows(stages).set_index(["fips5", "year"])
fallback_by_state = typical_windows(stages).assign(st=lambda d: d.fips5.astype(str).str[:2]) \
    .groupby("st")[WINDOWS].median()
ndvi = pd.concat([pd.read_csv(DATA / f"modis_ndvi_{s}.csv.gz", parse_dates=["date"]) for s in ["RS", "PR"]])
ndvi = ndvi[ndvi["harvest_year"] <= 2023]
nd_by_code = {c: g for c, g in ndvi.groupby("fips5")}
feats = [f for f in load_boundaries()["features"] if f["properties"]["st"] in ("RS", "PR")]


def one(f):
    code = int(f["id"])
    lat = float(np.array(f["geometry"]["coordinates"][0])[:, 1].mean())
    w = pd.read_csv(DATA / "power" / f"{code}.csv.gz", index_col=0, parse_dates=True)
    ind = daily_indicators(w, lat)
    nd = nd_by_code.get(code, pd.DataFrame(columns=["date", "ndvi", "harvest_year"]))
    fb = fallback_by_state.loc[str(code)[:2]]
    return asof_features(ind, nd, code, YEARS, DATES, typ, fb)


if __name__ == "__main__":
    with Pool(8) as p:
        rows = [r for rs in p.imap_unordered(one, feats, chunksize=8) for r in rs]
    feat = pd.DataFrame(rows)
    feat.to_csv(DATA / "asof_features.csv.gz", index=False)

    sc = pd.read_csv(RESULTS / "v1_scores_rs_pr.csv.gz")
    base = sc[["st", "fips5", "year", "area_harvested_ha", "rel_anom", "loss", "SSI v1 full (+ NDVI)"]]
    out = []
    for d in DATES:
        f = base.merge(feat[feat["asof"] == d], on=["fips5", "year"], how="inner").reset_index(drop=True)
        f["early_ssi"] = ssi(f).values
        f["early_ssi_weather"] = ssi(f.drop(columns=["ndvi_vegetative", "ndvi_reproductive"])).values
        f["early_rain"] = rainfall_index(f).values
        for region, states in {"RS + PR": ["RS", "PR"], "RS": ["RS"], "PR": ["PR"]}.items():
            g = f[f["st"].isin(states)].reset_index(drop=True)
            for name, col in [("Turgor index (as of date)", "early_ssi"),
                              ("Turgor weather only (as of date)", "early_ssi_weather"),
                              ("Rainfall index (as of date)", "early_rain")]:
                out.append({"asof": d, "region": region, "index": name, "n": len(g),
                            **point_metrics(g, g[col].values)})
    res = pd.DataFrame(out).round(3)
    # end-of-season reference with the real satellite windows (script 06)
    for region, states in {"RS + PR": ["RS", "PR"], "RS": ["RS"], "PR": ["PR"]}.items():
        g = base[base["st"].isin(states)].reset_index(drop=True)
        res = pd.concat([res, pd.DataFrame([{"asof": "end", "region": region,
                                              "index": "Turgor index (full season)", "n": len(g),
                                              **point_metrics(g, g["SSI v1 full (+ NDVI)"].values)}])])
    res.round(3).to_csv(RESULTS / "early_warning.csv", index=False)
    pd.set_option("display.width", 200)
    print(res.pivot_table(index=["region", "asof"], columns="index", values="auc_loss", sort=False).round(3))
