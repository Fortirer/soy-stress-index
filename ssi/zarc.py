"""ZARC (Zoneamento Agrícola de Risco Climático) as a baseline.

ZARC is the official MAPA/Embrapa zoning that lenders and insurers use today:
for each municipality, soil water class, cultivar cycle and 10-day sowing
window (decêndio), it gives the climatic risk class (20, 30 or 40% chance of
a failed crop); windows not listed are "not indicated" (risk above 40%).
It is required for subsidised rural credit (Proagro) and insurance (PSR).

Baseline score per municipality-season (higher = riskier):
  - sowing date = NDVI green-up date minus SOWING_LAG_D days
  - soil class AD2 by default (DEFAULT_SOIL), lowest-risk cycle available
    (the choice a farmer following ZARC would make)
  - risk of that sowing window from the ZARC table of that safra, or the
    nearest safra available; not indicated = NOT_INDICATED_RISK

ZARC is static and pre-season: it knows where and when it is risky to sow,
not how this season is going. It is "what the market uses today".
"""
from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd

SOWING_LAG_D = 20
DEFAULT_SOIL = "AD2"
NOT_INDICATED_RISK = 50.0


def decendio(date) -> int:
    """1..36: 1 = 1-10 Jan, 2 = 11-20 Jan, 3 = 21-31 Jan, ..."""
    d = pd.Timestamp(date)
    return (d.month - 1) * 3 + min((d.day - 1) // 10, 2) + 1


def _norm(c: str) -> str:
    return re.sub(r"[^a-z0-9]", "", c.lower())


def load_table(fp: Path) -> pd.DataFrame:
    """Read one MAPA 'tábua de risco' CSV and keep soybean rows in RS and PR.
    Returns long format: fips5, soil, cycle, dec (1-36), risk."""
    raw = None
    for sep in [";", ","]:
        for enc in ["utf-8", "latin-1"]:
            try:
                t = pd.read_csv(fp, sep=sep, encoding=enc, low_memory=False)
                if t.shape[1] > 20:
                    raw = t
                    break
            except Exception:
                continue
        if raw is not None:
            break
    if raw is None:
        raise ValueError(f"cannot parse {fp}")
    cols = {_norm(c): c for c in raw.columns}

    def col(*names):
        for n in names:
            if n in cols:
                return cols[n]
        for k, c in cols.items():
            if any(n in k for n in names):
                return c
        raise KeyError(names)

    cult = col("nomecultura", "cultura")
    raw = raw[raw[cult].astype(str).str.lower().str.contains("soja")]
    raw = raw[~raw[cult].astype(str).str.lower().str.contains("irrig")]
    geo = col("geocodigo", "codigoibge", "codmunicipio")
    uf = col("uf")
    raw = raw[raw[uf].astype(str).str.upper().isin(["RS", "PR"])]
    soil = col("codsolo", "solo")
    cyc = col("codciclo", "ciclo", "grupo")
    dec_cols = [c for c in raw.columns if re.fullmatch(r"dec\D*0?(\d{1,2})", _norm(c))]
    if len(dec_cols) < 36:
        raise ValueError(f"expected 36 decêndio columns in {fp.name}, got {len(dec_cols)}")
    long = raw.melt(id_vars=[geo, soil, cyc], value_vars=dec_cols, var_name="dec", value_name="risk")
    long["dec"] = long["dec"].map(lambda c: int(re.findall(r"(\d{1,2})$", _norm(c))[0]))
    long["risk"] = pd.to_numeric(long["risk"], errors="coerce")
    long.loc[~long["risk"].isin([20, 30, 40]), "risk"] = NOT_INDICATED_RISK
    long = long.rename(columns={geo: "fips5", soil: "soil", cyc: "cycle"})
    long["fips5"] = pd.to_numeric(long["fips5"], errors="coerce").astype("Int64")
    long["soil"] = long["soil"].astype(str).str.upper().str.replace(" ", "")
    return long.dropna(subset=["fips5"])


def soil_label(s: str) -> str:
    """MAPA soil codes: 1-3 = soil types 1-3 (tables up to 2022/23);
    11-16 = water-availability classes AD1-AD6 (from 2023/24). 'AD2' kept as is."""
    txt = str(s).upper().replace(" ", "")
    if txt.startswith("AD"):
        return txt
    m = re.search(r"(\d+)", txt)
    if not m:
        return txt
    n = int(m.group(1))
    if 11 <= n <= 16:
        return f"AD{n - 10}"
    if 1 <= n <= 3:
        return f"TIPO{n}"
    return txt


def risk_lookup(tables: dict[int, pd.DataFrame], soil: str = DEFAULT_SOIL) -> dict:
    """{safra_start_year: Series indexed by (fips5, dec) -> lowest risk across cycles}."""
    out = {}
    for yr, t in tables.items():
        t = t.assign(soil=t["soil"].map(soil_label))
        s = t[t["soil"] == soil]
        if s.empty:   # tables before 2023/24 use soil types 1-3; type 2 = medium texture
            s = t[t["soil"] == "TIPO2"]
        out[yr] = s.groupby(["fips5", "dec"])["risk"].min()
    return out


def zarc_scores(seasons: pd.DataFrame, lookups: dict) -> pd.Series:
    """seasons: fips5, year (harvest), green_up. Returns ZARC risk (%) per row."""
    years = np.array(sorted(lookups))
    res = []
    for code, harv, gu in seasons[["fips5", "year", "green_up"]].itertuples(index=False):
        if pd.isna(gu):
            res.append(np.nan)
            continue
        safra = harv - 1
        y = years[np.argmin(np.abs(years - safra))]
        dec = decendio(pd.Timestamp(gu) - pd.Timedelta(days=SOWING_LAG_D))
        res.append(lookups[y].get((code, dec), NOT_INDICATED_RISK))
    return pd.Series(res, index=seasons.index, dtype=float)
