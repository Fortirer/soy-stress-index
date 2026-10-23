"""US one-pager (Illinois evidence) with a QR code to the repository.

    python midwest/scripts/11_onepager.py  ->  midwest/report/turgor_illinois_onepager.pdf
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

HERE = Path(__file__).resolve().parents[1]
ROOT = HERE.parent
URL = "https://github.com/Fortirer/soy-stress-index/tree/main/midwest"
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
    out = HERE / "report/turgor_illinois_onepager.pdf"
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
    c.drawRightString(W - m, H - m - s - 0.05 * cm, "Illinois analysis + code")

    y = H - m - 2.4 * cm
    head = P("One soybean stress index, validated on two continents", 22, GREEN, True, 25)
    w, h = head.wrap(W - 2 * m - 3 * cm, 100)
    head.drawOn(c, m, y - h)
    y -= h + 0.25 * cm
    sub = P("Turgor turns soybean physiology (when drought and heat hit flowering and seed fill) into a weekly "
            "county stress map and expected loss, from satellite and weather data only. Built in Brazil; tested in Illinois.", 11.5, MUTED)
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

    y = block("Why",
              "Lenders, crop insurers and grain buyers learn the size of a soybean shortfall late. In Illinois the loss below trend "
              "averaged <b>US$ 23.5/acre a year</b> (2001–2025), <b>US$ 57/acre</b> in a bad year and <b>US$ 104/acre in 2012</b> "
              "(at US$ 12.55/bu). July–August rainfall is the usual weather signal; it can miss stress at seed fill.", y)
    y = block("What",
              "Weekly, June to October: crop stage from MODIS NDVI (corn–soybean pixels, USDA Cropland Data Layer), water deficit, "
              "heat above 30 °C and their interaction from NASA POWER, weighted 3× at flowering and seed fill. "
              "Same formula and weights as in Brazil: nothing was tuned on Illinois.", y)
    t = P("Illinois evidence (102 counties, 2001–2023 backtest; 2,194 county-seasons)", 12, GREEN, True)
    w, h = t.wrap(W - 2 * m, 50)
    t.drawOn(c, m, y - h)
    y -= h + 0.15 * cm
    rows = [["", "Turgor", "Rainfall Jul–Aug", "Palmer Aug", "NDVI only"],
            ["AUC, loss > 10%", "0.81", "0.75", "0.69", "0.68"],
            ["Share of losses missed (basis risk)", "0.47", "0.57", "0.54", "0.72"],
            ["Statewide-year correlation", "0.60", "0.44", "0.34", "0.44"]]
    tb = Table(rows, colWidths=[6.4 * cm] + [2.65 * cm] * 4)
    tb.setStyle(TableStyle([
        ("FONT", (0, 0), (-1, -1), FN, 9.5), ("FONT", (0, 0), (-1, 0), FB, 9.5), ("FONT", (1, 1), (1, -1), FB, 9.5),
        ("TEXTCOLOR", (1, 1), (1, -1), rc.HexColor(GREEN)), ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [rc.HexColor(PALE), rc.white]),
        ("LINEBELOW", (0, 0), (-1, 0), 0.6, rc.HexColor(RULE)), ("TOPPADDING", (0, 0), (-1, -1), 2.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5)]))
    w, h = tb.wrap(W - 2 * m, 200)
    tb.drawOn(c, m, y - h)
    y -= h + 0.2 * cm
    note = P("<b>Honest limits:</b> the gain over rainfall is not statistically proven in Illinois (better in 78–85% of resampled "
             "season sets), and on the 2024–25 holdout (17 losses) rainfall did better. <b>2003:</b> July–August rain looked normal, "
             "the index ranked the season 78th percentile of stress; yields ended −17%. <b>15 July 2012:</b> 99 of 102 counties "
             "rated severe; they ended −17%. <b>Brazil</b> (780 municipalities): AUC 0.86 vs 0.78 for rainfall, gain proven, "
             "8–12 weeks before harvest.", 9.5, MUTED, lead=12.5)
    w, h = note.wrap(W - 2 * m, 200)
    note.drawOn(c, m, y - h)
    y -= h + 0.55 * cm
    y = block("For whom",
              "Reinsurers and parametric providers working in Brazil and the US; lenders and crop insurers watching a soybean book in "
              "season; grain buyers forecasting supply. Pricing to test: per portfolio per year, or US$ 0.25–2 per acre per season.", y)
    y = block("Looking for",
              "<b>Conversations</b> with lenders, insurers and grain buyers about how they track crop risk today. "
              "<b>Collaborators:</b> remote sensing and data science; agricultural finance and insurance. "
              "<b>Advisors:</b> crop insurance, farm credit, crop modelling.", y)

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
