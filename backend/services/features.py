"""Turn raw records into one row per day for the analysis.

A day is used in the analysis only if its outcome is known:
- it had an attack, or
- the user checked in and reported no symptoms.

Days with no check-in and no attack are left out. They are never assumed to be symptom-free.
"""
import os
from datetime import date, timedelta

from db import get_db
from services import environment

# Inputs to the model. pm25_lag1 is yesterday's PM2.5; the rest are same-day values.
FEATURES = ["pm25_lag1", "humidity", "temperature", "rainfall"]


def make_daily_table(attack_dates, checkins, env_daily):
    """Build one row per day from plain Python data. Easy to test with the synthetic CSV.

    attack_dates: set of 'YYYY-MM-DD' strings with at least one attack
    checkins:     dict 'YYYY-MM-DD' -> had_symptoms (bool)
    env_daily:    dict 'YYYY-MM-DD' -> {pm2_5, humidity, temperature, rainfall}
    """
    all_days = set(attack_dates) | set(checkins) | set(env_daily)
    if not all_days:
        return []

    day = date.fromisoformat(min(all_days))
    last = date.fromisoformat(max(all_days))
    rows = []
    while day <= last:
        key = day.isoformat()
        env = env_daily.get(key, {})
        prev = env_daily.get((day - timedelta(days=1)).isoformat(), {})

        attack = 1 if key in attack_dates else 0
        checked_in = key in checkins
        symptom_free = checked_in and not checkins[key] and not attack

        rows.append({
            "date": key,
            "attack": attack,
            "checked_in": int(checked_in),
            "symptom_free": int(symptom_free),
            "eligible": int(attack == 1 or symptom_free),
            "pm25_lag1": prev.get("pm2_5"),
            "humidity": env.get("humidity"),
            "temperature": env.get("temperature"),
            "rainfall": env.get("rainfall"),
        })
        day += timedelta(days=1)
    return rows


def _daily_means(hourly):
    """Average the hourly rows for each day. Rainfall is summed."""
    by_day = {}
    for r in hourly:
        by_day.setdefault(r["observed_at"][:10], []).append(r)

    def mean(rs, key):
        vals = [r[key] for r in rs if r[key] is not None]
        return round(sum(vals) / len(vals), 2) if vals else None

    out = {}
    for day, rs in by_day.items():
        rain = [r["rainfall"] for r in rs if r["rainfall"] is not None]
        out[day] = {
            "pm2_5": mean(rs, "pm2_5"),
            "humidity": mean(rs, "humidity"),
            "temperature": mean(rs, "temperature"),
            "rainfall": round(sum(rain), 2) if rain else None,
        }
    return out


def build_daily_table(profile_id):
    """Read a profile's attacks and check-ins from the database, add environment data, and build the table."""
    db = get_db()
    profile = db.execute("SELECT district FROM profiles WHERE id = ?", (profile_id,)).fetchone()
    if profile is None:
        raise LookupError(f"profile {profile_id} not found")
    district = profile["district"] or os.getenv("DEFAULT_DISTRICT") or "default"

    attack_dates = {
        r["attacked_at"][:10]
        for r in db.execute("SELECT attacked_at FROM attacks WHERE profile_id = ?", (profile_id,))
    }
    checkins = {
        r["checkin_date"]: bool(r["had_symptoms"])
        for r in db.execute(
            "SELECT checkin_date, had_symptoms FROM checkins WHERE profile_id = ?", (profile_id,)
        )
    }
    if not attack_dates and not checkins:
        return []

    known_days = attack_dates | set(checkins)
    start = date.fromisoformat(min(known_days)) - timedelta(days=1)  # one extra day for the lag
    end = date.fromisoformat(max(known_days))
    env_daily = _daily_means(environment.get_hourly(district, start, end))

    return make_daily_table(attack_dates, checkins, env_daily)
