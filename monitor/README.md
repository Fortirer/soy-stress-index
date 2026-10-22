# Turgor live monitor

The Turgor index for the current soybean season in Rio Grande do Sul and Paraná, updated every week from **1 December to 15 April**. Each week's output is kept, so the season becomes a timestamped track record written **before** harvest.

- **Latest:** [`latest/summary.md`](latest/summary.md) · [`latest/map.png`](latest/map.png) (appears after the first run of the season, 2 December 2026)
- **All runs:** [`log.csv`](log.csv) and one folder per week under `<season>/<as-of date>/`

## What each run contains

| File | Content |
| --- | --- |
| `turgor_monitor.csv` | one row per municipality: Turgor index, percentile against its own past seasons at the same date, stress class, P(loss > 10%), expected yield vs trend, expected loss in R$/ha, main driver (water deficit, heat or weak canopy) and the three stage-weighted z-scores |
| `turgor_monitor.geojson` | the same with municipality outlines, for QGIS or a web map |
| `map.png` | stress class map |
| `summary.md` | class counts and the 20 most stressed municipalities |

**Stress class** (municipality against its own 2001-2025 seasons at the same date): severe > 95th percentile, high > 85th, watch > 70th, normal otherwise.

**P(loss > 10%), expected yield vs trend, expected loss R$/ha:** how past municipality-seasons (2001-2025) with a similar index at the same date ended, from monotone (isotonic) maps per state (`scripts/18_expected_loss.py`). R$/ha = expected shortfall below the municipality's yield trend × trend yield × soybean price (default R$ 153.49 per 60 kg bag, CEPEA/ESALQ Paraná, 28 Sep 2026; `--price` to change). These are base rates: on the 2024-2025 test the probabilities were too confident at both ends (see the main README).

## How it runs

- `scripts/17_monitor.py --asof YYYY-MM-DD` downloads this season's MODIS NDVI (Planetary Computer) and NASA POWER daily weather, and computes `ssi.early.turgor_index` on the latest weekly anchor (1, 8, 15 and 22 of each month), with real-time data latency and typical stage windows.
- The reference for past seasons (`data/monitor_reference.csv.gz`, `results/monitor_loss_rates.csv`) is built once by `scripts/16_monitor_reference.py`; the expected-loss maps (`results/expected_loss_models_anchors.csv`, `results/yield_trend_next.csv`) by `scripts/18_expected_loss.py`.
- `.github/workflows/monitor.yml` runs it on GitHub the day after each anchor (2, 9, 16 and 23 of December to April) and commits the outputs here. It can also be started by hand (Actions → season-monitor → Run workflow, optional as-of date).
- Before 1 December the monitor writes nothing: the reproductive windows have not started.

## Replay: 15 February 2025 (the 2024/25 drought in RS)

`replays/2024-25/2025-02-15/` is the monitor run as if on 16 February 2025, with 2025 left out of the reference. Compared with the IBGE yields published later (771 municipalities with yields):

| Class on 15 Feb 2025 | Municipalities | Mean yield vs trend | Share with loss > 10% |
| --- | --- | --- | --- |
| severe | 227 | -29.6% | 83% |
| high | 212 | -23.6% | 68% |
| watch | 215 | -4.6% | 33% |
| normal | 117 | +0.8% | 19% |

AUC for loss > 10%: **0.81**, about two months before harvest. In this replay the expected-loss columns come from maps fitted on 2001-2025, so they include 2025; the classes and the index do not.
