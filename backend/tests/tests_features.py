"""Tests for services/features.py: the daily table and the hourly-to-daily averages.

These tests use plain Python data only, so they need no database or internet.
Run from the backend folder:  python -m pytest tests -v
"""
from services import features


def _env(pm2_5, humidity=50.0, temperature=30.0, rainfall=0.0):
    return {"pm2_5": pm2_5, "humidity": humidity, "temperature": temperature, "rainfall": rainfall}


def _by_date(rows):
    return {r["date"]: r for r in rows}


def test_no_data_gives_no_rows():
    assert features.make_daily_table(set(), {}, {}) == []


def test_checked_in_without_symptoms_is_symptom_free_and_eligible():
    rows = _by_date(features.make_daily_table(set(), {"2026-08-01": False}, {"2026-08-01": _env(10)}))
    day = rows["2026-08-01"]
    assert day["checked_in"] == 1
    assert day["symptom_free"] == 1
    assert day["eligible"] == 1


def test_checked_in_with_symptoms_is_not_eligible_without_attack():
    rows = _by_date(features.make_daily_table(set(), {"2026-08-02": True}, {"2026-08-02": _env(10)}))
    day = rows["2026-08-02"]
    assert day["symptom_free"] == 0
    assert day["eligible"] == 0


def test_day_with_no_checkin_and_no_attack_is_never_assumed_symptom_free():
    rows = _by_date(features.make_daily_table(set(), {}, {"2026-08-03": _env(10)}))
    day = rows["2026-08-03"]
    assert day["checked_in"] == 0
    assert day["symptom_free"] == 0
    assert day["eligible"] == 0


def test_attack_day_is_eligible_even_without_a_checkin():
    rows = _by_date(features.make_daily_table({"2026-08-04"}, {}, {"2026-08-04": _env(10)}))
    day = rows["2026-08-04"]
    assert day["attack"] == 1
    assert day["checked_in"] == 0
    assert day["eligible"] == 1


def test_attack_day_is_not_symptom_free_even_if_checkin_says_no_symptoms():
    rows = _by_date(features.make_daily_table({"2026-08-05"}, {"2026-08-05": False}, {"2026-08-05": _env(10)}))
    day = rows["2026-08-05"]
    assert day["attack"] == 1
    assert day["symptom_free"] == 0
    assert day["eligible"] == 1


def test_pm25_lag1_is_the_previous_days_value():
    env = {"2026-08-01": _env(10), "2026-08-02": _env(20), "2026-08-03": _env(30)}
    rows = _by_date(features.make_daily_table(set(), {}, env))
    assert rows["2026-08-02"]["pm25_lag1"] == 10
    assert rows["2026-08-03"]["pm25_lag1"] == 20


def test_first_day_has_no_lag_value():
    env = {"2026-08-01": _env(10), "2026-08-02": _env(20)}
    rows = _by_date(features.make_daily_table(set(), {}, env))
    assert rows["2026-08-01"]["pm25_lag1"] is None


def test_rows_cover_every_day_between_first_and_last_date():
    env = {"2026-08-01": _env(10), "2026-08-04": _env(40)}
    rows = features.make_daily_table({"2026-08-02"}, {}, env)
    dates = [r["date"] for r in rows]
    assert dates == ["2026-08-01", "2026-08-02", "2026-08-03", "2026-08-04"]


def test_same_day_environment_values_are_copied_to_the_row():
    env = {"2026-08-01": _env(10, humidity=72.5, temperature=31.0, rainfall=4.2)}
    day = _by_date(features.make_daily_table(set(), {}, env))["2026-08-01"]
    assert day["humidity"] == 72.5
    assert day["temperature"] == 31.0
    assert day["rainfall"] == 4.2


def test_daily_means_average_hourly_values_and_sum_rain():
    hourly = [
        {"observed_at": "2026-08-01T00:00:00", "pm2_5": 10.0, "humidity": 50.0, "temperature": 28.0, "rainfall": 0.0},
        {"observed_at": "2026-08-01T01:00:00", "pm2_5": 20.0, "humidity": 70.0, "temperature": 30.0, "rainfall": 1.5},
        {"observed_at": "2026-08-02T00:00:00", "pm2_5": None, "humidity": None, "temperature": None, "rainfall": None},
    ]
    daily = features._daily_means(hourly)
    assert daily["2026-08-01"]["pm2_5"] == 15.0
    assert daily["2026-08-01"]["humidity"] == 60.0
    assert daily["2026-08-01"]["temperature"] == 29.0
    assert daily["2026-08-01"]["rainfall"] == 1.5
    assert daily["2026-08-02"]["pm2_5"] is None
