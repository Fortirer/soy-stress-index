# 3-minute pitch (issue #23)

The **deck** (9 slides, English) is a private Slides page in claude.ai. It can be downloaded as PowerPoint or PDF and shared from its Share menu. The **one-pager** with the QR code is [`docs/report/turgor_onepager_en.pdf`](../report/turgor_onepager_en.pdf), rebuilt by `scripts/26_onepager.py`.

Read aloud at a calm pace: about 420 words, 3 minutes. The same text is in each slide's speaker notes.

| Slide | Say | Time |
| --- | --- | --- |
| 1. Cover | Hi, I’m Janaina, a plant ecophysiologist. I study what drought and heat do to soybean, from the leaf to the yield. Turgor turns that physiology into a number that tells co-ops, lenders and insurers which fields are losing yield, weeks before harvest. | 0:15 |
| 2. Problem | Brazilian co-ops, resellers and banks finance soybean. In the south, losses below trend average 700 to 1,200 reais per hectare a year, and they find out at harvest. Rainfall-based insurance triggers miss 44% of real losses, and the official zoning barely separates bad seasons from good ones. | 0:25 |
| 3. How it works | Turgor reads each field’s crop stage from satellites and adds daily weather. Then it weights drought and heat by when they hit: at flowering and seed fill they count three times more, because that is where yield is made. Out comes a weekly map and an expected loss in reais per hectare. No sensors on the farm. | 0:25 |
| 4. Early warning | The key result is timing. Using only the data available on each date, by 15 January the index separates loss seasons as well as a rainfall index does at the end of the season: 8 to 12 weeks before harvest. | 0:20 |
| 5. Replay 2025 | Here is a real season, replayed with the data that existed on 15 February 2025. Municipalities rated severe ended 30% below trend, and 83% of them lost more than 10%. The ones rated normal ended slightly above trend. | 0:20 |
| 6. Evidence | Every number is reproducible from the open repository. Over 23 seasons and 780 municipalities, the index beats rainfall, NDVI and the zoning. On the two newest seasons, never used in fitting, it misses 28% fewer real losses than rainfall. One honest limit: in Rio Grande do Sul, rainfall already works well, so the gain there is not yet proven. | 0:25 |
| 7. Business | We sell per hectare per season to whoever carries the risk, plus a licence for insurance triggers. At three reais per hectare, RS and PR are about 37 million reais a year, and Brazil about 146 million. | 0:20 |
| 8. Why Turgor | Brazil already has parametric insurtechs. They sell insurance. We supply the index: built on physiology, validated in public, and early. That makes them possible customers too. | 0:15 |
| 9. Ask | I’m looking for pilots (a free backtest on your own portfolio in two weeks), a data cofounder, a business cofounder, and advisors. Thank you. | 0:15 |

## Likely questions

- **“How is this different from NDVI monitoring?”** NDVI sees damage after the canopy shows it. Turgor adds when drought and heat hit the crop stage, so it sees the loss earlier, and it beats NDVI alone (AUC 0.86 vs 0.77).
- **“Why not just use rainfall?”** In Paraná, rainfall misses many losses (heat, timing). In Rio Grande do Sul it is close, and the advantage there is timing and portfolio view.
- **“Field level?”** The Sentinel-2 field pipeline is ready. Validation needs a co-op’s field yields, which is the pilot we are looking for.
- **“Who pays first?”** That is what the current interviews test: co-ops with input credit, credit co-ops and parametric insurtechs.
- **“Can others copy the code?”** Yes, it is open. The moat is the physiology, the public weekly track record, customer field data and calibration with controlled experiments.
