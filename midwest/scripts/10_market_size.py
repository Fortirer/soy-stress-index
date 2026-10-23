"""US market size, bottom-up, in US$ per year (Illinois and the Midwest).

    python midwest/scripts/10_market_size.py

Inputs are public numbers, written below with their source. The price per
acre is a hypothesis to test in interviews, not a quote.
"""
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from turgor_us import FIGURES, RESULTS  # noqa: E402

# USDA NASS, Crop Production Annual Summary (Jan 2026): 2025 soybean planted acres (millions)
ACRES = {"US": 81.215, "IL": 10.30, "IA": 9.45, "MN": 7.15, "IN": 5.45, "NE": 4.85}
PRICE = 1.00              # US$ per acre per season, risk score (hypothesis)
# Crop insurance: Champaign County, IL, 85% RP enterprise units, 2025: farmer-paid
# premium ~US$ 7.54/ac (farmdoc daily, Mar 2025); enterprise-unit subsidy at 85% = 53%
TOTAL_PREMIUM_USD_AC = 7.54 / (1 - 0.53)
LICENCE_SHARE = 0.02
IL_INSURED_SOY_ACRES = 7.68e6      # RMA Illinois State Profile 2024

SEGMENTS = [   # name, customers reachable in 5 years (IL + IA + IN), acres each, US$/ac
    ("Farm Credit associations and ag banks", 6, 300_000, PRICE),
    ("Grain co-ops and elevators", 8, 150_000, PRICE),
    ("Crop insurance agencies and AIPs (portfolio analytics)", 3, 500_000, PRICE),
]
TRIGGER_SHARE = 0.03   # share of IL insured soybean acres on a Turgor-licensed private trigger


def main():
    core = ACRES["IL"] + ACRES["IA"] + ACRES["IN"]
    rows = [("TAM", f"All US soybean, {ACRES['US']:.1f} M ac × US$ {PRICE:.2f}", ACRES["US"] * 1e6, ACRES["US"] * 1e6 * PRICE),
            ("SAM", f"IL + IA + IN soybean, {core:.1f} M ac × US$ {PRICE:.2f}", core * 1e6, core * 1e6 * PRICE)]
    som = 0
    for name, n, ac, pr in SEGMENTS:
        rows.append((f"SOM: {name}", f"{n} customers × {ac:,} ac × US$ {pr:.2f}", n * ac, n * ac * pr))
        som += n * ac * pr
    lic_ac = IL_INSURED_SOY_ACRES * TRIGGER_SHARE
    lic = lic_ac * TOTAL_PREMIUM_USD_AC * LICENCE_SHARE
    rows.append(("SOM: Trigger licence (private products)",
                 f"{TRIGGER_SHARE:.0%} of IL insured soybean acres × US$ {TOTAL_PREMIUM_USD_AC:.0f}/ac premium × {LICENCE_SHARE:.0%}",
                 lic_ac, lic))
    rows.append(("SOM total (5 years)", "sum", None, som + lic))
    df = pd.DataFrame(rows, columns=["level", "formula", "acres", "revenue_usd_year"])
    df.to_csv(RESULTS / "us_market_size.csv", index=False)
    print(df.to_string(index=False))

    fig, ax = plt.subplots(figsize=(10, 5.6), dpi=150)
    ax.axis("off")
    green, muted = "#1E5B3A", "#56695E"
    ax.text(0, 1, "Turgor US market, bottom-up (US$ per year)", fontsize=20, weight="bold", color=green, va="top")
    lines = [("TAM", f"$ {ACRES['US']*PRICE:.0f} M", f"All US soybean, {ACRES['US']:.1f} M acres × $1/acre"),
             ("SAM", f"$ {core*PRICE:.1f} M", f"Illinois + Iowa + Indiana soybean, {core:.1f} M acres × $1/acre"),
             ("SOM", f"$ {(som+lic)/1e6:.1f} M", "5-year reachable: 6 lenders × 300k ac, 8 grain co-ops × 150k ac,\n"
                                               "3 insurance portfolios × 500k ac at $1/acre\n+ a trigger licence on 3% of IL insured soybean acres")]
    y = 0.78
    for lab, val, txt in lines:
        ax.text(0, y, lab, fontsize=16, weight="bold", color=muted, va="top")
        ax.text(0.1, y, val, fontsize=26, weight="bold", color=green, va="top")
        ax.text(0.36, y - 0.01, txt, fontsize=11.5, color="#12291D", va="top")
        y -= 0.24
    ax.text(0, 0.02, "Sources: USDA NASS Crop Production 2025 Summary (Jan 2026); RMA Illinois State Profile 2024; farmdoc daily (Mar 2025).\n"
            "Price $1/acre/season is a hypothesis to test in interviews. midwest/scripts/10_market_size.py",
            fontsize=8, color=muted, va="bottom")
    fig.savefig(FIGURES / "us_market_size_slide.png", bbox_inches="tight")


if __name__ == "__main__":
    main()
