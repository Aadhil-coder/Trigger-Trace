from io import BytesIO

from flask import Blueprint, jsonify, request, send_file

bp = Blueprint("report", __name__)


@bp.get("/report")
def get_report():
    """Download the one-page doctor summary as a PDF."""
    try:
        profile_id = int(request.args.get("profile_id", 1))
    except ValueError:
        return jsonify(error="profile_id must be a number"), 400

    # Imported here so the rest of the API still starts before the PDF service exists.
    from services.pdf_report import build_report_pdf

    pdf_bytes = build_report_pdf(profile_id)
    return send_file(
        BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"triggertrace_summary_profile_{profile_id}.pdf",
    )
