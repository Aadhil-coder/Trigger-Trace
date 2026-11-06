from datetime import datetime

from flask import Blueprint, jsonify, request

from db import get_db

bp = Blueprint("attacks", __name__)
SEVERITIES = {"mild", "moderate", "severe"}


@bp.post("/attacks")
def create_attack():
    """One-tap log. Only district is required; time defaults to now."""
    data = request.get_json(silent=True) or {}
    district = (data.get("district") or "").strip()
    if not district:
        return jsonify(error="district is required"), 400

    try:
        profile_id = int(data.get("profile_id", 1))
    except (TypeError, ValueError):
        return jsonify(error="profile_id must be a number"), 400

    logged_later = 0
    if data.get("attacked_at"):  # back-dated entry
        try:
            ts = datetime.fromisoformat(data["attacked_at"])
        except ValueError:
            return jsonify(error="attacked_at must be ISO 8601, e.g. 2026-11-06T18:00"), 400
        logged_later = 1
    else:
        ts = datetime.now().replace(microsecond=0)

    db = get_db()
    cur = db.execute(
        "INSERT INTO attacks (profile_id, attacked_at, district, logged_later) VALUES (?, ?, ?, ?)",
        (profile_id, ts.isoformat(), district, logged_later),
    )
    db.commit()
    return jsonify(
        id=cur.lastrowid,
        attacked_at=ts.isoformat(),
        district=district,
        logged_later=bool(logged_later),
    ), 201


@bp.patch("/attacks/<int:attack_id>")
def add_followup(attack_id):
    """Follow-up 30 to 60 minutes later: severity and inhaler use."""
    data = request.get_json(silent=True) or {}

    severity = data.get("severity")
    if severity is not None and severity not in SEVERITIES:
        return jsonify(error="severity must be mild, moderate or severe"), 400

    inhaler = data.get("inhaler_used")
    if inhaler is not None:
        if not isinstance(inhaler, bool):
            return jsonify(error="inhaler_used must be true or false"), 400
        inhaler = int(inhaler)

    db = get_db()
    cur = db.execute(
        "UPDATE attacks SET severity = COALESCE(?, severity), "
        "inhaler_used = COALESCE(?, inhaler_used) WHERE id = ?",
        (severity, inhaler, attack_id),
    )
    db.commit()
    if cur.rowcount == 0:
        return jsonify(error="attack not found"), 404
    return jsonify(id=attack_id, severity=severity, inhaler_used=None if inhaler is None else bool(inhaler))


@bp.get("/attacks")
def list_attacks():
    try:
        profile_id = int(request.args.get("profile_id", 1))
    except ValueError:
        return jsonify(error="profile_id must be a number"), 400

    rows = get_db().execute(
        "SELECT id, attacked_at, district, severity, inhaler_used, logged_later "
        "FROM attacks WHERE profile_id = ? ORDER BY attacked_at DESC",
        (profile_id,),
    ).fetchall()
    return jsonify([
        {
            "id": r["id"],
            "attacked_at": r["attacked_at"],
            "district": r["district"],
            "severity": r["severity"],
            "inhaler_used": None if r["inhaler_used"] is None else bool(r["inhaler_used"]),
            "logged_later": bool(r["logged_later"]),
        }
        for r in rows
    ])
