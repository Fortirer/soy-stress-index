# US market size and pricing

Slide: [`figures/us_market_size_slide.png`](../figures/us_market_size_slide.png). Numbers come from `scripts/10_market_size.py` and are written to `results/us_market_size.csv`. To update them, change the inputs at the top of the script and run it again.

## Formula

**Revenue = customers × acres per customer × price per acre per season**, summed by segment. For insurance triggers the revenue is a licence fee: covered acres × premium per acre × licence share.

## Numbers (price hypothesis US$ 1 per acre per season)

| Level | How | Acres | US$ per year |
| --- | --- | --- | --- |
| TAM | All US soybean, 81.2 M acres planted in 2025 | 81.2 M | $81 M |
| SAM | Illinois + Iowa + Indiana, 25.2 M acres | 25.2 M | $25 M |
| SOM, lenders | 6 Farm Credit associations or ag banks × 300k acres | 1.8 M | $1.8 M |
| SOM, grain co-ops and elevators | 8 × 150k acres | 1.2 M | $1.2 M |
| SOM, insurance portfolio analytics | 3 portfolios × 500k acres | 1.5 M | $1.5 M |
| SOM, trigger licence | 3% of Illinois insured soybean acres × ~$16/acre premium × 2% | 0.23 M | $0.07 M |
| **SOM in 5 years** | sum | | **≈ $4.6 M** |

**Sources:**

- **2025 soybean acres:** US 81.2 M planted; Illinois 10.3 M, Iowa 9.45 M, Indiana 5.45 M (USDA NASS Crop Production 2025 Summary, [executive briefing, 12 Jan 2026](https://data.nass.usda.gov/Newsroom/Executive_Briefings/2026/01-12-2026.pdf)).
- **Insured acres:** 7.68 M of 10.69 M Illinois soybean acres were insured in 2024 (72%). Illinois soybean indemnities that year were $113 M ([RMA Illinois State Profile 2024](https://www.rma.usda.gov/sites/default/files/2025-03/Illinois-State-Profile-2024.pdf)).
- **Premium:** in Champaign County, 85% Revenue Protection with enterprise units cost the farmer about $7.54/acre in 2025 ([farmdoc daily](https://farmdocdaily.illinois.edu/2025/03/crop-insurance-decisions-for-2025.html)). With the 53% enterprise-unit subsidy at that level, the total premium is about $16/acre. This is my estimate; check it with the farmdoc premium calculator.
- **Farm Credit in Illinois:** $24.6 B of loans to 31,465 customers at the end of 2024 ([Farm Credit](https://farmcredit.com/states/illinois/)).

## Value anchors: is $1/acre reasonable?

Shortfall below trend in Illinois, at $12.55/bu (soybean futures, 22 Oct 2026; `results/il_value_anchors.csv`):

| | US$ per acre |
| --- | --- |
| Revenue at trend yield (2016–2025) | ≈ $700 |
| Average shortfall per year, 2001–2025 | $23.5 |
| Average shortfall per year, 2016–2025 (good run) | $7.9 |
| Bad year (90th percentile) | $57 |
| 2012 | $104 |

$1/acre is about 0.14% of revenue, 4% of the long-run average shortfall and 1% of a 2012-type loss.

## What this means

1. **The US per-acre market is small and cheap.** At $1/acre, even all US soybean is only $81 M a year. Plain satellite imagery is sold cheaply (in Brazil, NDVI maps at about R$ 1 per hectare a year), so a higher price needs a decision it changes, such as loan pricing, adjuster deployment or supply buying.
2. **US crop insurance already pays on measured yield and revenue.** A weather trigger has room only in private supplemental products and reinsurance. That is why the licence line in the SOM is small.
3. **The sale is probably per portfolio, not per acre.** Examples: a lender's loan book, an insurer's book or a merchandiser's draw area, priced per year (for instance $25–100 k). Test this in interviews: "how do you buy data today?"
4. **Price questions to ask** (US$ per acre per season, or per year for the whole book): too cheap, cheap, expensive, too expensive; who signs; when the budget is set.
