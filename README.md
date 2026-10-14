# Soybean Stage-weighted Stress Index (SSI)

**A physiology-based drought and heat stress index for soybean in Brazil, built from public weather and satellite data and weighted by crop stage.**

The index scores each municipality and season for water deficit, extreme heat and their interaction, separately for the vegetative and reproductive stages, and weights the reproductive stages (flowering, pod set, seed fill) three times more. It is the scientific core of a climate-risk product for agricultural lenders, cooperatives and insurers.

> Status: **v1 (satellite + weather by crop stage) is built and backtested** for Rio Grande do Sul and Paraná, harvests 2001-2023. Sentinel-2 field-scale code is included but not yet run on pilot fields.

---

## v1 results: satellite crop stages + NDVI cut basis risk

17,342 municipality-harvests in RS and PR, 2001-2023. MODIS NDVI over summer-crop pixels in each municipality; crop stages read from each season's NDVI curve; NASA POWER daily weather summed over those stages. **No weights were fitted** (physiology priors only), so there is no training leakage.

| Region | Index | AUC, loss > 10% | State-year r | Basis risk |
| --- | --- | --- | --- | --- |
| RS + PR | Rainfall index | 0.784 | 0.68 | 0.44 |
| RS + PR | SSI v0 (calendar windows) | 0.791 | 0.71 | 0.46 |
| RS + PR | NDVI only | 0.773 | 0.85 | 0.44 |
| RS + PR | SSI v1, weather by satellite stage | 0.786 | 0.79 | 0.44 |
| RS + PR | **SSI v1 full (+ NDVI)** | **0.828** | **0.88** | **0.37** |
| RS | Rainfall index | 0.857 | 0.76 | 0.31 |
| RS | **SSI v1 full** | **0.871** | **0.92** | **0.30** |
| PR | Rainfall index | 0.696 | 0.58 | 0.60 |
| PR | **SSI v1 full** | **0.775** | **0.86** | **0.46** |

- The full index **misses 15% fewer real losses** than a rainfall trigger over RS + PR (basis risk 0.44 to 0.37), and **23% fewer in Paraná** (0.60 to 0.46).
- Neither satellite nor weather alone gets there: NDVI only and weather-by-stage only both stay at 0.44. The gain comes from combining them by stage.
- Reading the stage timing from NDVI instead of a fixed Jan-Feb calendar raises the state-year correlation from 0.71 to 0.79 using weather alone.

![v1 skill](figures/fig3_v1_skill.png)

![RS NDVI 2021 vs 2022](figures/fig4_rs_ndvi_2021_vs_2022.png)

Caveat: NDVI measures the canopy during the season, so v1 is an **in-season monitor and loss estimator**, not a pre-season forecast. That is what lenders, co-ops and parametric insurers need during the season; pre-season pricing still uses the weather climatology.

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
| Field-scale NDVI (10 m) for pilot farms | Sentinel-2 L2A | `ssi.satellite.sentinel2_ndvi()` (not yet run) |

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
- Harvests end in 2023 in the current panel. The 2024/25 drought in RS is not yet included.

## License and credit

MIT. Yields and weather features from [Modelling-soybean](https://github.com/Fortirer/-Modelling-soybean) (J. Fortirer). Satellite data: NASA MODIS and ESA Sentinel-2 via Microsoft Planetary Computer. Weather: NASA POWER.
