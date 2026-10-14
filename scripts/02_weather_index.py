"""Version 0 of the index: weather + crop stage (no satellite yet).

    python scripts/02_weather_index.py

Compares, with leave-one-year-out where anything is fitted:
  1. Rainfall index      - low Jan-Feb rain (what rainfall-index insurance uses)
  2. Unweighted stress   - water + heat + heat x dry, both stages weighted equally
  3. SSI (a priori)      - same, reproductive stage weighted 0.75 (physiology prior)
  4. SSI (fitted)        - component weights learned by logistic regression, LOYO
"""
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ssi.config import DROUGHT_HARVESTS, FOCUS_STATES, RESULTS, STATES  # noqa: E402
from ssi.data import load_panel  # noqa: E402
from ssi.evaluate import drought_year_table, fitted_weights_loyo, metrics  # noqa: E402
from ssi.index import rainfall_index, ssi, unweighted_index  # noqa: E402

RESULTS.mkdir(exist_ok=True)
panel = load_panel()


def evaluate(df: pd.DataFrame, label: str) -> tuple[pd.DataFrame, dict, pd.Series]:
    df = df.reset_index(drop=True)
    fitted, weights = fitted_weights_loyo(df)
    scores = {"Rainfall index": rainfall_index(df).values,
              "Unweighted stress": unweighted_index(df).values,
              "SSI a priori": ssi(df).values,
              "SSI fitted (LOYO)": fitted}
    rows = [{"region": label, "index": k, **metrics(v, df)} for k, v in scores.items()]
    return pd.DataFrame(rows), scores, weights


tables, all_weights = [], {}
for region, states in {"RS + PR": FOCUS_STATES, "RS": ["RS"], "PR": ["PR"],
                       "All 10 states": STATES}.items():
    df = panel[panel["st"].isin(states)].reset_index(drop=True)
    t, scores, w = evaluate(df, region)
    tables.append(t)
    all_weights[region] = w.round(3).to_dict()
    if region == "RS + PR":
        focus_df, focus_scores = df, scores

res = pd.concat(tables).round(3)
res.to_csv(RESULTS / "v0_weather_metrics.csv", index=False)
drought = drought_year_table(focus_df, focus_scores, DROUGHT_HARVESTS)
drought.to_csv(RESULTS / "v0_drought_years.csv", index=False)

out = focus_df[["st", "fips5", "county", "year", "area_harvested_ha", "rel_anom", "loss"]].copy()
for k, v in focus_scores.items():
    out[k] = v
out.round(4).to_csv(RESULTS / "v0_scores_rs_pr.csv.gz", index=False)
(RESULTS / "v0_fitted_weights.json").write_text(json.dumps(all_weights, indent=2))

pd.set_option("display.width", 160)
print(res.to_string(index=False))
print()
print(drought.to_string(index=False))
