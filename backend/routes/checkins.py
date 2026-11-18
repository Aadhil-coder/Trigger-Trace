from datetime import date

from flask import Blueprint, jsonify, request

from db import get_db

bp = Blueprint("checkins", __name__)


def _to_row(r):
    return {
        "id": r["id"],
        "profile_id": r["profile_id"],
        "checkin_date": r["checkin_date"],
        "had_symptoms": bool(r["had_symptoms"]),
    }


@bp.post("/checkins")
def save_checkin():
    """Evening yes/no check-in. Saving again for the same day updates the answer."""
    data = request.get_json(silent=True) or {}

    try:
        profile_id = int(data.get("profile_id", 1))
    except (TypeError, ValueError):
        return jsonify(error="profile_id must be a number"), 400

    raw_date = data.get("checkin_date") or date.today().isoformat()
    try:
        checkin_date = date.fromisoformat(raw_date).isoformat()
    except ValueError:
        return jsonify(error="checkin_date must be YYYY-MM-DD"), 400

    had_symptoms = data.get("had_symptoms")
    if not isinstance(had_symptoms, bool):
        return jsonify(error="had_symptoms must be true or false"), 400

    db = get_db()
    db.execute(
        "INSERT INTO checkins (profile_id, checkin_date, had_symptoms) VALUES (?, ?, ?) "
        "ON CONFLICT(profile_id, checkin_date) DO UPDATE SET had_symptoms = excluded.had_symptoms",
        (profile_id, checkin_date, int(had_symptoms)),
    )
    db.commit()
    row = db.execute(
        "SELECT id, profile_id, checkin_date, had_symptoms FROM checkins "
        "WHERE profile_id = ? AND checkin_date = ?",
        (profile_id, checkin_date),
    ).fetchone()
    return jsonify(_to_row(row)), 201


@bp.get("/checkins")
def list_checkins():
    """List check-ins, optionally between two dates (inclusive)."""
    try:
        profile_id = int(request.args.get("profile_id", 1))
    except ValueError:
        return jsonify(error="profile_id must be a number"), 400

    sql = ("SELECT id, profile_id, checkin_date, had_symptoms FROM checkins "
           "WHERE profile_id = ?")
    params = [profile_id]

    for arg, op in (("from", ">="), ("to", "<=")):
        value = request.args.get(arg)
        if value:
            try:
                value = date.fromisoformat(value).isoformat()
            except ValueError:
                return jsonify(error=f"{arg} must be YYYY-MM-DD"), 400
            sql += f" AND checkin_date {op} ?"
            params.append(value)

    sql += " ORDER BY checkin_date"
    rows = get_db().execute(sql, params).fetchall()
    return jsonify([_to_row(r) for r in rows])
