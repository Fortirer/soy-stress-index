"""Read a co-op's field and yield files as they come (issue #9).

Fields: GeoJSON, Shapefile (.shp or zipped), KML/KMZ or GeoPackage, any
coordinate system (CAR polygons often come in SIRGAS 2000 / UTM). Converted
to WGS84; multipart fields keep their largest part.

Yields: CSV (comma or semicolon) or Excel, with Portuguese or English column
names, as asked in docs/pilot_data_request_pt.md:
  id_talhao | field_id                  field identifier
  safra | harvest_year                  2022, "2021/22" or "2021/2022" -> harvest 2022
  produtividade_kg_ha | yield_kg_ha     or produtividade_sc_ha (60 kg bags)
  municipio_ibge | fips5                optional, IBGE code
check() lists problems in plain Portuguese before anything is downloaded.
"""
from __future__ import annotations

import re
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd

ID_COLS = ["field_id", "id_talhao", "talhao", "id", "codigo", "cod_talhao", "name", "nome", "cod_imovel"]
YEAR_COLS = ["harvest_year", "safra", "ano", "ano_colheita"]
KG_COLS = ["yield_kg_ha", "produtividade_kg_ha", "produtividade", "kg_ha", "rendimento_kg_ha"]
BAG_COLS = ["produtividade_sc_ha", "sc_ha", "sacas_ha", "yield_bags_ha"]
MUN_COLS = ["fips5", "municipio_ibge", "cod_ibge", "codigo_ibge", "ibge"]


def _norm(c: str) -> str:
    c = unicodedata.normalize("NFKD", str(c)).encode("ascii", "ignore").decode().lower().strip()
    return re.sub(r"[^a-z0-9]+", "_", c).strip("_")


def _pick(cols: dict, names: list[str]):
    for n in names:
        if n in cols:
            return cols[n]
    return None


def harvest_year(v) -> int | float:
    """2022 -> 2022; '2021/22' or '2021/2022' or '2021-22' -> 2022."""
    s = str(v).strip()
    m = re.fullmatch(r"(\d{4})\s*[/-]\s*(\d{2,4})", s)
    if m:
        y0, y1 = int(m.group(1)), m.group(2)
        return int(y1) if len(y1) == 4 else (y0 // 100) * 100 + int(y1) + (100 if int(y1) < y0 % 100 else 0)
    try:
        return int(float(s))
    except ValueError:
        return np.nan


def read_fields(path: str | Path, id_col: str | None = None) -> dict:
    """GeoJSON FeatureCollection in WGS84, one Polygon per field, property field_id."""
    import geopandas as gpd
    p = Path(path)
    src = f"zip://{p}" if p.suffix.lower() == ".zip" else str(p)
    if p.suffix.lower() == ".kmz":
        src = f"/vsizip/{p}/doc.kml"
    g = gpd.read_file(src)
    if g.crs is None:
        g = g.set_crs("EPSG:4326")
    g = g.to_crs("EPSG:4326")
    cols = {_norm(c): c for c in g.columns if c != "geometry"}
    col = id_col or _pick(cols, ID_COLS)
    if col is None:
        raise ValueError(f"Nao achei a coluna de identificacao do talhao. Colunas: {list(g.columns)}")
    feats = []
    for fid, geom in zip(g[col].astype(str), g.geometry):
        if geom is None or geom.is_empty:
            continue
        if geom.geom_type == "MultiPolygon":
            geom = max(geom.geoms, key=lambda x: x.area)
        if geom.geom_type != "Polygon":
            continue
        feats.append({"type": "Feature", "properties": {"field_id": fid},
                      "geometry": {"type": "Polygon", "coordinates": [list(map(list, geom.exterior.coords))]}})
    return {"type": "FeatureCollection", "features": feats}


def read_yields(path: str | Path) -> pd.DataFrame:
    p = Path(path)
    if p.suffix.lower() in (".xlsx", ".xls"):
        y = pd.read_excel(p)
    else:
        y = pd.read_csv(p, sep=None, engine="python", decimal=",") if ";" in p.read_text(errors="ignore")[:2000] \
            else pd.read_csv(p)
    cols = {_norm(c): c for c in y.columns}
    fid, yr = _pick(cols, ID_COLS), _pick(cols, YEAR_COLS)
    kg, bags, mun = _pick(cols, KG_COLS), _pick(cols, BAG_COLS), _pick(cols, MUN_COLS)
    if fid is None or yr is None or (kg is None and bags is None):
        raise ValueError("A planilha precisa de id_talhao, safra e produtividade_kg_ha (ou produtividade_sc_ha). "
                         f"Colunas encontradas: {list(y.columns)}")
    out = pd.DataFrame({"field_id": y[fid].astype(str), "harvest_year": y[yr].map(harvest_year)})
    out["yield_kg_ha"] = pd.to_numeric(y[kg], errors="coerce") if kg else pd.to_numeric(y[bags], errors="coerce") * 60
    if mun:
        out["fips5"] = pd.to_numeric(y[mun], errors="coerce").astype("Int64")
    return out


def check(fields: dict, yields: pd.DataFrame) -> list[str]:
    """Problems that would weaken the test, in plain Portuguese."""
    msgs = []
    ids = {f["properties"]["field_id"] for f in fields["features"]}
    yid = set(yields["field_id"])
    if missing := sorted(yid - ids)[:10]:
        msgs.append(f"{len(yid - ids)} talhoes com produtividade mas sem contorno (ex.: {missing})")
    if no_y := sorted(ids - yid)[:10]:
        msgs.append(f"{len(ids - yid)} talhoes com contorno mas sem produtividade (ex.: {no_y})")
    bad_year = yields["harvest_year"].isna().sum()
    if bad_year:
        msgs.append(f"{bad_year} linhas com safra ilegivel")
    old = (yields["harvest_year"] < 2018).sum()
    if old:
        msgs.append(f"{old} linhas antes da safra 2017/18: o Sentinel-2 comeca em 2017, essas ficam de fora")
    out = yields[(yields["yield_kg_ha"] < 300) | (yields["yield_kg_ha"] > 7500)]
    if len(out):
        msgs.append(f"{len(out)} produtividades fora de 300-7500 kg/ha (unidade errada? sacas em vez de kg?)")
    n = yields.dropna().groupby("field_id")["harvest_year"].nunique()
    few = (n < 3).sum()
    if few:
        msgs.append(f"{few} de {len(n)} talhoes com menos de 3 safras: ficam de fora da comparacao por talhao")
    for f in fields["features"]:
        r = np.array(f["geometry"]["coordinates"][0])
        if not (-35 < r[:, 1].mean() < 0 and -60 < r[:, 0].mean() < -35):
            msgs.append("ha talhoes fora do Brasil: confira o sistema de coordenadas do arquivo")
            break
    return msgs
