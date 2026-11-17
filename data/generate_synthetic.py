"""
TriggerTrace: generate 90 days of SYNTHETIC asthma and environment data.

Outputs (paths are relative to this file):
  synthetic_sample.csv                          one row per day (for the analysis)
  cache/synthetic_environment_hourly.csv        hourly air and weather (for the cache)

Uses only the Python standard library, so it runs in Termux.
No real patient data is used or produced.

Run:  python generate_synthetic.py
"""
import csv
import math
import os
import random
from datetime import date, datetime, timedelta

SEED = 42
DAYS = 90
START = date(2026, 8, 1)
DISTRICT = "Coimbatore (synthetic)"

# Planted ("true") pattern the analysis should recover.
# Attack risk rises with yesterday's PM2.5 and with humidity.
# Temperature is included as a control with NO effect.
INTERCEPT = -1.4
PM25_EFFECT = 0.035      # per ug/m3 of yesterday's mean PM2.5 above 35
HUMIDITY_EFFECT = 0.03   # per % of humidity above 60
TEMP_EFFECT = 0.0        # deliberately zero

CHECKIN_RATE = 0.8       # share of days with a completed check-in
MILD_SYMPTOM_RATE = 0.04 # symptoms on non-attack days (cough, tightness)

HERE = os.path.dirname(os.path.abspath(__file__))
DAILY_OUT = os.path.join(HERE, "synthetic_sample.csv")
HOURLY_OUT = os.path.join(HERE, "cache", "synthetic_environment_hourly.csv")


def sigmoid(x):
    return 1.0 / (1.0 + math.exp(-x))


def clip(x, lo, hi):
    return max(lo, min(hi, x))


def make_hourly(rng):
    """Hourly PM2.5, humidity, temperature and rainfall for every day."""
    rows = []
    for d in range(DAYS):
        day = START + timedelta(days=d)
        # Day-level baselines with a seasonal drift and random weather
        pm_base = clip(rng.gauss(35, 12) + 3 * math.sin(d / 9), 8, 120)
        hum_base = clip(rng.gauss(60, 10), 35, 95)
        temp_base = clip(rng.gauss(30, 2.5), 22, 38)
        rain_day = rng.random() < 0.3
        for h in range(24):
            ts = datetime(day.year, day.month, day.day, h)
            # Diurnal patterns: hotter and drier in the afternoon, dust peaks at rush hours
            diurnal_temp = 3.0 * math.sin((h - 9) / 24 * 2 * math.pi)
            diurnal_hum = -8.0 * math.sin((h - 9) / 24 * 2 * math.pi)
            rush = 6.0 if h in (8, 9, 18, 19) else 0.0
            rows.append({
                "district": DISTRICT,
                "observed_at": ts.isoformat(),
                "pm2_5": round(clip(pm_base + rush + rng.gauss(0, 3), 3, 200), 1),
                "humidity": round(clip(hum_base + diurnal_hum + rng.gauss(0, 3), 20, 100), 1),
                "temperature": round(temp_base + diurnal_temp + rng.gauss(0, 0.8), 1),
                "rainfall": round(max(0.0, rng.gauss(1.5, 1.0)) if rain_day and 12 <= h <= 18 else 0.0, 1),
                "source": "synthetic",
            })
    return rows


def daily_from_hourly(hourly):
    """Aggregate hourly rows into one row per day."""
    by_day = {}
    for r in hourly:
        key = r["observed_at"][:10]
        by_day.setdefault(key, []).append(r)
    daily = []
    for key in sorted(by_day):
        rs = by_day[key]
        n = len(rs)
        daily.append({
            "date": key,
            "pm2_5": round(sum(r["pm2_5"] for r in rs) / n, 2),
            "humidity": round(sum(r["humidity"] for r in rs) / n, 2),
            "temperature": round(sum(r["temperature"] for r in rs) / n, 2),
            "rainfall": round(sum(r["rainfall"] for r in rs), 2),
        })
    return daily


def add_outcomes(daily, rng):
    """Attack, check-in and symptom columns, driven by the planted pattern."""
    for i, row in enumerate(daily):
        # Use yesterday's PM2.5 (lag 1). Day 0 uses its own value as a stand-in.
        pm_prev = daily[i - 1]["pm2_5"] if i > 0 else row["pm2_5"]
        logit = (INTERCEPT
                 + PM25_EFFECT * (pm_prev - 35)
                 + HUMIDITY_EFFECT * (row["humidity"] - 60)
                 + TEMP_EFFECT * (row["temperature"] - 30))
        attack = 1 if rng.random() < sigmoid(logit) else 0
        checked_in = 1 if rng.random() < CHECKIN_RATE else 0
        if attack:
            symptoms = 1
        else:
            symptoms = 1 if rng.random() < MILD_SYMPTOM_RATE else 0
        row["attack"] = attack
        row["checked_in"] = checked_in
        # Symptom status is only known if the user checked in
        row["had_symptoms"] = symptoms if checked_in else ""
    return daily


def write_csv(path, rows, fields):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def main():
    rng = random.Random(SEED)
    hourly = make_hourly(rng)
    daily = add_outcomes(daily_from_hourly(hourly), rng)

    write_csv(HOURLY_OUT, hourly,
              ["district", "observed_at", "pm2_5", "humidity", "temperature", "rainfall", "source"])
    write_csv(DAILY_OUT, daily,
              ["date", "pm2_5", "humidity", "temperature", "rainfall", "attack", "checked_in", "had_symptoms"])

    attacks = sum(r["attack"] for r in daily)
    checkins = sum(r["checked_in"] for r in daily)
    symptom_free = sum(1 for r in daily if r["checked_in"] == 1 and r["had_symptoms"] == 0)
    print(f"Days: {len(daily)}")
    print(f"Attack days: {attacks}   (need >= 10 to show a pattern)")
    print(f"Check-in days: {checkins}   (need >= 30 to show a pattern)")
    print(f"Symptom-free check-in days: {symptom_free}")
    print(f"Wrote {DAILY_OUT}")
    print(f"Wrote {HOURLY_OUT}")


if __name__ == "__main__":
    main()
  
