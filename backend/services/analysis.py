"""Find possible patterns between the environment and attacks.

Method
- Outcome: attack on that day (yes or no).
- Inputs: yesterday's PM2.5, plus same-day humidity, temperature and rainfall.
- Model: logistic regression with L2 regularisation on standardised inputs.
- Uncertainty: bootstrap (refit on resampled days) gives a 95% range for each odds ratio.
- Check: a plain attack-rate comparison above and below the median.

Results are always possible patterns, never causes.
"""
import math
import os

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

from services import features

PLAIN_NAMES = {
    "pm25_lag1": "PM2.5 the day before",
    "humidity": "Humidity that day",
    "temperature": "Temperature that day",
    "rainfall": "Rainfall that day",
}
DISCLAIMER = (
    "These are possible patterns, not causes and not a diagnosis. Discuss them with your doctor. "
    "During a severe attack, follow your asthma action plan or call emergency services first."
)


def _min_attacks():
    return int(os.getenv("MIN_ATTACKS", "10"))


def _min_checkin_days():
    return int(os.getenv("MIN_CHECKIN_DAYS", "30"))


def _n_boot():
    return int(os.getenv("BOOTSTRAP_RESAMPLES", "500"))


def run_analysis(profile_id):
    """Entry point used by routes/patterns.py."""
    return analyse_rows(features.build_daily_table(profile_id))


def analyse_rows(rows):
    """Run the full analysis on rows from features.make_daily_table."""
    df = pd.DataFrame(rows)
    if df.empty:
        return _not_enough(0, 0, "No records yet.")

    n_attacks = int(df["attack"].sum())
    n_checkins = int(df["checked_in"].sum())
    if n_attacks < _min_attacks() or n_checkins < _min_checkin_days():
        return _not_enough(
            n_attacks, n_checkins,
            f"Need at least {_min_attacks()} attacks and {_min_checkin_days()} check-in days "
            f"before showing patterns. Keep logging.",
        )

    data = df[df["eligible"] == 1].dropna(subset=features.FEATURES)
    if len(data) < 20 or data["attack"].nunique() < 2:
        return _not_enough(n_attacks, n_checkins, "Not enough variation in the data yet.")

    return {
        "status": "ok",
        "n_attack_days": n_attacks,
        "n_checkin_days": n_checkins,
        "unit": "odds ratio per 1 standard deviation increase in each factor",
        "confidence_note": _confidence_note(n_attacks, n_checkins),
        "factors": fit_factors(data),
        "simple_check": simple_check(data),
        "disclaimer": DISCLAIMER,
    }


def _confidence_note(n_attacks, n_checkins):
    note = (f"Based on {n_attacks} attack days and {n_checkins} check-in days. "
            "This is a possible pattern, not a cause.")
    if n_attacks < 20:
        note += " The sample is still small, so treat this as a hint to discuss with your doctor."
    return note


def _fit(X, y):
    return LogisticRegression(C=1.0, max_iter=1000).fit(X, y).coef_[0]


def _verdict(lo, hi):
    if lo > 1:
        return "possible higher risk"
    if hi < 1:
        return "possible lower risk"
    return "no clear pattern"


def fit_factors(data):
    """Odds ratios with 95% bootstrap ranges, one entry per factor."""
    X_raw = data[features.FEATURES].to_numpy(dtype=float)
    y = data["attack"].to_numpy(dtype=int)

    scaler = StandardScaler().fit(X_raw)
    X = scaler.transform(X_raw)
    coef = _fit(X, y)

    rng = np.random.default_rng(42)
    boots = []
    for _ in range(_n_boot()):
        idx = rng.integers(0, len(y), len(y))
        if y[idx].min() == y[idx].max():
            continue  # a resample with only one outcome cannot be fitted
        boots.append(_fit(X[idx], y[idx]))
    boots = np.array(boots)

    enough = len(boots) >= 50
    if enough:
        lo = np.percentile(boots, 2.5, axis=0)
        hi = np.percentile(boots, 97.5, axis=0)

    factors = []
    for i, name in enumerate(features.FEATURES):
        odds = math.exp(coef[i])
        if enough:
            odds_lo, odds_hi = math.exp(lo[i]), math.exp(hi[i])
            verdict = _verdict(odds_lo, odds_hi)
        else:
            odds_lo = odds_hi = None
            verdict = "not enough resamples to judge"
        factors.append({
            "factor": name,
            "label": PLAIN_NAMES[name],
            "odds_ratio": round(odds, 2),
            "range_low": None if odds_lo is None else round(odds_lo, 2),
            "range_high": None if odds_hi is None else round(odds_hi, 2),
            "verdict": verdict,
        })
    return factors


def simple_check(data):
    """Attack rate above and below the median, for a plain-language cross-check."""
    out = {}
    for name in ("pm25_lag1", "humidity"):
        median = data[name].median()
        high = data[data[name] > median]["attack"]
        low = data[data[name] <= median]["attack"]
        rate_high = float(high.mean()) if len(high) else None
        rate_low = float(low.mean()) if len(low) else None
        ratio = round(rate_high / rate_low, 2) if rate_high is not None and rate_low else None
        out[name] = {
            "label": PLAIN_NAMES[name],
            "attack_rate_above_median": None if rate_high is None else round(rate_high, 3),
            "attack_rate_below_median": None if rate_low is None else round(rate_low, 3),
            "rate_ratio": ratio,
        }
    return out


def _not_enough(n_attacks, n_checkins, message):
    return {
        "status": "not_enough_data",
        "n_attack_days": n_attacks,
        "n_checkin_days": n_checkins,
        "message": message,
        "factors": [],
        "disclaimer": DISCLAIMER,
    }
