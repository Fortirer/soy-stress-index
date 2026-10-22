# Turgor — what we're building and who we need (issue #18)

*One page to share at the hackathon, at MaRS Climate Impact, on LinkedIn and in USP / ESALQ / INPE networks.*

## What we're building

**Turgor tells soybean lenders, co-ops and insurers which fields are losing yield to drought and heat, weeks before harvest, using satellites and weather data only.**

- **The problem.** Brazilian soybean losses below trend average R$ 700–1,200 per ha a year in Paraná and Rio Grande do Sul, at today's prices. Co-ops, input resellers and banks finance that crop and find out how bad the season was at harvest, through field inspections. Parametric insurance triggers based on rainfall miss many real losses (basis risk).
- **The product.** A stage-weighted stress index built on crop physiology. Heat and water deficit count three times more during flowering and seed fill. It runs every week, per municipality and per field (Sentinel-2), and converts stress into expected loss in R$ per ha.
- **The evidence (public, reproducible).** Backtest 2001–2023 on 780 municipalities: AUC 0.86 vs 0.78 for a rainfall index, and basis risk 0.33 vs 0.44. On the new seasons 2024–25 it missed 28% fewer real losses than rainfall. By 15 January it already matches what a rainfall index only knows at season end, 8–12 weeks before harvest. Code and report: github.com/Fortirer/soy-stress-index.
- **Business.** B2B, priced per hectare per season (hypothesis R$ 2–6/ha) plus licences for insurance triggers. We are now running customer interviews in RS and PR, and the live monitor goes online on 2 December 2026.

## Founder

**Janaina Fortirer.** Plant ecophysiologist: PhD at USP on soybean under elevated CO2, drought and warming, from gas exchange to transcriptomics, and visiting researcher at the University of Illinois (SoyFACE). She built the index and the validation.

## Who we need

**1. Data and remote-sensing cofounder (CTO)**

- Satellite and weather pipelines (Sentinel-2, MODIS, ERA5), geospatial Python, cloud jobs, an API for customers.
- Good with statistics and validation. Bonus: crop models, ML for yield.
- Ideally based in São Paulo state, since the FAPESP PIPE grant requires the principal investigator to be a partner living in SP.
- Where we're looking: USP ICMC and Poli, ESALQ, INPE, the Ciampitti Lab (N Scout) team, hackathon participants.

**2. Business cofounder (managing partner)**

- Sells to co-ops, input resellers, rural credit and insurance. Knows how a credit committee or an underwriting desk decides.
- Background: ex-co-op, ex-insurer or reinsurer, ex-agfintech, or rural credit manager.
- Would be the company's administrator. The founder will soon hold a public research post, so this role matters from day one.

**Advisors:** a crop modeller, an agricultural insurance actuary and a rural credit manager.

## How we'd start

1. **A 30-minute call**, then a short trial project (4–6 weeks) before any equity talk.
2. **Trial ideas:**
   - CTO: wrap the weekly monitor in a simple API and map viewer.
   - Business: run 5 of the customer demos and bring back a price range.
3. **Equity, vesting (4 years, 1-year cliff) and roles** get agreed in writing after the trial.

**Contact:** psjana@usp.br · github.com/Fortirer/soy-stress-index
