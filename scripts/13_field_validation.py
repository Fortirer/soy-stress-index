"""Validate the index against a partner's real field yields (co-op pilot).

    python scripts/13_field_validation.py --fields talhoes.shp --yields produtividade.xlsx
    python scripts/13_field_validation.py --check-only --fields ... --yields ...   # just check the files

fields : GeoJSON, Shapefile (.shp/.zip), KML/KMZ or GeoPackage, any CRS (ssi/coop_input.py)
yields : CSV or Excel; id_talhao/field_id, safra/harvest_year ("2021/22" ok),
         produtividade_kg_ha/yield_kg_ha or produtividade_sc_ha [, municipio_ibge/fips5]
Seasons 2018-2025 work (Sentinel-2 L2A from 2017). At least 3 seasons per field.

The field index is the product index (ssi.early.turgor_index) at field scale:
each field's own Sentinel-2 curve, its typical stage windows (median of its
other seasons), data latency, weather at the field.

Outputs (in --out, default results/field_validation/):
  verificacao_dados.txt      problems found in the input files
  field_features.csv         stages, NDVI and weather per field-season
  field_scores.csv           field index, municipal index, field rainfall index, yields, loss flags
  field_metrics.csv          AUC, basis risk and within-season ranking per index
  field_early_warning.csv    the same by date (1 Jan ... 15 Apr)
  relatorio_cooperativa.md   two-page report for the co-op (Portuguese) + figure

--demo runs the whole pipeline on 4 pilot plots with SYNTHETIC yields, only
to check that it works end to end. Demo numbers are not results.
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ssi.config import DATA, RESULTS  # noqa: E402
from ssi.fieldval import (SEASONS_MIN, field_index, field_season_features,  # noqa: E402
                          validate, yield_anomaly)
from ssi.coop_input import check, read_fields, read_yields  # noqa: E402
from ssi.early import WINDOWS, asof_features, turgor_index, typical_windows  # noqa: E402
from ssi.index import rainfall_index  # noqa: E402
from ssi.pilot import load_season  # noqa: E402
from ssi.weather import daily_indicators, fetch_power  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--fields")
ap.add_argument("--yields")
ap.add_argument("--out", default=str(RESULTS / "field_validation"))
ap.add_argument("--demo", action="store_true")
ap.add_argument("--id-col", help="field id column in the fields file, if not detected")
ap.add_argument("--check-only", action="store_true")
ap.add_argument("--name", default="cooperativa parceira", help="partner name for the report")
args = ap.parse_args()
out = Path(args.out)
cache = DATA / "field_cache"
cache.mkdir(parents=True, exist_ok=True)

if args.demo:
    out = RESULTS / "field_validation_demo"
    gj = json.loads((DATA / "pilot_fields.geojson").read_text())
    feats = []
    for f in gj["features"]:
        if f["properties"]["municipality"] == "Cruz Alta" and f["properties"]["field"] <= 4:
            f["properties"]["field_id"] = f"CA{f['properties']['field']}"
            feats.append(f)
    fields = {"type": "FeatureCollection", "features": feats}
    yields = None                      # filled in after NDVI is read (synthetic)
    years = [2021, 2022, 2023]
else:
    fields = read_fields(args.fields, args.id_col)
    yields = read_yields(args.yields)
    yields = yields[yields["harvest_year"] >= 2018].dropna(subset=["harvest_year", "yield_kg_ha"])
    years = sorted(int(y) for y in yields["harvest_year"].unique())
out.mkdir(parents=True, exist_ok=True)
if not args.demo:
    problems = check(fields, read_yields(args.yields))
    (out / "verificacao_dados.txt").write_text(
        f"{len(fields['features'])} talhoes com contorno, {yields['field_id'].nunique()} com produtividade, "
        f"safras {years}\n" + ("\n".join("- " + p for p in problems) if problems else "- nenhum problema encontrado") + "\n")
    print((out / "verificacao_dados.txt").read_text())
    if args.check_only:
        sys.exit(0)
# one polygon per field: if a field comes in several parts, keep the largest
_best = {}
for f in fields["features"]:
    ring = np.array(f["geometry"]["coordinates"][0])
    area = 0.5 * abs(np.dot(ring[:, 0], np.roll(ring[:, 1], 1)) - np.dot(ring[:, 1], np.roll(ring[:, 0], 1)))
    fid = f["properties"]["field_id"]
    if fid not in _best or area > _best[fid][0]:
        _best[fid] = (area, f)
fields["features"] = [f for _, f in _best.values()]


def field_series(feature, yr):
    """Median Sentinel-2 NDVI over the field polygon for every clear date of a season."""
    from rasterio.features import geometry_mask
    from rasterio.warp import transform_geom
    from affine import Affine
    fid = feature["properties"]["field_id"]
    fp = cache / f"{fid}_{yr}.npz"
    ring = np.array(feature["geometry"]["coordinates"][0])
    pad = 0.002
    bbox = [ring[:, 0].min() - pad, ring[:, 1].min() - pad, ring[:, 0].max() + pad, ring[:, 1].max() + pad]
    if fp.exists():
        z = np.load(fp)
        t, nd, tr = pd.to_datetime(z["times"]), z["ndvi"], Affine(*z["transform"][:6])
    else:
        t, nd, ds = load_season(bbox, yr)
        tr = ds.odc.geobox.transform
        np.savez_compressed(fp, times=t.values, ndvi=nd, transform=np.array(list(tr)[:6], dtype=float))
    geom = transform_geom("EPSG:4326", "EPSG:32722", feature["geometry"])
    inside = ~geometry_mask([geom], out_shape=nd.shape[1:], transform=tr)
    rows = []
    for i, d in enumerate(t):
        v = nd[i][inside]
        ok = np.isfinite(v)
        if inside.sum() and ok.mean() >= 0.5:
            rows.append((d.normalize(), float(np.median(v[ok]))))
    return pd.DataFrame(rows, columns=["date", "ndvi"])


def field_weather(feature):
    fid = feature["properties"]["field_id"]
    fp = cache / f"{fid}_power.csv.gz"
    ring = np.array(feature["geometry"]["coordinates"][0])
    lat, lon = ring[:, 1].mean(), ring[:, 0].mean()
    if fp.exists():
        w = pd.read_csv(fp, index_col=0, parse_dates=True)
    else:
        w = fetch_power(lat, lon, f"{min(years) - 1}-07-01", f"{max(years)}-05-31")
        w.to_csv(fp)
    return daily_indicators(w, lat)


DATES = ["01-01", "01-15", "02-01", "02-15", "03-01", "04-15"]
rows, series, inds = [], {}, {}
for f in fields["features"]:
    fid = f["properties"]["field_id"]
    inds[fid] = field_weather(f)
    for yr in years:
        s = field_series(f, yr)
        series[(fid, yr)] = s.assign(harvest_year=yr)
        feat = field_season_features(s["date"], s["ndvi"], inds[fid], yr) if len(s) >= 6 else None
        rows.append({"field_id": fid, "harvest_year": yr, "n_clear_dates": len(s), **(feat or {})})
        print(fid, yr, "ok" if feat else "no clear season", flush=True)
feat = pd.DataFrame(rows)
feat.to_csv(out / "field_features.csv", index=False)

# real-time features: each field's typical windows (median of its other seasons), data latency
st = feat.dropna(subset=["veg_start"]).rename(columns={"field_id": "fips5", "harvest_year": "year"})
typ = typical_windows(st).set_index(["fips5", "year"])
fallback = typical_windows(st)[WINDOWS].median()
med = typical_windows(st).groupby("fips5")[WINDOWS].median()
arows = []
for f in fields["features"]:
    fid = f["properties"]["field_id"]
    nd = pd.concat([series[(fid, yr)] for yr in years], ignore_index=True)
    for yr in years:
        if (fid, yr) not in typ.index:
            t = med.loc[fid] if fid in med.index else fallback
            typ.loc[(fid, yr), WINDOWS] = t.values
    arows += asof_features(inds[fid], nd, fid, years, DATES, typ, fallback)
asof = pd.DataFrame(arows).rename(columns={"fips5": "field_id", "year": "harvest_year"})

if args.demo:
    # SYNTHETIC yields: 3,600 kg/ha scaled by reproductive NDVI plus noise. Pipeline test only.
    rng = np.random.default_rng(0)
    yields = feat[["field_id", "harvest_year"]].copy()
    yields["yield_kg_ha"] = 3600 * (feat["ndvi_reproductive"].fillna(0.6) / 0.8) + rng.normal(0, 250, len(feat))
    yields["fips5"] = 4306106

y = yield_anomaly(yields.dropna(subset=["yield_kg_ha"]))
nseas = y.groupby("field_id")["harvest_year"].nunique()
y = y[y["field_id"].isin(nseas[nseas >= SEASONS_MIN].index)]


def scores_at(date):
    a = asof[asof["asof"] == date].drop(columns="asof").merge(y, on=["field_id", "harvest_year"], how="inner")
    a = a.reset_index(drop=True)
    g = a.drop(columns=["fips5"], errors="ignore").rename(columns={"field_id": "fips5"})
    a["field_index"] = turgor_index(g).values
    a["field_rainfall_index"] = rainfall_index(g).values
    return a


d = scores_at("04-15")
cols = {"Turgor field index": "field_index", "Rainfall index at the field": "field_rainfall_index"}
muni_fp = RESULTS / "municipal_scores_2001_2025.csv.gz"
if "fips5" in d.columns and d["fips5"].notna().any() and muni_fp.exists():
    m = pd.read_csv(muni_fp)[["fips5", "year", "Turgor index"]]
    m = m.rename(columns={"year": "harvest_year", "Turgor index": "municipal_index"})
    d = d.merge(m.astype({"fips5": "Int64"}), on=["fips5", "harvest_year"], how="left")
    cols["Turgor municipal index"] = "municipal_index"
d.to_csv(out / "field_scores.csv", index=False)
res = validate(d, cols).round(3)
res.to_csv(out / "field_metrics.csv", index=False)
ew = []
for dt in DATES:
    a = scores_at(dt)
    r = validate(a, {"Turgor field index": "field_index", "Rainfall index at the field": "field_rainfall_index"})
    ew.append(r.assign(asof=dt))
ew = pd.concat(ew, ignore_index=True).round(3)
ew.to_csv(out / "field_early_warning.csv", index=False)
print(res.to_string(index=False))
print(ew.to_string(index=False))

# ---------------------------------------------------------------- report for the co-op (Portuguese)
import matplotlib  # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

fig, ax = plt.subplots(1, 2, figsize=(10, 4))
for yr, g in d.groupby("harvest_year"):
    ax[0].scatter(g["field_index"], 100 * g["rel_anom"], s=18, label=str(yr))
ax[0].axhline(-10, color="#B4541A", lw=0.8, ls="--")
ax[0].set(xlabel="Indice Turgor do talhao (fim da safra)", ylabel="Produtividade vs. tendencia do talhao (%)",
          title="Estresse x produtividade, por talhao")
ax[0].legend(frameon=False, fontsize=8, title="safra")
e = ew[ew["index"] == "Turgor field index"]
lab = {"01-01": "1 jan", "01-15": "15 jan", "02-01": "1 fev", "02-15": "15 fev", "03-01": "1 mar", "04-15": "15 abr"}
ax[1].plot([lab[a] for a in e["asof"]], 100 * (1 - e["basis_risk"]), "-o", color="#1E5B3A", label="Turgor")
e = ew[ew["index"] == "Rainfall index at the field"]
ax[1].plot([lab[a] for a in e["asof"]], 100 * (1 - e["basis_risk"]), "-o", color="#2A78D6", label="Indice de chuva")
ax[1].set(ylabel="% das perdas reais encontradas", title="Quao cedo as perdas aparecem", ylim=(0, 100))
ax[1].legend(frameon=False)
for a_ in ax:
    a_.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
fig.savefig(out / "relatorio_figura.png", dpi=170)


def pct(v):
    return "" if pd.isna(v) else f"{100 * v:.0f}%"


name = {"Turgor field index": "Indice Turgor do talhao", "Rainfall index at the field": "Indice de chuva no talhao",
        "Turgor municipal index": "Indice Turgor do municipio"}
L = [f"# Piloto Turgor - {args.name}", "",
     f"{d['field_id'].nunique()} talhoes, safras {', '.join(map(str, sorted(d['harvest_year'].unique())))}, "
     f"{len(d)} talhao-safras com produtividade. Perda = produtividade mais de 10% abaixo da tendencia do proprio talhao "
     f"({pct(d['loss'].mean())} dos casos).", "",
     "## Resultado no fim da safra", "",
     "| Indice | Perdas reais encontradas* | AUC | Ordena talhoes na mesma safra (r) |", "| --- | --- | --- | --- |"]
for r in res.itertuples():
    L.append(f"| {name.get(r.index, r.index)} | {pct(1 - r.basis_risk)} | {r.auc_loss:.2f} | "
             f"{'' if pd.isna(r.within_season_rank_r) else f'{r.within_season_rank_r:.2f}'} |")
L += ["", "\\* Com o gatilho calibrado para disparar no mesmo numero de talhao-safras em que houve perda.", "",
      "## Quao cedo", "", "| Dados ate | Perdas encontradas - Turgor | Perdas encontradas - chuva |", "| --- | --- | --- |"]
for dt in DATES:
    t = ew[(ew["asof"] == dt) & (ew["index"] == "Turgor field index")]
    c = ew[(ew["asof"] == dt) & (ew["index"] == "Rainfall index at the field")]
    L.append(f"| {lab[dt]} | {pct(1 - t['basis_risk'].iloc[0]) if len(t) else ''} | "
             f"{pct(1 - c['basis_risk'].iloc[0]) if len(c) else ''} |")
L += ["", "![figura](relatorio_figura.png)", "",
      "Talhao a talhao: `field_scores.csv`. Dados usados apenas neste teste, conforme o termo assinado.", ""]
if args.demo:
    L.insert(1, "> **DEMONSTRACAO com produtividades SINTETICAS. Estes numeros nao sao resultado.**")
(out / "relatorio_cooperativa.md").write_text("\n".join(L))
if args.demo:
    print("\nDEMO: yields are synthetic. These numbers only show the pipeline runs.")
