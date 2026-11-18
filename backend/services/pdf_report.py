"""Build the one-page doctor summary as a PDF. Returns the file as bytes."""
import os
from datetime import datetime
from io import BytesIO
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from db import get_db
from services.analysis import run_analysis

MAX_ATTACK_ROWS = 15
ACCENT = colors.HexColor("#1F5C7A")

TITLE = ParagraphStyle("title", fontName="Helvetica-Bold", fontSize=18, leading=22, textColor=ACCENT, spaceAfter=4)
H2 = ParagraphStyle("h2", fontName="Helvetica-Bold", fontSize=11.5, leading=15, textColor=ACCENT, spaceBefore=8, spaceAfter=3)
BODY = ParagraphStyle("body", fontName="Helvetica", fontSize=9.5, leading=13)
SMALL = ParagraphStyle("small", fontName="Helvetica", fontSize=8, leading=10.5, textColor=colors.HexColor("#555555"))


def _profile(profile_id):
    row = get_db().execute(
        "SELECT id, name, district FROM profiles WHERE id = ?", (profile_id,)
    ).fetchone()
    if row is None:
        raise LookupError(f"profile {profile_id} not found")
    return row


def _attacks(profile_id):
    db = get_db()
    total = db.execute(
        "SELECT COUNT(*) FROM attacks WHERE profile_id = ?", (profile_id,)
    ).fetchone()[0]
    rows = db.execute(
        "SELECT attacked_at, severity, inhaler_used, logged_later FROM attacks "
        "WHERE profile_id = ? ORDER BY attacked_at DESC LIMIT ?",
        (profile_id, MAX_ATTACK_ROWS),
    ).fetchall()
    return total, rows


def _attack_table(rows):
    data = [["Date and time", "Severity", "Inhaler used", "Logged"]]
    for r in rows:
        inhaler = "not recorded" if r["inhaler_used"] is None else ("yes" if r["inhaler_used"] else "no")
        data.append([
            r["attacked_at"][:16].replace("T", " "),
            r["severity"] or "not recorded",
            inhaler,
            "later" if r["logged_later"] else "at the time",
        ])
    table = Table(data, colWidths=[55 * mm, 40 * mm, 35 * mm, 40 * mm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E6F0F5")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#B8C7CF")),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    return table


def _pattern_flowables(result):
    if result["status"] != "ok":
        return [Paragraph(escape(result["message"]), BODY)]

    items = [Paragraph(escape(result["confidence_note"]), BODY), Spacer(1, 4)]
    for f in result["factors"]:
        if f["range_low"] is None:
            text = f"<b>{f['label']}</b>: {f['verdict']}."
        else:
            text = (f"<b>{f['label']}</b>: {f['verdict']}. Odds ratio {f['odds_ratio']} "
                    f"per standard deviation (range {f['range_low']} to {f['range_high']}).")
        items.append(Paragraph(text, BODY))

    check = result["simple_check"].get("pm25_lag1", {})
    if check.get("attack_rate_above_median") is not None and check.get("attack_rate_below_median") is not None:
        items.append(Spacer(1, 4))
        items.append(Paragraph(
            f"Simple check: attack rate was {check['attack_rate_above_median']:.0%} on days after "
            f"higher-than-median PM2.5, compared with {check['attack_rate_below_median']:.0%} after "
            f"lower-than-median PM2.5.", BODY))
    return items


def build_report_pdf(profile_id):
    profile = _profile(profile_id)
    total, attack_rows = _attacks(profile_id)
    result = run_analysis(profile_id)
    label = os.getenv("DATA_LABEL", "Synthetic demo data")

    story = [
        Paragraph("TriggerTrace: Doctor Summary", TITLE),
        Paragraph(
            f"Patient profile: {escape(profile['name'])}<br/>"
            f"District: {escape(profile['district'] or 'not set')}<br/>"
            f"Prepared: {datetime.now():%d %b %Y, %H:%M}",
            BODY,
        ),
        Paragraph("Attacks", H2),
        Paragraph(f"Total attacks logged: {total}. Most recent {len(attack_rows)} shown below.", BODY),
        Spacer(1, 4),
    ]
    if attack_rows:
        story.append(_attack_table(attack_rows))
    else:
        story.append(Paragraph("No attacks logged yet.", BODY))

    story += [Paragraph("Possible patterns", H2)] + _pattern_flowables(result)
    story += [
        Paragraph("About these results", H2),
        Paragraph(escape(result["disclaimer"]), BODY),
        Spacer(1, 8),
        Paragraph(f"Data source: {escape(label)}", SMALL),
    ]

    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm,
                            topMargin=16 * mm, bottomMargin=16 * mm,
                            title="TriggerTrace Doctor Summary", author="TriggerTrace")
    doc.build(story)
    return buf.getvalue()
