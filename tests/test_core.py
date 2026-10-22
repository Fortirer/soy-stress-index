"""Offline tests: no network needed (satellite and weather steps use synthetic data)."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ssi.evaluate import metrics, trigger_basis_risk  # noqa: E402
from ssi.index import components, ssi  # noqa: E402
from ssi.satellite import municipality_raster, stage_windows, zonal_mean  # noqa: E402
from ssi.weather import daily_indicators, stage_weather  # noqa: E402


def synthetic_ndvi(peak="2022-01-25", amp=0.6):
    dates = pd.date_range("2021-09-01", "2022-05-31", freq="16D")
    t = (dates - pd.Timestamp(peak)).days.values
    return pd.Series(dates), pd.Series(0.25 + amp * np.exp(-(t / 40.0) ** 2))


def test_stage_windows_find_peak_and_order():
    d, n = synthetic_ndvi()
    w = stage_windows(d, n)
    assert abs((w["peak"] - pd.Timestamp("2022-01-25")).days) <= 10
    assert w["green_up"] < w["rep_start"] < w["peak"] < w["rep_end"]
    assert w["ndvi_reproductive"] > w["ndvi_vegetative"]


def test_stage_windows_reject_flat_series():
    d, _ = synthetic_ndvi()
    assert stage_windows(d, pd.Series(np.full(len(d), 0.3))) is None


def test_zonal_mean_and_raster():
    from odc.geo.geobox import GeoBox
    gb = GeoBox.from_bbox([0, 0, 2, 1], crs="EPSG:4326", resolution=0.1)
    feats = [{"id": 1, "geometry": {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]}},
             {"id": 2, "geometry": {"type": "Polygon", "coordinates": [[[1, 0], [2, 0], [2, 1], [1, 1], [1, 0]]]}}]
    zones = municipality_raster(feats, gb)
    vals = np.where(zones == 1, 0.8, 0.4).astype("float32")
    z = zonal_mean(vals, zones).set_index("fips5")
    assert np.isclose(z.loc[1, "ndvi"], 0.8) and np.isclose(z.loc[2, "ndvi"], 0.4)


def test_weather_drought_raises_deficit_and_heat():
    idx = pd.date_range("2021-11-01", "2022-03-31")
    wet = pd.DataFrame({"T2M_MAX": 29.0, "T2M_MIN": 18.0, "PRECTOTCORR": 6.0, "RH2M": 75.0,
                        "ALLSKY_SFC_SW_DWN": 22.0, "WS2M": 2.0}, index=idx)
    dry = wet.assign(T2M_MAX=35.0, PRECTOTCORR=0.0, RH2M=45.0)
    win = {"veg_start": "2021-11-01", "veg_end": "2021-12-31",
           "rep_start": "2022-01-01", "rep_end": "2022-02-28"}
    sw_wet = stage_weather(daily_indicators(wet, -29.0), win)
    sw_dry = stage_weather(daily_indicators(dry, -29.0), win)
    assert sw_dry["rep_water_deficit_mm"] > sw_wet["rep_water_deficit_mm"] + 50
    assert sw_dry["rep_edd"] > 100 and sw_wet["rep_edd"] == 0


def make_panel(n_muni=30, n_years=20, seed=0):
    rng = np.random.default_rng(seed)
    rows = []
    for m in range(n_muni):
        for y in range(n_years):
            wd, edd = rng.normal(0, 60), rng.gamma(2, 8)
            rel = -0.002 * wd - 0.004 * edd * (wd > 0) + rng.normal(0, 0.08)
            rows.append({"st": "RS", "fips5": m, "year": 2000 + y, "area_harvested_ha": 1000,
                         "win_water_deficit_mm": wd, "win_edd": edd,
                         "veg_water_deficit_mm": rng.normal(0, 40), "veg_edd": rng.gamma(2, 3),
                         "pcp_critical": 200 - wd + rng.normal(0, 30), "rel_anom": rel})
    df = pd.DataFrame(rows)
    df["loss"] = (df.rel_anom < -0.1).astype(int)
    return df


def test_ssi_detects_simulated_losses():
    df = make_panel()
    m = metrics(ssi(df).values, df)
    assert m["auc_loss"] > 0.75 and m["state_year_r"] > 0.5


def test_ndvi_component_enters_when_present():
    df = make_panel()
    assert "reproductive_ndvi" not in components(df)
    df["ndvi_reproductive"] = 0.8 - 0.001 * df["win_water_deficit_mm"]
    df["ndvi_vegetative"] = 0.6
    assert "reproductive_ndvi" in components(df)


def test_basis_risk_perfect_and_random():
    loss = np.array([0] * 80 + [1] * 20)
    assert trigger_basis_risk(loss.astype(float), loss)["basis_risk"] == 0
    rng = np.random.default_rng(1)
    br = np.mean([trigger_basis_risk(rng.random(100), loss)["basis_risk"] for _ in range(200)])
    assert 0.7 < br < 0.9


def test_field_validation_synthetic():
    """Field index should rank synthetic fields whose yield follows reproductive NDVI."""
    import numpy as np
    import pandas as pd
    from ssi.fieldval import field_index, validate, yield_anomaly
    rng = np.random.default_rng(1)
    rows = []
    for f in range(30):
        for yr in range(2018, 2025):
            nd = rng.normal(0.8, 0.06)
            wd = rng.normal(100, 30)
            rows.append({"field_id": f"F{f}", "harvest_year": yr, "ndvi_vegetative": rng.normal(0.7, 0.05),
                         "ndvi_reproductive": nd, "veg_water_deficit_mm": rng.normal(50, 15),
                         "win_water_deficit_mm": wd, "veg_edd": rng.normal(10, 3), "win_edd": rng.normal(20, 5),
                         "yield_kg_ha": 3500 + 4000 * (nd - 0.8) - 5 * (wd - 100) + rng.normal(0, 120)})
    d = yield_anomaly(pd.DataFrame(rows))
    d["field_index"] = field_index(d).values
    res = validate(d, {"field": "field_index"})
    assert res.loc[0, "auc_loss"] > 0.75


def test_reference_z_uses_training_rows_only():
    import numpy as np
    import pandas as pd
    from ssi.index import local_z
    df = pd.DataFrame({"fips5": [1] * 5, "x": [1.0, 2.0, 3.0, 4.0, 100.0]})
    z = local_z(df, "x", ref=np.array([True, True, True, True, False]))
    assert abs(z.iloc[0] + 1.162) < 0.01 and z.iloc[4] > 70


def test_zarc_table_and_scores(tmp_path):
    import pandas as pd
    from ssi.zarc import decendio, load_table, risk_lookup, zarc_scores
    assert decendio("2023-01-05") == 1 and decendio("2023-10-25") == 30 and decendio("2023-12-31") == 36
    head = ["Nome_cultura", "SafraIni", "SafraFin", "Cod_Cultura", "Cod_Ciclo", "Cod_Solo", "geocodigo", "UF", "municipio"]
    decs = [f"dec{i}" for i in range(1, 37)]
    rows = []
    for ciclo, risk_oct3 in [(1, 30), (2, 20)]:
        r = ["Soja", 2022, 2023, 1, ciclo, "AD2", 4300034, "RS", "Acegua"] + [0] * 36
        r[len(head) + 29] = risk_oct3      # dec30 = 21-31 Oct
        rows.append(r)
    fp = tmp_path / "t.csv"
    pd.DataFrame(rows, columns=head + decs).to_csv(fp, sep=";", index=False)
    lk = risk_lookup({2022: load_table(fp)})
    s = pd.DataFrame({"fips5": [4300034, 4300034], "year": [2023, 2023],
                      "green_up": ["2022-11-15", "2023-01-20"]})
    out = zarc_scores(s, lk).tolist()
    assert out == [20.0, 50.0]   # sown ~26 Oct -> best cycle 20%; sown ~31 Dec -> not indicated


def test_turgor_index_is_ssi_on_asof_features():
    import numpy as np
    import pandas as pd
    from ssi.early import turgor_index
    from ssi.index import ssi
    rng = np.random.default_rng(3)
    f = pd.DataFrame({"fips5": np.repeat([1, 2], 10), "year": list(range(2001, 2011)) * 2,
                      "veg_water_deficit_mm": rng.normal(50, 10, 20), "win_water_deficit_mm": rng.normal(100, 30, 20),
                      "veg_edd": rng.normal(10, 3, 20), "win_edd": rng.normal(20, 5, 20),
                      "ndvi_vegetative": rng.normal(0.7, 0.05, 20), "ndvi_reproductive": rng.normal(0.8, 0.05, 20)})
    assert np.allclose(turgor_index(f), ssi(f))
    ref = f["year"] < 2009
    assert not np.allclose(turgor_index(f, ref=ref), turgor_index(f))


def test_monitor_anchors_and_classes():
    import numpy as np
    import pandas as pd
    from ssi.monitor import anchor_for, harvest_year_of, own_percentile, stress_class
    assert anchor_for("2026-11-20") is None
    assert anchor_for("2026-12-02") == "12-01" and anchor_for("2027-01-23") == "01-22"
    assert anchor_for("2027-05-10") == "04-15" and harvest_year_of("2026-12-02") == 2027
    assert [stress_class(p) for p in (99, 90, 75, 10)] == ["severe", "high", "watch", "normal"]
    s = pd.Series(list(range(20)) + [25.0])
    pct = own_percentile(s, pd.Series([1] * 21), np.array([False] * 20 + [True]))
    assert pct.iloc[-1] == 100.0 and pct.iloc[:20].isna().all()
