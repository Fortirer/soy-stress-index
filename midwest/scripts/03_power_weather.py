"""Daily NASA POWER weather at each Illinois county centroid, 2000-2025.

    python midwest/scripts/03_power_weather.py

Cached in midwest/data/power/<fips>.csv.gz (not committed; re-downloadable).
"""
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from turgor_us import DATA, centroid  # noqa: E402
from ssi.weather import fetch_power  # noqa: E402

cache = DATA / "power"
cache.mkdir(exist_ok=True)
feats = json.load(open(DATA / "il_counties.geojson"))["features"]


def one(f):
    fp = cache / f"{int(f['id'])}.csv.gz"
    if not fp.exists():
        lat, lon = centroid(f)
        fetch_power(lat, lon, "2000-01-01", "2025-12-31").to_csv(fp)
    return fp


with ThreadPoolExecutor(6) as pool:
    for i, _ in enumerate(pool.map(one, feats), 1):
        if i % 20 == 0:
            print(f"{i}/{len(feats)}", flush=True)
print("done")
