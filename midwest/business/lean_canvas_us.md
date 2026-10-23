# Lean Canvas: US (version 0, October 2026)

✔ = evidence (link) · ? = hypothesis to test in interviews

| Box | Content |
| --- | --- |
| **1. Problem** | ? Lenders, crop insurers and grain buyers learn the size of a soybean shortfall from NASS reports and harvest, county by county, late. ? In-season tools show imagery but not *why* the crop is losing yield or how much. ✔ July–August rainfall already flags losses fairly well in Illinois (AUC 0.75), so the problem is not "no signal" but "weak signal and late". |
| **2. Customer segments** | ? Farm Credit associations and ag banks (in-season loan book risk); ? crop insurers and reinsurers (claims planning, private products); ? grain co-ops and merchandisers (supply). **Early adopters:** reinsurers and parametric providers that work in both Brazil and the US. |
| **3. Unique value** | ✔ One physiology-based index, validated in public on two continents (Brazil and Illinois) with confidence intervals. ✔ In Illinois: fewer missed losses than rainfall in the backtest (basis risk 0.47 vs 0.57) and a better statewide-year signal (r 0.60 vs 0.44), though not statistically proven. ✔ Catches seed-fill stress that rain misses (2003). |
| **4. Solution** | ✔ Weekly county stress map from June to October, with expected loss in $/acre. ? Field level via Sentinel-2 (built for Brazil, not yet tested in the US). ? Soybean-only mask from the yearly Cropland Data Layer. |
| **5. Channels** | ? UIUC network (farmdoc, ACES, Research Park), the hackathon, Illinois Soybean Association, Farm Bureau, Farm Credit innovation teams, reinsurer contacts from Brazil. |
| **6. Revenue** | ? $0.25–2 per acre per season, or $25–100 k per portfolio per year; ? trigger licence 1–3% of premium on private products. |
| **7. Costs** | Near zero for data (public MODIS, NASA POWER, NASS); people. A US entity, if ever needed, brings legal and visa constraints (see `founder_and_funding_us.md`). |
| **8. Key metrics** | Portfolios monitored; renewals after the first season; the public weekly record each season (basis risk vs rainfall). |
| **9. Unfair advantage** | ✔ Soybean physiology under drought, heat and CO2 (SoyFACE connection); ✔ an open two-country backtest; ? Brazilian customers and data for a global offer. |

## Main risks

1. **The US gain over rainfall is small and not proven.** Don't lead the US pitch with "better than rainfall". Lead with the two-continent track record and stress diagnosis.
2. **The market is crowded and some players have big funding** (EarthDaily, CeresAI). Gro Intelligence failed despite $85 M.
3. **Visa and ownership limits** for US work and SBIR.
