from flask import Blueprint, jsonify, request

from db import get_db

bp = Blueprint("profile", __name__)
ROLES = {"self", "caregiver"}


def _to_row(r):
    return {"id": r["id"], "name": r["name"], "role": r["role"], "district": r["district"]}


@bp.get("/profiles")
def list_profiles():
    rows = get_db().execute("SELECT id, name, role, district FROM profiles ORDER BY id").fetchall()
    return jsonify([_to_row(r) for r in rows])


@bp.post("/profiles")
def create_profile():
    """Add a profile. Use role 'caregiver' when logging for a child or older adult."""
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify(error="name is required"), 400

    role = data.get("role", "self")
    if role not in ROLES:
        return jsonify(error="role must be self or caregiver"), 400

    district = (data.get("district") or "").strip() or None

    db = get_db()
    cur = db.execute(
        "INSERT INTO profiles (name, role, district) VALUES (?, ?, ?)",
        (name, role, district),
    )
    db.commit()
    row = db.execute(
        "SELECT id, name, role, district FROM profiles WHERE id = ?", (cur.lastrowid,)
    ).fetchone()
    return jsonify(_to_row(row)), 201


@bp.patch("/profiles/<int:profile_id>")
def update_profile(profile_id):
    """Change the name, role or district. Only the fields you send are changed."""
    data = request.get_json(silent=True) or {}

    if "role" in data and data["role"] not in ROLES:
        return jsonify(error="role must be self or caregiver"), 400
    name = data.get("name")
    if name is not None and not str(name).strip():
        return jsonify(error="name cannot be empty"), 400

    db = get_db()
    cur = db.execute(
        "UPDATE profiles SET name = COALESCE(?, name), role = COALESCE(?, role), "
        "district = COALESCE(?, district) WHERE id = ?",
        (name, data.get("role"), data.get("district"), profile_id),
    )
    db.commit()
    if cur.rowcount == 0:
        return jsonify(error="profile not found"), 404

    row = db.execute(
        "SELECT id, name, role, district FROM profiles WHERE id = ?", (profile_id,)
    ).fetchone()
    return jsonify(_to_row(row))


@bp.delete("/profiles/<int:profile_id>/data")
def delete_profile_data(profile_id):
    """Delete all attacks and check-ins for this profile, but keep the profile itself."""
    db = get_db()
    exists = db.execute("SELECT 1 FROM profiles WHERE id = ?", (profile_id,)).fetchone()
    if not exists:
        return jsonify(error="profile not found"), 404

    db.execute("DELETE FROM attacks WHERE profile_id = ?", (profile_id,))
    db.execute("DELETE FROM checkins WHERE profile_id = ?", (profile_id,))
    db.commit()
    return jsonify(deleted=True, profile_id=profile_id)


@bp.delete("/profiles/<int:profile_id>")
def delete_profile(profile_id):
    """Delete the profile and, through foreign keys, all of its attacks and check-ins."""
    db = get_db()
    cur = db.execute("DELETE FROM profiles WHERE id = ?", (profile_id,))
    db.commit()
    if cur.rowcount == 0:
        return jsonify(error="profile not found"), 404
    return jsonify(deleted=True, profile_id=profile_id)
