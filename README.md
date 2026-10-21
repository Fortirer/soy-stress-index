# Soybean Stage-weighted Stress Index (SSI)

**A physiology-based drought and heat stress index for soybean in Brazil, built from public weather and satellite data and weighted by crop stage.**

The index scores each municipality and season for water deficit, extreme heat and their interaction, separately for the vegetative and reproductive stages, and weights the reproductive stages (flowering, pod set, seed fill) three times more. It is the scientific core of a climate-risk product for agricultural lenders, cooperatives and insurers.

> Status: **v1 (satellite + weather by crop stage) is built and backtested** for Rio Grande do Sul and Paraná, harvests 2001-2023, **tested out of sample on 2024 and 2025**, with confidence intervals and an early-warning test. A Sentinel-2 field pilot (15 plots, 2020/21 vs 2021/22) and a ready-to-run field-yield validation for a co-op pilot are included.

---

## v1 results: satellite crop stages + NDVI cut basis risk

17,342 municipality-harvests in RS and PR, 2001-2023. MODIS NDVI over summer-crop pixels in each municipality; crop stages read from each season's NDVI curve; NASA POWER daily weather summed over those stages. **No weights were fitted** (physiology priors only), so there is no training leakage.

| Region | Index | AUC, loss > 10% | State-year r | Basis risk |
| --- | --- | --- | --- | --- |
| RS + PR | ZARC risk class (official zoning) | 0.573 | 0.41 | 0.64 |
| RS + PR | Rainfall index | 0.784 | 0.68 | 0.44 |
| RS + PR | SSI v0 (calendar windows) | 0.791 | 0.71 | 0.46 |
| RS + PR | NDVI only | 0.773 | 0.85 | 0.44 |
| RS + PR | SSI v1, weather by satellite stage | 0.786 | 0.79 | 0.44 |
| RS + PR | **SSI v1 full (+ NDVI)** | **0.828** | **0.88** | **0.37** |
| RS | ZARC risk class | 0.584 | 0.51 | 0.60 |
| RS | Rainfall index | 0.857 | 0.76 | 0.31 |
| RS | **SSI v1 full** | **0.871** | **0.92** | **0.30** |
| PR | ZARC risk class | 0.535 | 0.49 | 0.73 |
| PR | Rainfall index | 0.696 | 0.58 | 0.60 |
| PR | **SSI v1 full** | **0.775** | **0.86** | **0.46** |

- The full index **misses 15% fewer real losses** than a rainfall trigger over RS + PR (basis risk 0.44 to 0.37), and **23% fewer in Paraná** (0.60 to 0.46).
- Neither satellite nor weather alone gets there: NDVI only and weather-by-stage only both stay at 0.44. The gain comes from combining them by stage.
- Reading the stage timing from NDVI instead of a fixed Jan-Feb calendar raises the state-year correlation from 0.71 to 0.79 using weather alone.

![v1 skill](figures/fig3_v1_skill.png)

![RS NDVI 2021 vs 2022](figures/fig4_rs_ndvi_2021_vs_2022.png)

Caveat: NDVI measures the canopy during the season, so v1 is an **in-season monitor and loss estimator**, not a pre-season forecast. That is what lenders, co-ops and parametric insurers need during the season; pre-season pricing still uses the weather climatology.

---

## Validation round (October 2026): new seasons, confidence intervals, lead time

### 1. Out-of-sample test on the 2024 and 2025 harvests

These two harvests were never used to build the index. Yields come fresh from IBGE PAM (SIDRA table 1612). Each municipality's trend and its z-score reference use 2001-2023 only, and the weights are unchanged. 1,542 municipality-harvests in RS and PR.

| Region, harvests | Index | AUC, loss > 10% | Basis risk |
| --- | --- | --- | --- |
| RS + PR, 2024+2025 | ZARC risk class | 0.571 | 0.462 |
| RS + PR, 2024+2025 | Rainfall index | 0.563 | 0.505 |
| RS + PR, 2024+2025 | NDVI only | 0.606 | 0.422 |
| RS + PR, 2024+2025 | **Turgor full** | **0.695** | **0.342** |
| RS, 2024+2025 | ZARC risk class | 0.541 | 0.381 |
| RS, 2024+2025 | Rainfall index | 0.777 | 0.231 |
| RS, 2024+2025 | **Turgor full** | **0.808** | **0.203** |
| PR, 2024+2025 | ZARC risk class | 0.607 | 0.563 |
| PR, 2024+2025 | Rainfall index | 0.575 | 0.509 |
| PR, 2024+2025 | **Turgor full** | **0.656** | **0.495** |

- On new seasons the index **misses 32% fewer real losses** than the rainfall trigger (basis risk 0.51 to 0.34).
- The 2025 RS drought (yield 34% below trend) ranks in the top 12% of stress since 2001.
- Skill is lower than in the backtest (AUC 0.70 vs 0.83). Two seasons is a small sample, and part of the 2024 RS loss came from the May 2024 floods at harvest, which no drought index should flag.

![Holdout](figures/fig7_holdout_2024_2025.png)

### 2. Confidence intervals (2001-2023 backtest)

95% intervals from 1,000 bootstrap resamples of whole harvest years. Municipalities in the same season share weather, so rows are not independent. `results/v1_ci.csv`.

| Region | Metric | Rainfall index | Turgor full | Difference (95% CI) | Turgor better in |
| --- | --- | --- | --- | --- | --- |
| RS + PR | AUC | 0.784 (0.70-0.84) | 0.828 (0.77-0.87) | +0.044 (-0.003 to +0.107) | 96% of resamples |
| RS + PR | Basis risk | 0.44 (0.33-0.61) | 0.37 (0.29-0.51) | -0.067 (-0.16 to +0.01) | 95% |
| RS + PR | State-year r | 0.68 (0.52-0.78) | 0.88 (0.76-0.93) | +0.19 (+0.09 to +0.32) | >99% |
| PR | Basis risk | 0.60 (0.47-0.81) | 0.46 (0.38-0.60) | -0.14 (-0.26 to -0.05) | >99% |
| RS | Basis risk | 0.31 (0.20-0.48) | 0.30 (0.21-0.46) | -0.01 (-0.12 to +0.12) | 55% |

- **Paraná: the gain is clear** on every metric. **RS + PR: borderline** at the municipality level, clear at the portfolio (state-year) level.
- **Rio Grande do Sul: no clear gain** over rainfall at the municipality level. RS droughts are rainfall droughts, so a rainfall index already works there; the gain in RS is in portfolio correlation and in lead time (below).

### 3. How early it warns

The index rebuilt as it would have looked on each date, using only data available then: weather 3 days late, MODIS 16-day composites 23 days late, and each municipality's typical stage windows (median of its other seasons), since the current season's stages are not known yet. `results/early_warning.csv`.

| Data up to | Turgor AUC (RS + PR) | Rainfall index AUC | Turgor basis risk |
| --- | --- | --- | --- |
| 1 Dec | 0.52 | no signal yet | |
| 1 Jan | 0.74 | no signal yet | 0.49 |
| 15 Jan | **0.79** | 0.70 | 0.41 |
| 1 Feb | 0.79 | 0.67 | 0.42 |
| 1 Mar | 0.85 | 0.78 | 0.35 |
| 15 Mar onward | 0.86 | 0.78 | 0.33 |

- **By 15 January the index already matches the rainfall index's end-of-season skill** (0.78), about 6 weeks earlier. In PR it beats the final rainfall index from 1 January.
- Typical harvest is late Feb-March in PR and March-April in RS, so a usable warning comes **8-12 weeks before harvest**.
- On the 2024-2025 holdout the same holds: by 1 January AUC 0.68 (rainfall: no signal), by 15 February 0.71 vs 0.68.
- The real-time version with typical windows ends the season at AUC 0.86, higher than the full-season version with each season's own satellite windows (0.83). In a drought the NDVI peak comes early and low, which shifts the season's own window; a fixed window keeps the collapse inside it. The product should use typical windows.

![Early warning](figures/fig6_early_warning.png)

### 4. ZARC: what the market uses today

ZARC (Zoneamento Agrícola de Risco Climático, MAPA/Embrapa) is the official zoning that rural credit and subsidised insurance require. It gives, per municipality, soil class, cycle and 10-day sowing window, a risk class of 20, 30 or 40% of crop failure; windows not listed are "not indicated" (scored here as 50%).

ZARC score per municipality-season: sowing date = NDVI green-up minus 20 days; soil class AD2 (soil type 2 in tables before 2023/24); the lowest-risk cycle available; the ZARC table of that safra (MAPA open data, safras 2017/18 to 2025/26; harvests before 2018 use the 2017/18 table). `scripts/15_zarc_baseline.py`, `results/baselines_ci.csv`, `results/zarc_scores.csv.gz`.

| Test | Region | Turgor full | ZARC | Rainfall | NDVI only | Turgor minus ZARC, AUC (95% CI) |
| --- | --- | --- | --- | --- | --- | --- |
| Backtest 2001-2023, AUC | RS + PR | **0.828** | 0.573 | 0.784 | 0.773 | +0.26 (+0.20 to +0.31) |
| Backtest 2001-2023, AUC | RS | **0.871** | 0.584 | 0.857 | 0.829 | +0.29 (+0.22 to +0.35) |
| Backtest 2001-2023, AUC | PR | **0.775** | 0.535 | 0.696 | 0.705 | +0.24 (+0.18 to +0.30) |
| Backtest, basis risk | RS + PR | **0.37** | 0.64 | 0.44 | 0.44 | |
| Holdout 2024-2025, AUC | RS + PR | **0.698** | 0.571 | 0.566 | 0.608 | +0.13 (+0.09 to +0.16)* |
| Holdout, basis risk | RS + PR | **0.34** | 0.46 | 0.50 | 0.42 | |

\* Holdout intervals resample municipalities (only two seasons), so they are narrower than the year-resampled backtest intervals. Turgor beats ZARC in every region of the backtest (100% of resamples) and in the RS and RS + PR holdout. In the PR holdout the gain is borderline: AUC +0.05 (-0.01 to +0.12), basis risk 0.49 vs 0.56.

- **ZARC barely separates loss seasons from normal ones** (AUC 0.54-0.61). It is a pre-season, static zoning: it says where and when sowing is risky, not how this season is going. On 2018-2023 alone, where each safra has its own table, ZARC reaches 0.62 against 0.85 for Turgor.
- ZARC still carries some portfolio signal (state-year r 0.41), possibly because dry springs delay sowing into riskier windows (not tested).
- Read this as "Turgor adds in-season information on top of the zoning lenders already use", not "ZARC is wrong": ZARC answers a different, pre-season question and remains an input.

### 5. Field yields: ready for a co-op pilot

Real field yields are not public, so this step needs a partner. Everything is ready:

- `scripts/13_field_validation.py`: takes the partner's field polygons and yields per field and season, reads each field's Sentinel-2 curve and stages, adds weather at the field, and compares the field index with the municipal index on the same field-seasons (AUC, basis risk, within-season ranking of fields).
- `python scripts/13_field_validation.py --demo` runs it end to end on 4 pilot plots with **synthetic** yields (a pipeline test, not a result).
- `docs/pilot_data_request_pt.md`: the one-page data request for co-ops (in Portuguese).

---

## Sentinel-2 field pilot (2020/21 vs 2021/22 drought)

Three RS municipalities with different 2022 losses. In a 10 x 10 km window in each, five ~35 ha sample plots were picked at random among cells that were at least 90% soybean in 2020/21, detected from Sentinel-2 itself (low NDVI in Oct-Nov, dense canopy in Jan-Feb; 20 m). Each plot's NDVI was followed through both seasons, and its crop stages read from its own curve.

| Municipality | IBGE yield vs trend, 2021 to 2022 | MODIS municipal change, reproductive NDVI | Sentinel-2 plots, reproductive NDVI change (5 plots) |
| --- | --- | --- | --- |
| Dom Pedrito | +29% to -20% | -14% | -8% to -37% (median -25%) |
| Cruz Alta | +38% to -53% | -31% | -12% to -61% (median -52%) |
| Tupanciretã | +29% to -66% | -26% | -27% to -49% (median -45%) |

![Sentinel-2 field plots](figures/fig5_sentinel2_fields.png)

- Plot-level NDVI loss ranks the municipalities in the same order as IBGE yield loss, and it is closer to the size of the yield loss than municipal MODIS. MODIS mixes soybean with other cover at 1 km.
- **Damage differs field by field.** In Cruz Alta, one plot lost 12% of reproductive NDVI while its neighbours lost 51-61%. A municipal index pays every field the same way; this is exactly the basis risk a field-level product removes.
- Limits: plots are sample cells, not farm boundaries (CAR or co-op polygons would replace them), there are no field yields to validate against, and only two seasons are compared. Next step: real fields with harvest records from one co-op.

Run it: `python scripts/07_sentinel2_pilot.py` then `python scripts/08_pilot_figure.py` (Sentinel-2 stacks are cached in `data/s2_cache/`).

---

## v0 results (weather only, all states, 1981-2023)

---

Backtest on 62,968 municipality-harvests in 10 Brazilian states, harvests 1981-2023. Yields from IBGE PAM, detrended per municipality; a **loss** is a harvest more than 10% below the municipality's own trend.

| Region | Index | AUC, loss > 10% | State-year r with yield | Basis risk* |
| --- | --- | --- | --- | --- |
| RS | Rainfall index (Jan-Feb rain) | 0.778 | 0.61 | 0.37 |
| RS | **SSI a priori** | **0.783** | **0.70** | 0.40 |
| PR | Rainfall index | 0.664 | 0.39 | 0.61 |
| PR | **SSI a priori** | **0.724** | **0.62** | **0.56** |
| RS + PR | Rainfall index | 0.725 | 0.52 | 0.48 |
| RS + PR | **SSI a priori** | **0.753** | **0.65** | 0.48 |

\* Basis risk: the index is turned into a trigger that pays in as many municipality-seasons as losses really occur; basis risk is the share of real losses it misses (equal to the share of payouts that go to non-losses). Lower is better.

**Named drought harvests** (percentile of each harvest's stress among all years in that state; 100 = most stressed year on record):

| State | Harvest | Yield vs trend | Rainfall index | SSI a priori |
| --- | --- | --- | --- | --- |
| RS | 2005 | -68.8% | 100 | 95 |
| RS | 2012 | -40.6% | 81 | 93 |
| RS | 2020 | -27.5% | 79 | 88 |
| RS | 2022 | -43.4% | 88 | **100** |
| RS | 2023 | -29.5% | 95 | 98 |
| PR | 2012 | -19.5% | 93 | 98 |
| PR | 2022 | -31.6% | 95 | **100** |

![State-year stress vs yield](figures/fig1_state_year_stress_vs_yield.png)

**What the backtest says**

- Adding heat, the heat x dry interaction and stage weighting improves on rainfall alone, most of all in Paraná (state-year correlation 0.39 to 0.62).
- **Physiology priors beat fitted weights.** Weights learned by logistic regression (leave-one-year-out) do worse than the a-priori stage weights in every region. With few drought years, the prior generalizes better than the data alone.
- The signal is strong in the south (RS, PR) and weak in Mato Grosso and Goiás, where rainfall is more reliable and other factors drive yield. The product should start in the south.

![Skill by index](figures/fig2_skill_by_index.png)

---

## How the index works

```
SSI = 0.25 * Stress(vegetative) + 0.75 * Stress(reproductive)

Stress(stage) = Z(water deficit) + 0.5 * Z(extreme heat) + 0.5 * max(Z water, 0) * max(Z heat, 0)
                - Z(NDVI)                      <- v1, from satellite
```

- **Z** = standardized anomaly against each municipality's own record, so the index measures stress relative to what is normal there.
- **Water deficit**: crop water demand (ET0) not met by rain and stored soil water.
- **Extreme heat**: degree-days above 30 °C.
- **Heat x dry**: heat is mostly harmless when water is available and damaging when it is not (found in the companion Illinois analysis).
- **Stages**:
  - v0 uses the calendar critical window (Jan-Feb) from the source data.
  - v1 reads green-up and peak from each municipality's NDVI curve:
    - vegetative = green-up to 16 days before peak;
    - reproductive = 16 days before to 40 days after peak.

## Pipeline

| Step | Data | Script |
| --- | --- | --- |
| NDVI per municipality, cropland pixels only, 16-day composites 2001-2023 | MODIS MOD13Q1 (250 m) + MCD12Q1 cropland mask, Microsoft Planetary Computer | `04_download_modis.py` |
| Crop stages per municipality-season from the NDVI curve | derived | `04_download_modis.py` |
| Daily weather per municipality, water balance, heat, VPD by stage window | NASA POWER | `05_download_power.py` |
| Full index and comparison with v0, NDVI only and rainfall | | `06_full_index.py` |
| Field-scale NDVI for sample plots, 2 seasons | Sentinel-2 L2A (20 m) | `07_sentinel2_pilot.py`, `08_pilot_figure.py` |

**Satellite details.** MOD13Q1 (Terra and Aqua, 8-day spacing) is read at about 1 km from the COG overviews. Pixels must be IGBP cropland (MCD12Q1) *and* show a summer cycle: low NDVI in Oct-Nov, high in Jan-Mar, amplitude at least 0.15. This removes pasture, forest and winter-wheat-only pixels. Stages per municipality-season:

- green-up: half-amplitude rise after the Oct-Dec minimum;
- peak: Dec-Mar maximum;
- reproductive window: 16 days before to 40 days after the peak.

## Run it

```bash
pip install -r requirements.txt
git clone --depth 1 https://github.com/Fortirer/-Modelling-soybean.git ../Modelling-soybean
python scripts/01_build_panel.py ../Modelling-soybean   # yields + weather, year-aligned
python scripts/02_weather_index.py                      # v0 backtest
python scripts/03_figures.py
# v1 - downloads from planetarycomputer.microsoft.com, *.blob.core.windows.net
# and power.larc.nasa.gov (about 45 min per state for MODIS; results are in data/ already)
python scripts/04_download_modis.py --states RS PR
python scripts/05_download_power.py --states RS PR
python scripts/06_full_index.py
python scripts/03_figures.py
# validation round
python scripts/10_confidence_intervals.py               # year-block bootstrap
python scripts/11_early_warning.py                      # skill by date
python scripts/04_download_modis.py --states RS --first 2024 --last 2025   # then PR
python scripts/09_extend_weather.py                     # POWER to May 2025
python scripts/12_holdout_2024_2025.py                  # needs apisidra.ibge.gov.br
python scripts/14_validation_figures.py
python scripts/15_zarc_baseline.py --offline          # ZARC tables in data/zarc/ (MAPA open data)
python scripts/13_field_validation.py --fields F.geojson --yields Y.csv   # co-op pilot
pytest -q                                                 # offline tests
```

## Data note: year alignment in the source repo

In `Modelling-soybean`, Brazilian weather aggregates are keyed by **crop year** (season start, Sep of Y), while IBGE yields are keyed by **harvest year** (Y+1). Joining them on the same year pairs each harvest with the previous season's weather.

In Rio Grande do Sul, this drops the correlation between Jan-Feb water deficit and yield from **-0.48 (aligned) to -0.08 (as joined)**. `ssi/data.py` shifts weather by one year before joining. The Brazilian results in the source repo should be re-run with the same fix.

## Repository layout

```
ssi/          config, data loading, index, evaluation, satellite, weather
scripts/      01-06 pipeline steps
data/         panel.csv.gz (municipal yields + weather), municipalities.geojson
results/      metrics, drought-year tables, municipal scores
figures/      backtest figures
tests/        offline tests (synthetic NDVI and weather)
```

## Limits

- MODIS at about 1 km mixes soybean with other summer crops (maize, rice in RS). A soybean map (MapBiomas) or 250 m reads would sharpen it.
- The summer-crop mask can drop the worst-hit pixels in severe droughts (low amplitude), which may understate NDVI losses in those years.
- Stage windows use fixed offsets around the NDVI peak; calibrating them on field phenology (e.g. Embrapa trials) is the next step.
- Municipal yields average many farms; field-level skill needs pilot data from cooperatives.
- The 2024-2025 holdout covers only two seasons; it will grow by one season a year.
- In Rio Grande do Sul the index does not clearly beat a rainfall index at the municipality level (see confidence intervals).

## License and credit

MIT. Yields and weather features from [Modelling-soybean](https://github.com/Fortirer/-Modelling-soybean) (J. Fortirer). Satellite data: NASA MODIS and ESA Sentinel-2 via Microsoft Planetary Computer. Weather: NASA POWER.
