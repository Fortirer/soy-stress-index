"""Extend daily NASA POWER weather to the 2024 and 2025 harvests.

    python scripts/09_extend_weather.py --states RS PR

Writes data/power_ext/<code>.csv.gz (2023-06-01 to 2025-05-31). Together with
data/power/ (2000-09-01 to 2023-05-31) this gives an unbroken daily record.
"""
import argparse
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ssi.config import DATA  # noqa: E402
from ssi.data import load_boundaries  # noqa: E402
from ssi.weather import fetch_power  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--states", nargs="+", default=["RS", "PR"])
ap.add_argument("--start", default="2023-06-01")
ap.add_argument("--end", default="2025-05-31")
ap.add_argument("--workers", type=int, default=6)
args = ap.parse_args()

cache = DATA / "power_ext"
cache.mkdir(parents=True, exist_ok=True)
feats = [f for f in load_boundaries()["features"] if f["properties"]["st"] in args.states]


def get(f):
    fp = cache / f"{int(f['id'])}.csv.gz"
    if not fp.exists():
        ring = np.array(f["geometry"]["coordinates"][0])
        fetch_power(ring[:, 1].mean(), ring[:, 0].mean(), args.start, args.end).to_csv(fp)


with ThreadPoolExecutor(args.workers) as pool:
    for i, _ in enumerate(pool.map(get, feats), 1):
        if i % 100 == 0:
            print(f"{i}/{len(feats)}", flush=True)
print("done")
