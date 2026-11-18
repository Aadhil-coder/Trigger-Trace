#!/usr/bin/env python3
"""Load the synthetic demo data into the TriggerTrace database.

Run from the data/ folder:
    python load_demo.py            load the demo (safe to run once; refuses to duplicate)
    python load_demo.py --reset    clear the demo profile's records, then load again

Reads:
    synthetic_sample.csv                      daily attacks and check-ins
    cache/synthetic_environment_hourly.csv    hourly air and weather

Writes to the database:
    profile 1 "Demo user" with district "Coimbatore (synthetic)"
    attacks, checkins, environment_cache
"""
import argparse
import csv
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "backend"))

from app import app  # noqa: E402  (also creates the tables)
from db import get_db  # noqa: E402

DEMO_PROFILE_ID = 1
DEMO_NAME = "Demo user"
DAILY_CSV = os.path.join(HERE, "synthetic_sample.csv")
HOURLY_CSV = os.path.join(HERE, "cache", "synthetic_environment_hourly.csv")
SEVERITIES = ["mild", "moderate", "severe"]
ATTACK_HOUR = 14  # synthetic attacks are placed at 14:00


def read_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def demo_attack_count(db):
    return db.execute(
        "SELECT COUNT(*) FROM attacks WHERE profile_id = ?", (DEMO_PROFILE_ID,)
    ).fetchone()[0]


def reset(db):
    db.execute("DELETE FROM attacks WHERE profile_id = ?", (DEMO_PROFILE_ID,))
    db.execute("DELETE FROM checkins WHERE profile_id = ?", (DEMO_PROFILE_ID,))
    db.execute("DELETE FROM environment_cache WHERE source = 'synthetic'")


def ensure_profile(db, district):
    db.execute(
        "INSERT OR IGNORE INTO profiles (id, name, role, district) VALUES (?, ?, 'self', ?)",
        (DEMO_PROFILE_ID, DEMO_NAME, district),
    )
    db.execute(
        "UPDATE profiles SET name = ?, district = ? WHERE id = ?",
        (DEMO_NAME, district, DEMO_PROFILE_ID),
    )


def load_environment(db):
    rows = read_csv(HOURLY_CSV)
    db.executemany(
        "INSERT OR REPLACE INTO environment_cache "
        "(district, observed_at, pm2_5, humidity, temperature, rainfall, source) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        [
            (
                r["district"],
                r["observed_at"],
                float(r["pm2_5"]),
                float(r["humidity"]),
                float(r["temperature"]),
                float(r["rainfall"]),
                r["source"],
            )
            for r in rows
        ],
    )
    return len(rows), rows[0]["district"]


def load_daily(db, district):
    attacks = checkins = 0
    for r in read_csv(DAILY_CSV):
        day = r["date"]

        if r["checked_in"] == "1":
            db.execute(
                "INSERT OR REPLACE INTO checkins (profile_id, checkin_date, had_symptoms) VALUES (?, ?, ?)",
                (DEMO_PROFILE_ID, day, int(r["had_symptoms"])),
            )
            checkins += 1

        if r["attack"] == "1":
            severity = SEVERITIES[attacks % len(SEVERITIES)]
            inhaler = 0 if severity == "mild" else 1
            db.execute(
                "INSERT INTO attacks (profile_id, attacked_at, district, severity, inhaler_used, logged_later) "
                "VALUES (?, ?, ?, ?, ?, 0)",
                (DEMO_PROFILE_ID, f"{day}T{ATTACK_HOUR:02d}:00:00", district, severity, inhaler),
            )
            attacks += 1
    return attacks, checkins


def main():
    parser = argparse.ArgumentParser(description="Load the TriggerTrace synthetic demo data.")
    parser.add_argument("--reset", action="store_true", help="clear the demo records before loading")
    args = parser.parse_args()

    with app.app_context():
        db = get_db()

        if args.reset:
            reset(db)
        elif demo_attack_count(db) > 0:
            print("Demo data is already loaded. Run with --reset to load it again.")
            return

        hourly_count, district = load_environment(db)
        ensure_profile(db, district)
        attacks, checkins = load_daily(db, district)
        db.commit()

    print(f"Loaded demo profile {DEMO_PROFILE_ID} ({DEMO_NAME}, {district}):")
    print(f"  attacks:          {attacks}")
    print(f"  check-in days:    {checkins}")
    print(f"  hourly env rows:  {hourly_count}")
    print("Next: start the server and open /api/patterns?profile_id=1")


if __name__ == "__main__":
    main()
