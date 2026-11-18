from flask import Blueprint, jsonify, request

bp = Blueprint("patterns", __name__)


@bp.get("/patterns")
def get_patterns():
    """Run the analysis for one profile and return possible patterns with confidence notes."""
    try:
        profile_id = int(request.args.get("profile_id", 1))
    except ValueError:
        return jsonify(error="profile_id must be a number"), 400

    # Imported here so the rest of the API still starts before the analysis service exists.
    from services.analysis import run_analysis

    result = run_analysis(profile_id)
    return jsonify(result)
