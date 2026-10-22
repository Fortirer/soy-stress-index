"""Rio Grande do Sul: can the Turgor index clearly beat a rainfall index?

    python scripts/19_rs_experiments.py --variants base vpd modis250 ...

Each variant changes one thing and is scored exactly like the product index
(end of season, typical windows, data latency, physiology weights):

  base       current Turgor index (MODIS ~1 km, NASA POWER weather)
  vpd        + vapour-pressure deficit by stage (0.5 weight, like heat)
  modis250   MODIS read at full 250 m
  soymask    MODIS pixels limited to MapBiomas soybean      (data/mapbiomas, script 20)
  chirps     CHIRPS daily rain in the water balance          (data/chirps, script 21)
  best       combination of the variants that helped

Backtest 2001-2023: AUC and basis risk with 95% CIs from 1,000 resampled
harvest years, as differences against the rainfall index. Holdout 2024-2025:
point values. Writes results/rs_experiments.csv.
"""
import argparse
import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ssi.config import DATA, RESULTS  # noqa: E402
from ssi.data import load_boundaries  # noqa: E402
from ssi.early import END_OF_SEASON, WINDOWS, asof_features, turgor_index, typical_windows  # noqa: E402
from ssi.index import local_z  # noqa: E402
from ssi.satellite import stage_table  # noqa: E402
from ssi.uncertainty import point_metrics, year_bootstrap  # noqa: E402
from ssi.weather import daily_indicators  # noqa: E402

YEARS = list(range(2001, 2026))
OUT = DATA / "rs_experiments"
OUT.mkdir(exist_ok=True)
VARIANT_INPUTS = {  # (ndvi series file, rain source)
    "base": ("modis_ndvi_RS.csv.gz", "power"),
    "vpd": ("modis_ndvi_RS.csv.gz", "power"),
    "modis250": ("modis_ndvi_RS_250m.csv.gz", "power"),
    "soymask": ("modis_ndvi_RS_soy.csv.gz", "power"),
    "chirps": ("modis_ndvi_RS.csv.gz", "chirps"),
}
feats = [f for f in load_boundaries()["features"] if f["properties"]["st"] == "RS"]


def typical(series: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    st = stage_table(series[series["harvest_year"] <= 2023])
    loyo = typical_windows(st)
    off = st[["fips5", "year"] + WINDOWS].copy()
    for c in WINDOWS:
        off[c] = (pd.to_datetime(off[c]) - pd.to_datetime((off["year"] - 1).astype(str) + "-09-01")).dt.days
    med = off.groupby("fips5")[WINDOWS].median().reset_index()
    typ = pd.concat([loyo] + [med.assign(year=y) for y in (2024, 2025)]).set_index(["fips5", "year"])
    fb = loyo[WINDOWS].median()
    return typ, fb


def weather(code: int, lat: float, rain: str) -> pd.DataFrame:
    parts = [pd.read_csv(DATA / d / f"{code}.csv.gz", index_col=0, parse_dates=True)
             for d in ("power", "power_ext") if (DATA / d / f"{code}.csv.gz").exists()]
    w = pd.concat(parts)
    w = w[~w.index.duplicated()].sort_index()
    if rain == "chirps":
        ch = pd.read_csv(DATA / "chirps" / "chirps_rs_daily.csv.gz", index_col=0, parse_dates=True)
        if str(code) in ch.columns:
            w["PRECTOTCORR"] = ch[str(code)].reindex(w.index)
    return daily_indicators(w, lat)


def _one(args):
    f, rain, typ, fb, nd_by = args
    code = int(f["id"])
    lat = float(np.array(f["geometry"]["coordinates"][0])[:, 1].mean())
    g = nd_by.get(code, pd.DataFrame(columns=["date", "ndvi", "harvest_year"]))
    return asof_features(weather(code, lat, rain), g, code, YEARS, [END_OF_SEASON], typ, fb)


def features(variant: str) -> pd.DataFrame:
    ndfile, rain = VARIANT_INPUTS[variant]
    key = f"{Path(ndfile).name.split('.')[0]}_{rain}"
    fp = OUT / f"features_{key}.csv.gz"
    if fp.exists():
        return pd.read_csv(fp)
    nd = pd.read_csv(DATA / ndfile, parse_dates=["date"])
    typ, fb = typical(nd)
    nd_by = {c: g for c, g in nd.groupby("fips5")}
    with Pool(4) as p:
        rows = [r for rs in p.imap_unordered(_one, [(f, rain, typ, fb, nd_by) for f in feats], chunksize=8) for r in rs]
    df = pd.DataFrame(rows).drop(columns="asof")
    df.round(4).to_csv(fp, index=False)
    return df


def score(variant: str, f: pd.DataFrame, extra_vpd: bool) -> np.ndarray:
    ref = (f["year"] <= 2023).values
    s = turgor_index(f, ref=ref)
    if extra_vpd:
        zv = 0.25 * local_z(f, "veg_vpd_sum", ref=ref).fillna(0) + 0.75 * local_z(f, "win_vpd_sum", ref=ref).fillna(0)
        s = s + 0.5 * zv
    return s.values


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--variants", nargs="+", default=["base", "vpd", "modis250"])
    ap.add_argument("--combine", nargs="*", default=[], help="variants to combine into 'best'")
    args = ap.parse_args()

    v1 = pd.read_csv(RESULTS / "v1_scores_rs_pr.csv.gz")
    bt_base = v1[v1["st"] == "RS"][["st", "fips5", "year", "area_harvested_ha", "rel_anom", "loss", "Rainfall index"]]
    ms = pd.read_csv(RESULTS / "municipal_scores_2001_2025.csv.gz")
    ho_base = ms[(ms["st"] == "RS") & ms["year"].isin([2024, 2025])][
        ["st", "fips5", "year", "area_harvested_ha", "rel_anom", "loss", "Rainfall index"]]

    scores = {}
    for v in args.variants:
        if v not in VARIANT_INPUTS or not (DATA / VARIANT_INPUTS[v][0]).exists():
            print(f"skip {v}: input missing", flush=True)
            continue
        f = features(v)
        scores[v] = f[["fips5", "year"]].assign(s=score(v, f, extra_vpd=(v == "vpd")))
        print(v, "scored", flush=True)
    if args.combine:   # 'best': NDVI from the first listed NDVI variant, rain from chirps if listed, + vpd if listed
        nd_v = next((v for v in args.combine if v in ("modis250", "soymask")), "base")
        rain = "chirps" if "chirps" in args.combine else "power"
        VARIANT_INPUTS["best"] = (VARIANT_INPUTS[nd_v][0], rain)
        f = features("best")
        scores["best"] = f[["fips5", "year"]].assign(s=score("best", f, extra_vpd=("vpd" in args.combine)))

    rows = []
    bt = bt_base.copy()
    for v, s in scores.items():
        bt = bt.merge(s.rename(columns={"s": v}), on=["fips5", "year"], how="left")
    bt = bt.dropna().reset_index(drop=True)
    res = year_bootstrap(bt, {k: bt[k].values for k in ["Rainfall index", *scores]}, n=1000, reference="Rainfall index")
    res.insert(0, "test", "backtest 2001-2023 (RS)")
    rows.append(res)
    ho = ho_base.copy()
    for v, s in scores.items():
        ho = ho.merge(s.rename(columns={"s": v}), on=["fips5", "year"], how="left")
    ho = ho.dropna().reset_index(drop=True)
    for k in ["Rainfall index", *scores]:
        pm = point_metrics(ho, ho[k].values)
        rows.append(pd.DataFrame([{"test": "holdout 2024-2025 (RS)", "index": k, "metric": m, "estimate": pm[m]}
                                  for m in ("auc_loss", "basis_risk")]))
    out = pd.concat(rows, ignore_index=True).round(3)
    prev = RESULTS / "rs_experiments.csv"
    if prev.exists():   # keep earlier variants' rows
        old = pd.read_csv(prev)
        out = pd.concat([old[~old["index"].isin(out["index"])], out], ignore_index=True)
    out.to_csv(prev, index=False)
    pd.set_option("display.width", 220)
    print(out[out["metric"].isin(["auc_loss", "basis_risk"])].to_string(index=False))
