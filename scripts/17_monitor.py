"""Live monitor: Turgor index for the current soybean season, RS and PR.

    python scripts/17_monitor.py                     # as of today
    python scripts/17_monitor.py --asof 2025-02-15   # replay a past date

Downloads this season's MODIS NDVI (Planetary Computer) and NASA POWER daily
weather up to the as-of date, computes the real-time Turgor index on the
latest weekly anchor (1 Dec ... 15 Apr), and ranks it against the same anchor
in every past season (data/monitor_reference.csv.gz, script 16).

Writes monitor/<season>/<YYYY-MM-DD>/ and refreshes monitor/latest/:
  turgor_monitor.csv       one row per municipality
  turgor_monitor.geojson   same, with outlines, for any GIS or web map
  map.png                  stress classes
  summary.md               the 20 most stressed municipalities
and appends a line to monitor/log.csv. Every week's output is kept, so the
season becomes a timestamped track record written before harvest.
"""
import argparse
import json
import shutil
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ssi.config import DATA, RESULTS, ROOT  # noqa: E402
from ssi.data import load_boundaries  # noqa: E402
from ssi.early import WINDOWS, asof_features, turgor_index  # noqa: E402
from ssi.index import components  # noqa: E402
from ssi.monitor import (CLASS_COLORS, anchor_date, anchor_for, harvest_year_of,  # noqa: E402
                         lookup_loss_rate, own_percentile, stress_class)
from ssi.satellite import modis_season_ndvi  # noqa: E402
from ssi.weather import daily_indicators, fetch_power  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--asof", default=pd.Timestamp.today().strftime("%Y-%m-%d"))
ap.add_argument("--states", nargs="+", default=["RS", "PR"])
ap.add_argument("--out", default=str(ROOT / "monitor"))
ap.add_argument("--workers", type=int, default=8)
args = ap.parse_args()

asof = pd.Timestamp(args.asof)
anchor = anchor_for(asof)
hy = harvest_year_of(asof)
season = f"{hy - 1}-{str(hy)[2:]}"
out_root = Path(args.out)
if anchor is None:
    print(f"{asof.date()}: before 1 December, season {season} not monitored yet")
    sys.exit(0)
adate = anchor_date(anchor, hy)
print(f"season {season}, as of {asof.date()} -> anchor {adate.date()}", flush=True)

geo = load_boundaries()
feats = [f for f in geo["features"] if f["properties"]["st"] in args.states]

# ---------------------------------------------------------------- 1. this season's data
nd_parts = []
for st in args.states:
    fs = [f for f in feats if f["properties"]["st"] == st]
    print(f"MODIS {st} ...", flush=True)
    nd_parts.append(modis_season_ndvi(fs, hy, end=adate.strftime("%Y-%m-%d"), mask_fallback_year=hy - 1))
nd = pd.concat(nd_parts, ignore_index=True)
nd_by = {c: g for c, g in nd.groupby("fips5")}


def centroid(f):
    r = np.array(f["geometry"]["coordinates"][0])
    return r[:, 1].mean(), r[:, 0].mean()


def weather(f):
    lat, lon = centroid(f)
    w = fetch_power(lat, lon, f"{hy - 1}-07-01", (adate - pd.Timedelta(days=1)).strftime("%Y-%m-%d"))
    return int(f["id"]), daily_indicators(w, lat)


print("NASA POWER ...", flush=True)
with ThreadPoolExecutor(args.workers) as pool:
    wx = dict(pool.map(weather, feats))

# typical windows = median of 2001-2023 seasons
st_hist = pd.read_csv(DATA / "ndvi_stages_2001_2023.csv.gz")
off = st_hist[["fips5", "year"] + WINDOWS].copy()
for c in WINDOWS:
    off[c] = (pd.to_datetime(off[c]) - pd.to_datetime((off["year"] - 1).astype(str) + "-09-01")).dt.days
med = off.groupby("fips5")[WINDOWS].median()
typ = med.assign(year=hy).reset_index().set_index(["fips5", "year"])
fallback = med.assign(s=med.index.astype(str).str[:2]).groupby("s")[WINDOWS].median()

rows = []
for f in feats:
    code = int(f["id"])
    g = nd_by.get(code, pd.DataFrame(columns=["date", "ndvi", "harvest_year"]))
    rows += asof_features(wx[code], g, code, [hy], [anchor], typ, fallback.loc[str(code)[:2]])
cur = pd.DataFrame(rows).drop(columns="asof")

# ---------------------------------------------------------------- 2. index vs past seasons
ref = pd.read_csv(DATA / "monitor_reference.csv.gz")
ref = ref[(ref["anchor"] == anchor) & (ref["year"] != hy)].drop(columns="anchor")
allf = pd.concat([ref, cur], ignore_index=True)
is_cur = (allf["year"] == hy).values
past = ~is_cur
allf["turgor_index"] = turgor_index(allf, ref=past).values
comp = components(allf, ref=past)
allf["percentile_vs_past"] = own_percentile(allf["turgor_index"], allf["fips5"], is_cur)
now = allf[is_cur].copy()
c = comp[is_cur]
now["water_z"] = (0.25 * c["vegetative_water"] + 0.75 * c["reproductive_water"]).round(2)
now["heat_z"] = (0.25 * c["vegetative_heat"] + 0.75 * c["reproductive_heat"]).round(2)
now["canopy_z"] = (0.25 * c.get("vegetative_ndvi", 0) + 0.75 * c.get("reproductive_ndvi", 0)).round(2)
now["main_driver"] = now[["water_z", "heat_z", "canopy_z"]].idxmax(axis=1).map(
    {"water_z": "water deficit", "heat_z": "heat", "canopy_z": "weak canopy (NDVI)"})
now.loc[now[["water_z", "heat_z", "canopy_z"]].max(axis=1) <= 0.5, "main_driver"] = "-"
now["stress_class"] = now["percentile_vs_past"].map(stress_class)
lr = pd.read_csv(RESULTS / "monitor_loss_rates.csv")
now["past_loss_frequency"] = [lookup_loss_rate(lr, anchor, s) for s in now["turgor_index"]]
names = pd.read_csv(DATA / "panel.csv.gz", usecols=["fips5", "county"]).drop_duplicates("fips5") \
    .set_index("fips5")["county"].str.split(" - ").str[0].str.title().to_dict()
area = pd.read_csv(RESULTS / "municipal_scores_2001_2025.csv.gz").sort_values("year") \
    .groupby("fips5")["area_harvested_ha"].last()
now["st"] = now["fips5"].astype(str).str[:2].map({"43": "RS", "41": "PR"})
now["soy_area_ha_last"] = now["fips5"].map(area)
cols = ["st", "fips5", "turgor_index", "percentile_vs_past", "stress_class", "past_loss_frequency",
        "main_driver", "water_z", "heat_z", "canopy_z", "soy_area_ha_last"]
now = now[cols].sort_values("turgor_index", ascending=False).round(3)

# ---------------------------------------------------------------- 3. outputs
out = out_root / season / adate.strftime("%Y-%m-%d")
out.mkdir(parents=True, exist_ok=True)
now.to_csv(out / "turgor_monitor.csv", index=False)
by = now.set_index("fips5")
gj = {"type": "FeatureCollection", "properties": {"season": season, "as_of": str(adate.date())}, "features": []}
for f in feats:
    code = int(f["id"])
    props = {"fips5": code, **({k: (None if pd.isna(v) else v) for k, v in by.loc[code].items()} if code in by.index else {})}
    gj["features"].append({"type": "Feature", "properties": props, "geometry": f["geometry"]})
(out / "turgor_monitor.geojson").write_text(json.dumps(gj))

import matplotlib  # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Patch, Polygon  # noqa: E402

fig, ax = plt.subplots(figsize=(7.5, 9))
for f in feats:
    code = int(f["id"])
    cls = by.loc[code, "stress_class"] if code in by.index else "no data"
    ax.add_patch(Polygon(f["geometry"]["coordinates"][0], closed=True, fc=CLASS_COLORS[cls], ec="#8A9A90", lw=0.15))
ax.autoscale_view()
ax.set_aspect("equal")
ax.axis("off")
counts = now["stress_class"].value_counts()
ax.legend(handles=[Patch(fc=CLASS_COLORS[k], ec="#8A9A90", label=f"{k} ({counts.get(k, 0)})")
                   for k in ["severe", "high", "watch", "normal"]],
          loc="lower right", frameon=False, title="Stress vs. past seasons")
ax.set_title(f"Turgor index - soybean stress, RS and PR\nseason {season}, data up to {adate:%d %b %Y}", fontsize=11)
fig.text(0.02, 0.02, "severe = above the 95th percentile of the municipality's own 2001-2025 seasons at this date; "
         "high > 85th; watch > 70th.\nMODIS NDVI + NASA POWER, real-time latency. github.com/Fortirer/soy-stress-index",
         fontsize=6.5, color="#56695E")
fig.savefig(out / "map.png", dpi=170, bbox_inches="tight")

top = now.head(20).copy()
top["municipality"] = [names.get(c) or c for c in top["fips5"]]
lines = [f"# Turgor monitor - season {season}, data up to {adate.date()}", "",
         f"Municipalities by class: " + ", ".join(f"{k} {counts.get(k, 0)}" for k in ["severe", "high", "watch", "normal"]), "",
         "![map](map.png)", "", "## 20 most stressed municipalities", "",
         "| # | State | Municipality (IBGE) | Turgor index | Percentile vs past | Class | Past loss frequency* | Main driver |",
         "| --- | --- | --- | --- | --- | --- | --- | --- |"]
for i, r in enumerate(top.itertuples(), 1):
    lines.append(f"| {i} | {r.st} | {r.municipality} | {r.turgor_index:.2f} | {r.percentile_vs_past:.0f} | {r.stress_class} | "
                 f"{'' if pd.isna(r.past_loss_frequency) else f'{100 * r.past_loss_frequency:.0f}%'} | {r.main_driver} |")
lines += ["", "\\* Share of past municipality-seasons (2001-2025) with yield more than 10% below trend, "
          "among those with a similar index at this date. Not a forecast of this season's yield."]
(out / "summary.md").write_text("\n".join(lines) + "\n")

latest = out_root / "latest"
if latest.exists():
    shutil.rmtree(latest)
shutil.copytree(out, latest)
log = out_root / "log.csv"
entry = pd.DataFrame([{"run_date": pd.Timestamp.today().strftime("%Y-%m-%d"), "season": season,
                       "as_of": str(adate.date()), **{k: int(counts.get(k, 0)) for k in ["severe", "high", "watch", "normal"]}}])
entry.to_csv(log, mode="a", header=not log.exists(), index=False)
print(f"written {out}")
print(now.head(10).to_string(index=False))
