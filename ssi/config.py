"""Configuration for the Soybean Stage-weighted Stress Index (SSI)."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RESULTS = ROOT / "results"
FIGURES = ROOT / "figures"

# Source of yields and weather: https://github.com/Fortirer/-Modelling-soybean
SOURCE_REPO = "https://github.com/Fortirer/-Modelling-soybean.git"

STATES = ["RS", "PR", "MS", "SP", "MG", "GO", "MT", "BA", "MA", "TO"]
FOCUS_STATES = ["RS", "PR"]  # where drought losses are largest and best documented

# A loss event: municipal yield more than 10% below its own technology trend.
LOSS_THRESHOLD = -0.10

# Documented drought harvests used as named backtest cases (harvest year).
DROUGHT_HARVESTS = {"RS": [2005, 2012, 2020, 2022, 2023], "PR": [2005, 2009, 2012, 2022]}

# ---------------------------------------------------------------- stage weights
# Share of final yield sensitivity attributed to stress in each phase.
# Reproductive stages (R1-R6: flowering, pod set, seed fill) dominate soybean
# yield response to water deficit and heat; vegetative stress is partly
# recovered. Starting values from crop physiology; scripts/02 also fits them.
STAGE_WEIGHTS = {"vegetative": 0.25, "reproductive": 0.75}

# Within a stage: water deficit is the main driver; heat matters mostly when
# it is dry (heat x dry interaction, as found in the Illinois analysis).
COMPONENT_WEIGHTS = {"water": 1.0, "heat": 0.5, "heat_x_dry": 0.5, "ndvi": 1.0}

# ---------------------------------------------------------------- satellite
# Microsoft Planetary Computer STAC (free, anonymous token signing)
STAC_URL = "https://planetarycomputer.microsoft.com/api/stac/v1"
MODIS_NDVI = "modis-13Q1-061"   # 250 m, 16-day composites, 2000-present
MODIS_LC = "modis-12Q1-061"     # yearly land cover, used as cropland mask
SENTINEL2 = "sentinel-2-l2a"    # 10 m, 5-day revisit, 2017-present
CROPLAND_CLASSES = [12, 14]     # IGBP croplands, cropland/natural mosaic

# Soybean season in southern Brazil: sowing Sep-Dec, harvest Feb-May.
SEASON_START_MMDD = "09-01"
SEASON_END_MMDD = "05-31"

# NASA POWER daily agro-climatology (free, no key)
POWER_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"
POWER_VARS = ["T2M_MAX", "T2M_MIN", "PRECTOTCORR", "RH2M", "ALLSKY_SFC_SW_DWN", "WS2M"]
