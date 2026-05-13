"""Unit tests for TQS sub-score functions.

These exercise the pure functions only — no DB. The orchestrator
compute_trip_quality_daily is tested indirectly via the materialized
view tests in a later phase.
"""

from datetime import date

from pipeline.predictions.trip_quality import (
    W_V05,
    access_score,
    apply_seasonal_modifier,
    catch_score,
    confidence,
    flow_score,
    hatch_score,
    primary_factor,
    proxy_water_temp_f,
    water_temp_score,
)


# ─── water_temp_score ───────────────────────────────────────────────────────

def test_water_temp_score_trout_ideal():
    assert water_temp_score(55) == 100
    assert water_temp_score(50) == 100
    assert water_temp_score(60) == 100


def test_water_temp_score_trout_hard_floors():
    assert water_temp_score(70) == 0   # ODFW hoot-owl threshold
    assert water_temp_score(40) == 0
    assert water_temp_score(75) == 0
    assert water_temp_score(35) == 0


def test_water_temp_score_trout_marginal():
    # 65°F is 5° above ideal → loses 50 pts at slope 10/°F
    assert water_temp_score(65) == 50
    # 45°F is 5° below ideal → 50
    assert water_temp_score(45) == 50


def test_water_temp_score_warm_water():
    assert water_temp_score(68, is_warm_water=True) == 100
    assert water_temp_score(85, is_warm_water=True) == 0
    assert water_temp_score(32, is_warm_water=True) == 0
    assert water_temp_score(78, is_warm_water=True) < 100   # above ideal but not lethal


def test_water_temp_score_none_returns_neutral():
    assert water_temp_score(None) == 50


# ─── flow_score ─────────────────────────────────────────────────────────────

def test_flow_score_inside_ideal_returns_100():
    assert flow_score(1500, low=500, ideal_low=1000, ideal_high=2000, high=4000) == 100
    assert flow_score(1000, low=500, ideal_low=1000, ideal_high=2000, high=4000) == 100
    assert flow_score(2000, low=500, ideal_low=1000, ideal_high=2000, high=4000) == 100


def test_flow_score_blown_out_returns_0():
    assert flow_score(5000, low=500, ideal_low=1000, ideal_high=2000, high=4000) == 0
    assert flow_score(100, low=500, ideal_low=1000, ideal_high=2000, high=4000) == 0


def test_flow_score_below_ideal_decays_linearly():
    # cfs=750 is halfway between low(500) and ideal_low(1000) → 50
    assert flow_score(750, low=500, ideal_low=1000, ideal_high=2000, high=4000) == 50


def test_flow_score_above_ideal_decays_linearly():
    # cfs=3000 is halfway between ideal_high(2000) and high(4000) → 50
    assert flow_score(3000, low=500, ideal_low=1000, ideal_high=2000, high=4000) == 50


# ─── hatch_score ────────────────────────────────────────────────────────────

def test_hatch_score_inside_window_returns_100():
    assert hatch_score(date(2026, 6, 15), [(5, 9)]) == 100


def test_hatch_score_no_windows_returns_baseline():
    assert hatch_score(date(2026, 6, 15), []) == 30


def test_hatch_score_decays_outside_window():
    # Window May-Sep (5-9); January target is 4 months from window edge
    s = hatch_score(date(2026, 1, 15), [(5, 9)])
    assert s < 100 and s >= 0


# ─── access_score ───────────────────────────────────────────────────────────

def test_access_score_fire_intersects_hard_closes():
    s, hard, partial = access_score(active_fire_intersects=True, regulation_closed=False)
    assert s == 0
    assert hard is True


def test_access_score_regulation_closed_hard_closes():
    s, hard, partial = access_score(False, regulation_closed=True)
    assert s == 0
    assert hard is True


def test_access_score_partial_does_not_hard_close():
    s, hard, partial = access_score(False, False, partial_access=True)
    assert s == 80
    assert hard is False
    assert partial is True


def test_access_score_open_returns_100():
    s, hard, partial = access_score(False, False)
    assert s == 100
    assert hard is False


# ─── confidence ─────────────────────────────────────────────────────────────

def test_confidence_today_is_high():
    today = date(2026, 5, 13)
    assert confidence(today, today) >= 95


def test_confidence_decays_with_horizon():
    today = date(2026, 5, 13)
    c7 = confidence(today.replace(day=20), today)
    c30 = confidence(date(2026, 6, 12), today)
    assert c7 > c30


def test_confidence_floors_at_20():
    today = date(2026, 5, 13)
    assert confidence(date(2027, 5, 13), today) == 20  # 365 days out


# ─── primary_factor ─────────────────────────────────────────────────────────

def test_primary_factor_picks_largest_weighted_gap():
    # catch=60 (gap 40), water_temp=65 (gap 35); weights equal → catch wins on raw gap
    weights = {k: 1.0 for k in ("catch", "water_temp", "flow", "hatch", "access")}
    scores = {"catch": 60, "water_temp": 65, "flow": 100, "hatch": 100, "access": 100}
    assert primary_factor(weights, scores) == "catch"


def test_primary_factor_respects_weights():
    # When weather (low score) carries higher weight, it dominates
    weights = {"catch": 0.1, "water_temp": 0.5, "flow": 0.1, "hatch": 0.1, "access": 0.1}
    scores = {"catch": 50, "water_temp": 70, "flow": 100, "hatch": 100, "access": 100}
    # gap*w: catch=50*0.1=5, water_temp=30*0.5=15 — water_temp wins
    assert primary_factor(weights, scores) == "water_temp"


# ─── seasonal modifier ─────────────────────────────────────────────────────

def test_seasonal_modifier_summer_dry_fly():
    mods = [{
        "season_label": "dry_fly_summer", "month_start": 6, "month_end": 9,
        "applies_to_species": None,
        "w_catch_delta": -0.05, "w_water_temp_delta": 0, "w_flow_delta": 0,
        "w_weather_delta": 0, "w_hatch_delta": 0.05, "w_access_delta": 0,
    }]
    base = {"catch": 0.30, "water_temp": 0.175, "flow": 0.175, "hatch": 0.175, "access": 0.175}
    out = apply_seasonal_modifier(base, date(2026, 7, 15), mods, [])
    assert out["catch"] < base["catch"]
    assert out["hatch"] > base["hatch"]


def test_seasonal_modifier_skips_when_species_does_not_match():
    mods = [{
        "season_label": "winter_steelhead", "month_start": 12, "month_end": 2,
        "applies_to_species": ["steelhead"],
        "w_catch_delta": 0.10, "w_water_temp_delta": 0, "w_flow_delta": 0,
        "w_weather_delta": 0, "w_hatch_delta": -0.10, "w_access_delta": 0,
    }]
    base = {"catch": 0.30, "water_temp": 0.175, "flow": 0.175, "hatch": 0.175, "access": 0.175}
    # Trout-only reach in January → modifier should not apply
    out = apply_seasonal_modifier(base, date(2026, 1, 15), mods, ["rainbow_trout"])
    assert out == base


def test_seasonal_modifier_wraps_year():
    mods = [{
        "season_label": "winter_steelhead", "month_start": 12, "month_end": 2,
        "applies_to_species": None,
        "w_catch_delta": 0.10, "w_water_temp_delta": 0, "w_flow_delta": 0,
        "w_weather_delta": 0, "w_hatch_delta": -0.10, "w_access_delta": 0,
    }]
    base = {"catch": 0.30, "water_temp": 0.175, "flow": 0.175, "hatch": 0.175, "access": 0.175}
    out = apply_seasonal_modifier(base, date(2026, 1, 15), mods, [])
    assert out["catch"] > base["catch"]


# ─── catch_score stub ──────────────────────────────────────────────────────

def test_catch_score_with_prediction_higher():
    assert catch_score(True) > catch_score(False)


# ─── proxy water temp ──────────────────────────────────────────────────────

def test_proxy_water_temp_warmer_in_summer():
    summer = proxy_water_temp_f(date(2026, 7, 15), lat=44.0)
    winter = proxy_water_temp_f(date(2026, 1, 15), lat=44.0)
    assert summer > winter


def test_proxy_water_temp_colder_at_higher_latitudes():
    pnw = proxy_water_temp_f(date(2026, 7, 15), lat=48.0)
    utah = proxy_water_temp_f(date(2026, 7, 15), lat=40.0)
    assert pnw < utah
