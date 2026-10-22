"""One-page summary with a QR code to the repository (issue #23).

    python scripts/26_onepager.py   ->  docs/report/turgor_onepager_en.pdf
"""
from pathlib import Path

from reportlab.graphics import renderPDF
from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.graphics.shapes import Drawing
from reportlab.lib import colors as rc
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Image, Paragraph, Table, TableStyle
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parents[1]
URL = "https://github.com/Fortirer/soy-stress-index"
GREEN, INK, MUTED, RULE, PALE = "#1E5B3A", "#12291D", "#4A5D52", "#D9E3DC", "#E3EFE7"

FONT = Path("/usr/share/fonts/truetype/crosextra/")
if (FONT / "Carlito-Regular.ttf").exists():
    pdfmetrics.registerFont(TTFont("B", str(FONT / "Carlito-Regular.ttf")))
    pdfmetrics.registerFont(TTFont("B-b", str(FONT / "Carlito-Bold.ttf")))
    pdfmetrics.registerFontFamily("B", normal="B", bold="B-b", italic="B", boldItalic="B-b")
    FN, FB = "B", "B-b"
else:
    FN, FB = "Helvetica", "Helvetica-Bold"


def P(text, size=10, color=INK, bold=False, lead=None):
    return Paragraph(text, ParagraphStyle("p", fontName=FB if bold else FN, fontSize=size,
                                          leading=lead or size * 1.3, textColor=rc.HexColor(color)))


def main():
    out = ROOT / "docs/report/turgor_onepager_en.pdf"
    W, H = A4
    m = 1.6 * cm
    c = canvas.Canvas(str(out), pagesize=A4)
    c.setTitle("Turgor one-pager")
    c.setAuthor("Janaina Fortirer")

    # header
    c.drawImage(str(ROOT / "docs/report/turgor_logo.png"), m, H - m - 1.5 * cm, width=4.7 * cm, height=1.5 * cm,
                preserveAspectRatio=True, mask="auto")
    qr = QrCodeWidget(URL)
    b = qr.getBounds()
    s = 2.6 * cm
    d = Drawing(s, s, transform=[s / (b[2] - b[0]), 0, 0, s / (b[3] - b[1]), 0, 0])
    d.add(qr)
    renderPDF.draw(d, c, W - m - s, H - m - s + 0.2 * cm)
    c.setFont(FN, 7.5)
    c.setFillColor(rc.HexColor(MUTED))
    c.drawRightString(W - m, H - m - s - 0.05 * cm, "code + validation report")

    y = H - m - 2.4 * cm
    head = P("See soybean drought losses weeks before harvest", 22, GREEN, True, 25)
    w, h = head.wrap(W - 2 * m - 3 * cm, 100)
    head.drawOn(c, m, y - h)
    y -= h + 0.25 * cm
    sub = P("A crop-physiology stress index for co-ops, input resellers, lenders and insurers in Brazil. "
            "Satellite and weather data only, no farm sensors.", 11.5, MUTED)
    w, h = sub.wrap(W - 2 * m - 3 * cm, 100)
    sub.drawOn(c, m, y - h)
    y -= h + 0.6 * cm

    def block(title, body, y):
        t = P(title, 12, GREEN, True)
        w, h1 = t.wrap(W - 2 * m, 50)
        t.drawOn(c, m, y - h1)
        bp = P(body, 10, INK, lead=13.5)
        w, h2 = bp.wrap(W - 2 * m, 400)
        bp.drawOn(c, m, y - h1 - 0.12 * cm - h2)
        return y - h1 - h2 - 0.55 * cm

    y = block("Problem",
              "Soybean losses below trend average <b>R$ 700–1,200 per ha a year</b> in Paraná and Rio Grande do Sul "
              "(2016–2025, at today’s price). Those who finance the crop learn how bad a season was at harvest, through "
              "field inspections. Rainfall triggers for parametric insurance miss 44% of real losses; the official ZARC "
              "zoning barely separates loss seasons (AUC 0.57).", y)
    y = block("Product",
              "Weekly, December to April: each field’s crop stage from Sentinel-2 and MODIS, plus water deficit, heat above 30 °C "
              "and their interaction, weighted by crop stage (flowering and seed fill count 3×). Output: a stress map per "
              "municipality or field, and expected loss in R$ per ha. Live monitor from 2 December 2026.", y)

    # evidence table
    t = P("Evidence (public, reproducible; 780 municipalities, RS + PR)", 12, GREEN, True)
    w, h = t.wrap(W - 2 * m, 50)
    t.drawOn(c, m, y - h)
    y -= h + 0.15 * cm
    rows = [["", "Turgor", "Rainfall", "NDVI", "ZARC"],
            ["Backtest 2001–2023, AUC", "0.86", "0.78", "0.77", "0.57"],
            ["Backtest, share of losses missed", "0.33", "0.44", "0.44", "0.64"],
            ["New seasons 2024–25, AUC", "0.67", "0.56", "0.61", "0.57"],
            ["New seasons, share of losses missed", "0.36", "0.51", "0.42", "0.46"]]
    tb = Table(rows, colWidths=[7.4 * cm] + [2.4 * cm] * 4)
    tb.setStyle(TableStyle([
        ("FONT", (0, 0), (-1, -1), FN, 9.5), ("FONT", (0, 0), (-1, 0), FB, 9.5), ("FONT", (1, 1), (1, -1), FB, 9.5),
        ("TEXTCOLOR", (1, 1), (1, -1), rc.HexColor(GREEN)), ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [rc.HexColor(PALE), rc.white]),
        ("LINEBELOW", (0, 0), (-1, 0), 0.6, rc.HexColor(RULE)), ("TOPPADDING", (0, 0), (-1, -1), 2.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5)]))
    w, h = tb.wrap(W - 2 * m, 200)
    tb.drawOn(c, m, y - h)
    y -= h + 0.2 * cm
    note = P("<b>Early warning:</b> by 15 January the index matches what a rainfall index only knows at season end, "
             "8–12 weeks before harvest. <b>Real season:</b> on 15 Feb 2025, municipalities rated “severe” ended 30% below "
             "trend; 83% lost more than 10%. <b>Limit:</b> in Rio Grande do Sul the municipal gain over rainfall is likely "
             "but not yet proven.", 9.5, MUTED, lead=12.5)
    w, h = note.wrap(W - 2 * m, 200)
    note.drawOn(c, m, y - h)
    y -= h + 0.55 * cm

    y = block("Business",
              "B2B, per hectare per season (hypotheses being tested: risk score R$ 2–6/ha; alerts R$ 1–3/ha; insurance trigger "
              "licence 1–3% of premium; portfolio backtests R$ 30–100 k). Market at R$ 3/ha: RS + PR R$ 37 M a year, "
              "Brazil R$ 146 M (48.7 M ha, Conab 2025/26).", y)
    y = block("Looking for",
              "<b>Pilots:</b> a free backtest on your own fields or portfolio, report in two weeks. "
              "<b>Cofounders:</b> a data and remote-sensing CTO; a business lead from rural credit or insurance. "
              "<b>Advisors:</b> crop modelling, agricultural insurance, rural credit.", y)

    # footer
    c.setStrokeColor(rc.HexColor(RULE))
    c.line(m, m + 0.9 * cm, W - m, m + 0.9 * cm)
    f = P("<b>Janaina Fortirer</b>, plant ecophysiologist (PhD candidate, University of São Paulo; visiting researcher, "
          "University of Illinois) · psjana@usp.br · " + URL.replace("https://", ""), 9, MUTED)
    w, h = f.wrap(W - 2 * m, 50)
    f.drawOn(c, m, m + 0.75 * cm - h)
    c.showPage()
    c.save()
    print(out, "bottom margin left:", round((y - m - 1.0 * cm) / cm, 2), "cm")


if __name__ == "__main__":
    main()
