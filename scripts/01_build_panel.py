"""Build the municipal panel and boundaries from Modelling-soybean.

    git clone --depth 1 https://github.com/Fortirer/-Modelling-soybean.git ../Modelling-soybean
    python scripts/01_build_panel.py ../Modelling-soybean
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ssi.config import DATA  # noqa: E402
from ssi.data import build_boundaries, build_panel  # noqa: E402

src = sys.argv[1] if len(sys.argv) > 1 else "../Modelling-soybean"
DATA.mkdir(exist_ok=True)
panel = build_panel(src)
panel.round(4).to_csv(DATA / "panel.csv.gz", index=False)
(DATA / "municipalities.geojson").write_text(json.dumps(build_boundaries(src)))
print(f"{len(panel):,} municipality-harvests, {panel.fips5.nunique()} municipalities, "
      f"harvests {panel.year.min()}-{panel.year.max()}")
print(panel.groupby("st").size().to_string())
