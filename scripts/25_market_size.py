"""Bottom-up market size (issue #16): one table and one slide figure.

Inputs are public numbers written below with their source. Change them here
when a newer Conab survey or an interview gives a better figure.

    python scripts/25_market_size.py
"""
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

# Conab 2025/26 survey of May 2026, via Embrapa Soja "Dados economicos" (million ha)
AREA_MHA = {"RS": 6.73, "PR": 5.74, "Brasil": 48.72}
# Price per ha per season: middle of the risk-score hypothesis (issue #12)
PRICE = 3.0
# Insurance: PR soybean 2020 had ~2.0 M ha insured and R$ 404 M premium (Revista Cultivar, Dec 2020)
PREMIUM_RS_HA = 404e6 / 2.0e6
LICENCE_SHARE = 0.02  # 1-3% of premium, middle

# Customers: who buys, how much area each one would put in a first contract (ha), how many in RS + PR
SEGMENTS = [
    # name, customers in RS+PR reachable in 5 years, ha per customer, price R$/ha
    ("Cooperativas agrícolas", 15, 50_000, PRICE),
    ("Revendas e tradings (barter/CPR)", 10, 30_000, PRICE),
    ("Bancos e cooperativas de crédito", 5, 100_000, PRICE),
]
INSURED_SHARE_RS_PR = 0.05   # share of RS+PR soybean area insured with a Turgor-licensed trigger, 5-year view


def main():
    rows = []
    tam = AREA_MHA["Brasil"] * 1e6 * PRICE
    sam = (AREA_MHA["RS"] + AREA_MHA["PR"]) * 1e6 * PRICE
    rows.append(("TAM", "Toda a soja do Brasil × R$ 3/ha", AREA_MHA["Brasil"] * 1e6, tam))
    rows.append(("SAM", "Soja do RS + PR × R$ 3/ha", (AREA_MHA["RS"] + AREA_MHA["PR"]) * 1e6, sam))
    som_ha = 0
    som = 0
    for name, n, ha, pr in SEGMENTS:
        rows.append(("SOM: " + name, f"{n} clientes × {ha:,} ha × R$ {pr:g}/ha", n * ha, n * ha * pr))
        som_ha += n * ha
        som += n * ha * pr
    lic_ha = (AREA_MHA["RS"] + AREA_MHA["PR"]) * 1e6 * INSURED_SHARE_RS_PR
    lic = lic_ha * PREMIUM_RS_HA * LICENCE_SHARE
    rows.append(("SOM: Seguradoras (licença)", f"{INSURED_SHARE_RS_PR:.0%} da área RS+PR segurada × R$ {PREMIUM_RS_HA:.0f}/ha de prêmio × {LICENCE_SHARE:.0%}", lic_ha, lic))
    rows.append(("SOM total (5 anos)", "soma dos segmentos", som_ha + lic_ha, som + lic))
    df = pd.DataFrame(rows, columns=["nivel", "formula", "hectares", "receita_rs_ano"])
    df.to_csv(ROOT / "results/market_size.csv", index=False)
    print(df.to_string(index=False))

    # one slide
    fig, ax = plt.subplots(figsize=(10, 5.6), dpi=150)
    ax.axis("off")
    green, muted = "#1E5B3A", "#56695E"
    ax.text(0, 1, "Turgor market, bottom-up (R$ per year)", fontsize=20, weight="bold", color=green, va="top")
    lines = [("TAM", f"R$ {tam/1e6:.0f} M", f"All Brazilian soybean, {AREA_MHA['Brasil']:.1f} M ha × R$ 3/ha"),
             ("SAM", f"R$ {sam/1e6:.0f} M", f"RS + PR soybean, {AREA_MHA['RS']+AREA_MHA['PR']:.1f} M ha × R$ 3/ha (where the index is validated)"),
             ("SOM", f"R$ {(som+lic)/1e6:.1f} M", "5-year reachable: 15 co-ops × 50k ha, 10 resellers × 30k ha,\n5 lenders × 100k ha at R$ 3/ha + trigger licence (2% of premium)\non 5% of RS+PR soybean area")]
    y = 0.78
    for lab, val, txt in lines:
        ax.text(0, y, lab, fontsize=16, weight="bold", color=muted, va="top")
        ax.text(0.1, y, val, fontsize=26, weight="bold", color=green, va="top")
        ax.text(0.36, y - 0.01, txt, fontsize=11.5, color="#12291D", va="top")
        y -= 0.24
    ax.text(0, 0.02, "Sources: Conab 2025/26 (May 2026) via Embrapa Soja; insured soybean PR 2020 (R$ 404 M premium on ~2 M ha, Revista Cultivar);\n"
            "price R$ 3/ha = middle of the risk-score hypothesis, to be confirmed in interviews (issue #12). scripts/25_market_size.py",
            fontsize=8, color=muted, va="bottom")
    out = ROOT / "docs/figures"
    out.mkdir(parents=True, exist_ok=True)
    fig.savefig(out / "market_size_slide.png", bbox_inches="tight")


if __name__ == "__main__":
    main()
