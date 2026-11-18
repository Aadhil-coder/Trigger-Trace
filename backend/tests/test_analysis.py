"""Tests for services/analysis.py: thresholds, verdicts, and whether the method finds a planted pattern.

These tests use plain Python data only, so they need no database or internet.
Run from the backend folder:  python -m pytest tests -v
"""
import csv
import math
import os
import random
from datetime import date, timedelta

# Keep the tests fast and the thresholds fixed, whatever is in .env.
os.environ["MIN_ATTACKS"] = "10"
os.environ["MIN_CHECKIN_DAYS"] = "30"
os.environ["BOOTSTRAP_RESAMPLES"] = "200"

from services import analysis, features  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
SAMPLE_CSV = os.path.join(HERE, "..", "..", "data", "synthetic_sample.csv")
ALLOWED_VERDICTS = {"possible higher risk", "possible lower risk", "no clear pattern"}


def make_rows(records):
    """Turn day records into the table the analysis reads.

    Each record: date, pm2_5, humidity, temperature, rainfall, attack (0/1),
    checked_in (0/1), had_symptoms (0/1, ignored when not checked in).
    """
    attack_dates = {r["date"] for r in records if r["attack"] == 1}
    checkins = {r["date"]: bool(r["had_symptoms"]) for r in records if r["checked_in"] == 1}
    env = {
        r["date"]: {"pm2_5": r["pm2_5"], "humidity": r["humidity"],
                    "temperature": r["temperature"], "rainfall": r["rainfall"]}
        for r in records
    }
    return features.make_daily_table(attack_dates, checkins, env)


def planted_records(n_days, seed=1, effect=0.07):
    """Synthetic days where attack risk rises with yesterday's PM2.5 (about 2.3 times per standard deviation)."""
    rng = random.Random(seed)
    start = date(2026, 1, 1)
    records, prev_pm = [], 35.0
    for i in range(n_days):
        pm = rng.gauss(35, 12)
        logit = -1.2 + effect * (prev_pm - 35)
        attack = 1 if rng.random() < 1 / (1 + math.exp(-logit)) else 0
        records.append({
            "date": (start + timedelta(days=i)).isoformat(),
            "pm2_5": pm,
            "humidity": rng.gauss(60, 10),
            "temperature": rng.gauss(30, 2.5),
            "rainfall": max(0.0, rng.gauss(1, 1)),
            "attack": attack,
            "checked_in": 1,
            "had_symptoms": attack,
        })
        prev_pm = pm
    return records


def load_sample_csv():
    with open(SAMPLE_CSV, newline="", encoding="utf-8") as f:
        raw = list(csv.DictReader(f))
    return [
        {
            "date": r["date"],
            "pm2_5": float(r["pm2_5"]),
            "humidity": float(r["humidity"]),
            "temperature": float(r["temperature"]),
            "rainfall": float(r["rainfall"]),
            "attack": int(r["attack"]),
            "checked_in": int(r["checked_in"]),
            "had_symptoms": int(r["had_symptoms"]) if r["had_symptoms"] else 0,
        }
        for r in raw
    ]


# ---------- verdict rules ----------

def test_verdict_higher_risk_when_range_is_above_one():
    assert analysis._verdict(1.2, 2.0) == "possible higher risk"


def test_verdict_lower_risk_when_range_is_below_one():
    assert analysis._verdict(0.5, 0.9) == "possible lower risk"


def test_verdict_no_clear_pattern_when_range_crosses_one():
    assert analysis._verdict(0.8, 1.5) == "no clear pattern"


# ---------- thresholds ----------

def test_too_few_attacks_gives_not_enough_data():
    records = planted_records(200)
    for r in records:
        r["attack"] = 0
        r["had_symptoms"] = 0
    for r in records[:5]:
        r["attack"] = 1
        r["had_symptoms"] = 1
    result = analysis.analyse_rows(make_rows(records))
    assert result["status"] == "not_enough_data"
    assert "Need at least 10 attacks" in result["message"]
    assert result["factors"] == []


def test_too_few_checkin_days_gives_not_enough_data():
    records = planted_records(200)
    for i, r in enumerate(records):
        r["checked_in"] = 1 if i < 20 else 0  # only 20 check-in days
    result = analysis.analyse_rows(make_rows(records))
    assert result["status"] == "not_enough_data"
    assert "30 check-in days" in result["message"]


def test_empty_input_gives_not_enough_data():
    result = analysis.analyse_rows([])
    assert result["status"] == "not_enough_data"


# ---------- method ----------

def test_planted_pm25_pattern_is_recovered():
    result = analysis.analyse_rows(make_rows(planted_records(300)))
    assert result["status"] == "ok"
    pm = next(f for f in result["factors"] if f["factor"] == "pm25_lag1")
    assert pm["verdict"] == "possible higher risk"
    assert pm["odds_ratio"] > 1.5
    assert pm["range_low"] > 1


def test_result_has_expected_structure():
    result = analysis.analyse_rows(make_rows(planted_records(300)))
    assert [f["factor"] for f in result["factors"]] == features.FEATURES
    for f in result["factors"]:
        assert f["verdict"] in ALLOWED_VERDICTS
        assert f["range_low"] <= f["odds_ratio"] <= f["range_high"]
    assert "not a cause" in result["confidence_note"]
    assert "not a diagnosis" in result["disclaimer"]
    assert set(result["simple_check"]) == {"pm25_lag1", "humidity"}


def test_results_are_repeatable():
    rows = make_rows(planted_records(300))
    first = analysis.analyse_rows(rows)["factors"]
    second = analysis.analyse_rows(rows)["factors"]
    assert first == second


def test_small_sample_adds_a_caution_to_the_note():
    records = planted_records(60, seed=3)
    result = analysis.analyse_rows(make_rows(records))
    if result["status"] == "ok" and result["n_attack_days"] < 20:
        assert "sample is still small" in result["confidence_note"]


# ---------- the demo data ----------

def test_synthetic_sample_csv_runs_and_matches_generator_counts():
    # Counts match data/generate_synthetic.py. If you regenerate the data, update these.
    result = analysis.analyse_rows(make_rows(load_sample_csv()))
    assert result["status"] == "ok"
    assert result["n_attack_days"] == 16
    assert result["n_checkin_days"] == 75


def test_synthetic_sample_shows_the_planted_pm25_effect_in_the_simple_check():
    result = analysis.analyse_rows(make_rows(load_sample_csv()))
    pm_check = result["simple_check"]["pm25_lag1"]
    assert pm_check["rate_ratio"] is not None
    assert pm_check["rate_ratio"] > 1
