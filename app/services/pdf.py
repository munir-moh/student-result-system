from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from app.core.config import settings
from app.core.grading import AFFECTIVE_LABELS


def build_pdf(data: dict) -> bytes:
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            rightMargin=1.5*cm, leftMargin=1.5*cm,
                            topMargin=1.5*cm, bottomMargin=1.5*cm)
    s = getSampleStyleSheet()
    bold  = ParagraphStyle("b", fontSize=9,  fontName="Helvetica-Bold")
    plain = ParagraphStyle("p", fontSize=9,  fontName="Helvetica")
    ctr   = ParagraphStyle("c", fontSize=13, fontName="Helvetica-Bold", alignment=TA_CENTER)
    sub   = ParagraphStyle("s", fontSize=10, fontName="Helvetica",      alignment=TA_CENTER)
    els   = []

    els += [
        Paragraph(settings.SCHOOL_NAME.upper(),
                  ParagraphStyle("h", fontSize=16, fontName="Helvetica-Bold", alignment=TA_CENTER, spaceAfter=4)),
        Paragraph(settings.SCHOOL_ADDRESS, sub),
        Paragraph(f"Tel: {settings.SCHOOL_PHONE}", sub),
        HRFlowable(width="100%", thickness=2, color=colors.darkblue),
        Spacer(1, 0.3*cm),
        Paragraph("STUDENT REPORT CARD", ctr),
        Spacer(1, 0.4*cm),
    ]

    info = [
        [Paragraph("<b>Name:</b>", bold),          Paragraph(data["student_name"], plain),
         Paragraph("<b>Student ID:</b>", bold),     Paragraph(data["student_id"], plain)],
        [Paragraph("<b>Class:</b>", bold),          Paragraph(f"{data['class_level']} {data['arm'] or ''}".strip(), plain),
         Paragraph("<b>Gender:</b>", bold),         Paragraph(data["gender"], plain)],
        [Paragraph("<b>Academic Year:</b>", bold),  Paragraph(data["academic_year"], plain),
         Paragraph("<b>Term:</b>", bold),           Paragraph(f"{data['term']} Term", plain)],
        [Paragraph("<b>Date of Birth:</b>", bold),  Paragraph(str(data["date_of_birth"]), plain),
         Paragraph("<b>Class Size:</b>", bold),     Paragraph(str(data["class_size"]), plain)],
    ]
    t = Table(info, colWidths=[3.5*cm, 6*cm, 3.5*cm, 5*cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), colors.whitesmoke),
        ("BOX", (0,0), (-1,-1), 0.5, colors.grey),
        ("INNERGRID", (0,0), (-1,-1), 0.25, colors.lightgrey),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("TOPPADDING", (0,0), (-1,-1), 4),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
    ]))
    els += [t, Spacer(1, 0.4*cm)]

    els.append(Paragraph("<b>ACADEMIC PERFORMANCE</b>",
                         ParagraphStyle("rh", fontSize=10, fontName="Helvetica-Bold", spaceAfter=4)))
    rows = [["Subject", "CA1\n(20)", "CA2\n(20)", "Exam\n(60)", "Total\n(100)", "Grade", "Remark", "Status"]]
    for sub in data["subjects"]:
        rows.append([
            sub["subject_name"],
            f"{sub['ca1']:.1f}"   if sub["ca1"]   is not None else "-",
            f"{sub['ca2']:.1f}"   if sub["ca2"]   is not None else "-",
            f"{sub['exam']:.1f}"  if sub["exam"]  is not None else "-",
            f"{sub['total']:.1f}" if sub["total"] is not None else "-",
            sub["grade"]  or "-",
            sub["remark"] or "-",
            "PASS" if sub["is_pass"] else "FAIL",
        ])
    rows += [
        ["", "", "", "Total",   f"{data['total_score']:.1f}", "", "", ""],
        ["", "", "", "Average", f"{data['average']:.1f}%",    "", "", ""],
        ["", "", "", "Position",data["position"],             "", "", ""],
    ]
    rt = Table(rows, colWidths=[5.5*cm,1.5*cm,1.5*cm,1.8*cm,1.8*cm,1.5*cm,2.5*cm,2*cm])
    rt.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.darkblue),
        ("TEXTCOLOR",  (0,0), (-1,0), colors.white),
        ("FONTNAME",   (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE",   (0,0), (-1,-1), 8),
        ("ALIGN",      (1,0), (-1,-1), "CENTER"),
        ("ROWBACKGROUNDS", (0,1), (-1,-4), [colors.white, colors.lightyellow]),
        ("BOX",        (0,0), (-1,-1), 0.5, colors.grey),
        ("INNERGRID",  (0,0), (-1,-1), 0.25, colors.lightgrey),
        ("TOPPADDING", (0,0), (-1,-1), 3),
        ("BOTTOMPADDING", (0,0), (-1,-1), 3),
        ("FONTNAME",   (0,-3), (-1,-1), "Helvetica-Bold"),
        ("BACKGROUND", (0,-3), (-1,-1), colors.lightblue),
    ]))
    els += [rt, Spacer(1, 0.4*cm)]

    aff = data.get("affective")
    if aff:
        els.append(Paragraph("<b>AFFECTIVE / PSYCHOMOTOR DOMAIN</b>",
                             ParagraphStyle("ah", fontSize=10, fontName="Helvetica-Bold", spaceAfter=4)))
        def rl(v): return f"{v} – {AFFECTIVE_LABELS.get(v,'')}" if v else "-"
        aff_rows = [
            ["Trait", "Rating", "Trait", "Rating"],
            ["Punctuality",   rl(aff.punctuality),    "Neatness",         rl(aff.neatness)],
            ["Honesty",       rl(aff.honesty),         "Leadership",       rl(aff.leadership)],
            ["Sports",        rl(aff.sports),          "Arts",             rl(aff.arts)],
            ["Verbal Fluency",rl(aff.verbal_fluency),  "Tool Handling",    rl(aff.handling_of_tools)],
        ]
        at = Table(aff_rows, colWidths=[4*cm,5*cm,4*cm,5*cm])
        at.setStyle(TableStyle([
            ("BACKGROUND",     (0,0), (-1,0), colors.steelblue),
            ("TEXTCOLOR",      (0,0), (-1,0), colors.white),
            ("FONTNAME",       (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE",       (0,0), (-1,-1), 8),
            ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.aliceblue]),
            ("BOX",            (0,0), (-1,-1), 0.5, colors.grey),
            ("INNERGRID",      (0,0), (-1,-1), 0.25, colors.lightgrey),
            ("TOPPADDING",     (0,0), (-1,-1), 3),
            ("BOTTOMPADDING",  (0,0), (-1,-1), 3),
        ]))
        els += [at, Spacer(1, 0.4*cm)]

    ct = Table([
        [Paragraph("<b>Comment:</b>", bold), Paragraph(data["comment"], plain)]
    ], colWidths=[3*cm, 15*cm])
    ct.setStyle(TableStyle([
        ("BOX", (0,0), (-1,-1), 0.5, colors.grey),
        ("INNERGRID", (0,0), (-1,-1), 0.25, colors.lightgrey),
        ("TOPPADDING", (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
        ("BACKGROUND", (0,0), (-1,-1), colors.whitesmoke),
    ]))
    els += [ct, Spacer(1, 0.5*cm)]

    sig = Table([[
        Paragraph("_____________________\nClass Teacher", ParagraphStyle("sg", fontSize=8, alignment=TA_CENTER)),
        Paragraph("_____________________\nPrincipal",     ParagraphStyle("sg2",fontSize=8, alignment=TA_CENTER)),
        Paragraph("_____________________\nSchool Stamp",  ParagraphStyle("sg3",fontSize=8, alignment=TA_CENTER)),
    ]], colWidths=[6*cm,6*cm,6*cm])
    sig.setStyle(TableStyle([("ALIGN",(0,0),(-1,-1),"CENTER"),("TOPPADDING",(0,0),(-1,-1),20)]))
    els += [sig, Spacer(1, 0.3*cm), HRFlowable(width="100%", thickness=0.5, color=colors.grey)]
    els.append(Paragraph(
        "<b>Grade Key:</b> A(75–100) Excellent | B(65–74) Very Good | C(55–64) Good | D(45–54) Pass | E(40–44) Pass | F(0–39) Fail",
        ParagraphStyle("gk", fontSize=7, alignment=TA_CENTER)
    ))

    doc.build(els)
    return buf.getvalue()
