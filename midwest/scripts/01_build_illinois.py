"""Illinois county panel and county outlines.

    python midwest/scripts/01_build_illinois.py

Yields: USDA NASS county soybean yields (bu/ac) and harvested acres, 1980-2025,
as compiled in the Modelling-soybean repository (github.com/Fortirer/-Modelling-soybean),
together with its monthly weather, Palmer drought indices and crop-model stage dates.

Trend: per county, a Theil-Sen line fitted on 1990-2023 only (so the 2024-2025
holdout never informs it), extrapolated to every year. Loss = yield more than
10% below that trend. Writes midwest/data/il_panel.csv.gz and il_counties.geojson.
"""
import json
import sys
from pathlib import Path

import pandas as pd
from scipy.stats import theilslopes

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from turgor_us import DATA  # noqa: E402

SRC = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/home/claude/soystress-mvp/data")

p = pd.read_csv(SRC / "us_panel.csv.gz")
p = p[p["st"] == "IL"].copy()
rows = []
for code, g in p.groupby("fips5"):
    tr = g[g["year"].between(1990, 2023)]
    if len(tr) < 15:
        continue
    slope, icpt, *_ = theilslopes(tr["yield_bu_ac"], tr["year"])
    rows.append(g.assign(yield_trend=icpt + slope * g["year"]))
p = pd.concat(rows)
p["rel_anom"] = p["yield_bu_ac"] / p["yield_trend"] - 1
p["loss"] = (p["rel_anom"] < -0.10).astype(int)
p["area_harvested_ha"] = p["acres_harvested"] * 0.404686     # the evaluation code weights by this
keep = ["st", "county", "fips5", "year", "acres_harvested", "area_harvested_ha", "yield_bu_ac",
        "yield_trend", "rel_anom", "loss", "pcp07", "pcp08", "pdsi07", "pdsi08", "zndx08",
        "plant_doy", "r1_doy", "r3_doy", "r6_doy"]
p[keep].round(4).to_csv(DATA / "il_panel.csv.gz", index=False)

g = json.load(open(SRC / "us_counties.geojson"))
il = {"type": "FeatureCollection", "features": [f for f in g["features"] if f["properties"]["st"] == "IL"]}
(DATA / "il_counties.geojson").write_text(json.dumps(il))
print(f"{p.fips5.nunique()} counties, {len(p):,} county-years, {p.year.min()}-{p.year.max()}; "
      f"loss rate 2001-2023 {p[p.year.between(2001, 2023)]['loss'].mean():.2f}")
print(p[p.year >= 2001].groupby("year")["rel_anom"].mean().round(3).to_string())
