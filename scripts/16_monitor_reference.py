"""Reference for the live monitor: as-of features on every weekly anchor, 2001-2025.

    python scripts/16_monitor_reference.py

Needs the cached daily weather (data/power, data/power_ext: scripts 05 and 09)
and MODIS series (data/modis_ndvi_*.csv.gz). Run once; the monitor (script 17)
then only downloads the current season. Writes:
  data/monitor_reference.csv.gz     as-of features, municipality x season x anchor
  results/monitor_loss_rates.csv    past loss frequency by index decile, per anchor
"""
import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ssi.config import DATA, RESULTS  # noqa: E402
from ssi.data import load_boundaries  # noqa: E402
from ssi.early import WINDOWS, asof_features, turgor_index, typical_windows  # noqa: E402
from ssi.monitor import ANCHORS, loss_rate_table  # noqa: E402
from ssi.weather import daily_indicators  # noqa: E402

YEARS = list(range(2001, 2026))
st = pd.read_csv(DATA / "ndvi_stages_2001_2023.csv.gz")
loyo = typical_windows(st)                                   # 2001-2023, leave-one-season-out
off = st[["fips5", "year"] + WINDOWS].copy()
for c in WINDOWS:
    off[c] = (pd.to_datetime(off[c]) - pd.to_datetime((off["year"] - 1).astype(str) + "-09-01")).dt.days
med = off.groupby("fips5")[WINDOWS].median().reset_index()
typ = pd.concat([loyo] + [med.assign(year=y) for y in (2024, 2025)]).set_index(["fips5", "year"])
fallback = loyo.assign(s=lambda d: d.fips5.astype(str).str[:2]).groupby("s")[WINDOWS].median()
nd = pd.concat([pd.read_csv(DATA / f"modis_ndvi_{s}.csv.gz", parse_dates=["date"]) for s in ["RS", "PR"]])
nd_by = {c: g for c, g in nd.groupby("fips5")}
feats = [f for f in load_boundaries()["features"] if f["properties"]["st"] in ("RS", "PR")]


def one(f):
    code = int(f["id"])
    lat = float(np.array(f["geometry"]["coordinates"][0])[:, 1].mean())
    parts = [pd.read_csv(DATA / d / f"{code}.csv.gz", index_col=0, parse_dates=True)
             for d in ("power", "power_ext") if (DATA / d / f"{code}.csv.gz").exists()]
    w = pd.concat(parts)
    ind = daily_indicators(w[~w.index.duplicated()].sort_index(), lat)
    g = nd_by.get(code, pd.DataFrame(columns=["date", "ndvi", "harvest_year"]))
    return asof_features(ind, g, code, YEARS, ANCHORS, typ, fallback.loc[str(code)[:2]])


if __name__ == "__main__":
    with Pool(4) as p:
        rows = [r for rs in p.imap_unordered(one, feats, chunksize=8) for r in rs]
    ref = pd.DataFrame(rows).rename(columns={"asof": "anchor"})
    ref.round(3).to_csv(DATA / "monitor_reference.csv.gz", index=False)
    # loss frequency by index level, per anchor (index z-scores against all past seasons)
    y = pd.read_csv(RESULTS / "municipal_scores_2001_2025.csv.gz")[["fips5", "year", "loss"]]
    parts = []
    for a, g in ref.groupby("anchor"):
        g = g.reset_index(drop=True)
        parts.append(g[["fips5", "year"]].assign(anchor=a, score=turgor_index(g).values))
    sc = pd.concat(parts).merge(y, on=["fips5", "year"], how="left")
    loss_rate_table(sc).round(4).to_csv(RESULTS / "monitor_loss_rates.csv", index=False)
    print(f"reference: {len(ref):,} rows; loss-rate table written")
