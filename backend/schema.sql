CREATE TABLE IF NOT EXISTS profiles (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL,
    role        TEXT NOT NULL DEFAULT 'self' CHECK (role IN ('self', 'caregiver')),
    district    TEXT,
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS attacks (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_id   INTEGER NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    attacked_at  TEXT NOT NULL,                       -- ISO 8601, local time
    district     TEXT NOT NULL,
    severity     TEXT CHECK (severity IN ('mild', 'moderate', 'severe')),
    inhaler_used INTEGER CHECK (inhaler_used IN (0, 1)),
    logged_later INTEGER NOT NULL DEFAULT 0 CHECK (logged_later IN (0, 1)),
    created_at   TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_attacks_profile_time ON attacks(profile_id, attacked_at);

CREATE TABLE IF NOT EXISTS checkins (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_id   INTEGER NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    checkin_date TEXT NOT NULL,                       -- YYYY-MM-DD
    had_symptoms INTEGER NOT NULL CHECK (had_symptoms IN (0, 1)),
    created_at   TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (profile_id, checkin_date)
);

CREATE TABLE IF NOT EXISTS environment_cache (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    district    TEXT NOT NULL,
    observed_at TEXT NOT NULL,                        -- ISO 8601, hourly
    pm2_5       REAL,
    humidity    REAL,
    temperature REAL,
    rainfall    REAL,
    source      TEXT,
    fetched_at  TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (district, observed_at)
);
