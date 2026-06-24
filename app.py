from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from pathlib import Path
import pandas as pd

def create_pdf_report(df, output_path="investment_report.pdf"):
    output_path = Path(output_path)
    doc = SimpleDocTemplate(str(output_path), pagesize=A4)
    styles = getSampleStyleSheet()
    story = []
    story.append(Paragraph("Luc Investment Terminal - Portfolio Report", styles["Title"]))
    story.append(Spacer(1, 12))
    story.append(Paragraph("Educational report generated from your Streamlit dashboard.", styles["BodyText"]))
    story.append(Spacer(1, 12))

    cols = ["Ticker", "Company", "Weight", "Price", "Forward P/E", "PEG", "Total Score /100", "Investment Rating"]
    data = [cols]
    for _, r in df[cols].fillna("N/A").iterrows():
        data.append([str(r[c])[:28] for c in cols])
    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#0E1117")),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("GRID", (0,0), (-1,-1), 0.25, colors.grey),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,-1), 7),
    ]))
    story.append(table)
    doc.build(story)
    return output_path