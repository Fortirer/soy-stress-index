"""Value anchors for pricing (issue #12).

Average soybean shortfall below trend, in R$/ha at today's price, per state,
plus a stress test of annual revenue per customer at the hypothesised prices.
These are anchors for the founder, not prices: the price comes from buyers.

    python scripts/24_pricing_anchors.py --price 153.49
"""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--price", type=float, default=153.49, help="R$ per 60 kg bag (CEPEA/ESALQ PR, 28 Sep 2026)")
    ap.add_argument("--since", type=int, default=2016)
    a = ap.parse_args()

    d = pd.read_csv(ROOT / "results/expected_loss_2001_2025.csv.gz")
    p = a.price / 60
    d["revenue_trend_rs_ha"] = d.trend_kg_ha * p
    d["shortfall_rs_ha"] = np.clip(-d.rel_anom, 0, None) * d.trend_kg_ha * p
    rec = d[d.year >= a.since]

    sy = rec.groupby(["st", "year"]).shortfall_rs_ha.mean().reset_index()
    rows = []
    for st, g in rec.groupby("st"):
        y = sy[sy.st == st].shortfall_rs_ha
        rows.append(dict(st=st, seasons=f"{a.since}-{int(rec.year.max())}",
                         revenue_at_trend_rs_ha=g.revenue_trend_rs_ha.mean(),
                         mean_shortfall_rs_ha=g.shortfall_rs_ha.mean(),
                         p90_state_season_shortfall_rs_ha=y.quantile(0.9),
                         loss_rate=g.loss.mean()))
    anchors = pd.DataFrame(rows).round(2)
    for price in (1, 2, 3, 6):
        anchors[f"price_{price}_as_pct_of_mean_shortfall"] = (100 * price / anchors.mean_shortfall_rs_ha).round(2)

    stress = pd.DataFrame([dict(hectares=ha, price_rs_ha=pr, revenue_rs_year=ha * pr)
                           for ha in (20_000, 50_000, 200_000, 500_000) for pr in (1, 2, 3, 6)])

    out = ROOT / "results"
    anchors.to_csv(out / "pricing_anchors.csv", index=False)
    stress.to_csv(out / "pricing_stress_test.csv", index=False)
    print(anchors.to_string(index=False))
    print(stress.pivot(index="hectares", columns="price_rs_ha", values="revenue_rs_year").to_string())


if __name__ == "__main__":
    main()
