"""Fetch, cache and read hourly air-quality and weather data.

Order of use:
1. Look in the environment_cache table first.
2. If hours are missing, fetch them from Open-Meteo and store them.
3. Save each raw response in CACHE_DIR, so the demo can replay it offline.

Set USE_CACHE_ONLY=1 in .env to never call the internet.
"""
import json
import os
from datetime import timedelta

import requests

import config  # loads .env
from db import get_db

WEATHER_URL = os.getenv("OPEN_METEO_WEATHER_URL", "https://archive-api.open-meteo.com/v1/archive")
AIR_URL = os.getenv("OPEN_METEO_AIR_QUALITY_URL", "https://air-quality-api.open-meteo.com/v1/air-quality")
CACHE_DIR = os.path.join(config.BASE_DIR, "..", os.getenv("CACHE_DIR", "data/cache"))


def _use_cache_only():
    return os.getenv("USE_CACHE_ONLY", "0") == "1"


def _hour_key(t):
    """Open-Meteo gives '2026-08-01T00:00'. Store it as '2026-08-01T00:00:00'."""
    return t if len(t) == 19 else t + ":00"


def _load_cached(district, start, end):
    return get_db().execute(
        "SELECT observed_at, pm2_5, humidity, temperature, rainfall FROM environment_cache "
        "WHERE district = ? AND observed_at >= ? AND observed_at < ? ORDER BY observed_at",
        (district, f"{start.isoformat()}T00:00:00", f"{(end + timedelta(days=1)).isoformat()}T00:00:00"),
    ).fetchall()


def _fetch_remote(lat, lon, start, end):
    common = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "timezone": "auto",
    }
    weather = requests.get(WEATHER_URL, params={**common, "hourly": "temperature_2m,relative_humidity_2m,rain"}, timeout=30)
    weather.raise_for_status()
    air = requests.get(AIR_URL, params={**common, "hourly": "pm2_5"}, timeout=30)
    air.raise_for_status()
    return weather.json(), air.json()


def _at(values, i):
    return values[i] if values and i < len(values) else None


def _to_rows(district, weather, air):
    w = weather.get("hourly", {})
    a = air.get("hourly", {})
    air_by_time = dict(zip(a.get("time", []), a.get("pm2_5", [])))
    rows = []
    for i, t in enumerate(w.get("time", [])):
        rows.append((
            district,
            _hour_key(t),
            air_by_time.get(t),
            _at(w.get("relative_humidity_2m"), i),
            _at(w.get("temperature_2m"), i),
            _at(w.get("rain"), i),
            "open-meteo",
        ))
    return rows


def _save_raw(name, payload):
    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(os.path.join(CACHE_DIR, name), "w", encoding="utf-8") as f:
        json.dump(payload, f)


def get_hourly(district, start, end, lat=None, lon=None):
    """Return hourly rows between two dates (inclusive), fetching any gaps first.

    Each row is a dict with observed_at, pm2_5, humidity, temperature and rainfall.
    If the internet fails, the cached rows are returned instead.
    """
    expected = ((end - start).days + 1) * 24
    rows = _load_cached(district, start, end)

    if len(rows) < expected and not _use_cache_only():
        lat = lat if lat is not None else os.getenv("DEFAULT_LATITUDE")
        lon = lon if lon is not None else os.getenv("DEFAULT_LONGITUDE")
        if not lat or not lon:
            raise RuntimeError("Set DEFAULT_LATITUDE and DEFAULT_LONGITUDE in .env to fetch data.")
        try:
            weather, air = _fetch_remote(float(lat), float(lon), start, end)
        except requests.RequestException as err:
            print(f"Environment fetch failed, using cache only: {err}")
        else:
            slug = district.lower().replace(" ", "_")
            _save_raw(f"open_meteo_{slug}_{start}_{end}.json", {"weather": weather, "air": air})
            db = get_db()
            db.executemany(
                "INSERT OR REPLACE INTO environment_cache "
                "(district, observed_at, pm2_5, humidity, temperature, rainfall, source) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                _to_rows(district, weather, air),
            )
            db.commit()
            rows = _load_cached(district, start, end)

    return [dict(r) for r in rows]
