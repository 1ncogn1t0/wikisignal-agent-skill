import os
import matplotlib
import matplotlib.pyplot as plt
from fpdf import FPDF

_MPL_FONTS = os.path.join(matplotlib.get_data_path(), "fonts", "ttf")
FONT_REGULAR = os.path.join(_MPL_FONTS, "DejaVuSans.ttf")
FONT_BOLD = os.path.join(_MPL_FONTS, "DejaVuSans-Bold.ttf")
FONT_ITALIC = os.path.join(_MPL_FONTS, "DejaVuSans-Oblique.ttf")


def generate_chart(series_map: dict, output_path: str):
    plt.figure(figsize=(10, 4.2), dpi=200)
    for lang_code, data in series_map.items():
        df = data["df"]
        plt.plot(df["date"], df["ma_30"], label=f"{lang_code.upper()} (30D MA)", linewidth=2)

    plt.title("WikiSignal: Pageview Trend", fontsize=12, weight="bold")
    plt.xlabel("Date", fontsize=10)
    plt.ylabel("Daily Views", fontsize=10)
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.legend(frameon=True)
    plt.tight_layout()
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path)
    plt.close()


def build_recommendation(metrics: dict) -> str:
    candidates = [(lang, m) for lang, m in metrics.items() if "error" not in m]
    if not candidates:
        return "Недостатньо даних для формування висновку."

    ranked = sorted(
        candidates,
        key=lambda x: (x[1].get("mdi_score", 0), x[1]["yoy_growth_percent"]),
        reverse=True,
    )

    lines = []
    top_lang, top_m = ranked[0]
    lines.append(
        f"- Пріоритет ринку: {top_lang.upper()} (MDI {top_m.get('mdi_score', 'N/A')}/100, "
        f"YoY {top_m['yoy_growth_percent']}%, {top_m.get('mdi_tier', '')})."
    )

    low_confidence = [l for l, m in candidates if m["confidence_score"] < 60]
    if low_confidence:
        lines.append(
            f"- Застереження: {', '.join(l.upper() for l in low_confidence)} має високу волатильність/шум "
            f"(Confidence < 60)."
        )

    declining = [l for l, m in candidates if m["yoy_growth_percent"] < 0]
    if declining:
        lines.append(
            f"- Спадний попит: {', '.join(l.upper() for l in declining)} демонструє негативну динаміку YoY."
        )

    return "\n".join(lines)


class OnePagerPDF(FPDF):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if os.path.exists(FONT_REGULAR):
            self.add_font("DejaVu", "", FONT_REGULAR)
            self.add_font("DejaVu", "B", FONT_BOLD)
            self.add_font("DejaVu", "I", FONT_ITALIC)
            self.font_name = "DejaVu"
        else:
            self.font_name = "Helvetica"

    def header(self):
        self.set_font(self.font_name, "B", 15)
        self.cell(0, 8, "WikiSignal: Pageview Brief", ln=True, align="C")
        self.set_font(self.font_name, "I", 9)
        self.cell(0, 5, "Consumer demand & market interest validation", ln=True, align="C")
        self.ln(4)


def generate_pdf(topic_name: str, metrics: dict, chart_path: str, output_path: str):
    pdf = OnePagerPDF(orientation="P", unit="mm", format="A4")
    pdf.set_margins(15, 15, 15)
    pdf.add_page()
    pdf.set_auto_page_break(auto=False)
    fn = pdf.font_name

    pdf.set_font(fn, "B", 11)
    pdf.cell(0, 7, f"Evaluation Topic: {topic_name}", ln=True)
    pdf.set_font(fn, "", 9)
    pdf.multi_cell(0, 4.5, "Executive summary: Normalized Wikimedia pageview signals filtered for PR-spikes and noise.")
    pdf.ln(3)

    # Загальна ширина таблиці: 15 + 35 + 28 + 28 + 34 + 40 = 180 мм (ідеально для A4)
    cols = [15, 35, 28, 28, 34, 40]
    headers = ["Lang", "Daily Avg", "YoY Trend", "Spike %", "Weekend %", "MDI Score"]

    pdf.set_font(fn, "B", 8)
    for c, h in zip(cols, headers):
        pdf.cell(c, 6, h, 1, 0, "C")
    pdf.ln()

    pdf.set_font(fn, "", 8)
    for lang, m in metrics.items():
        if "error" in m:
            continue
        pdf.cell(cols[0], 6, lang.upper(), 1, 0, "C")
        pdf.cell(cols[1], 6, f"{m['daily_avg']:,}", 1, 0, "C")
        pdf.cell(cols[2], 6, f"{m['yoy_growth_percent']}%", 1, 0, "C")
        pdf.cell(cols[3], 6, f"{m['spike_share_percent']}%", 1, 0, "C")
        pdf.cell(cols[4], 6, f"{m['weekend_ratio_percent']}%", 1, 0, "C")
        pdf.cell(cols[5], 6, f"{m.get('mdi_score', 'N/A')}/100", 1, 0, "C")
        pdf.ln()

    pdf.ln(4)
    if os.path.exists(chart_path):
        pdf.image(chart_path, x=15, w=180)
        pdf.ln(2)

    pdf.set_y(225)
    pdf.set_font(fn, "B", 10)
    pdf.cell(0, 5, "Recommendation:", ln=True)
    pdf.set_font(fn, "", 8.5)
    pdf.multi_cell(0, 4, build_recommendation(metrics))

    pdf.ln(2)
    pdf.set_font(fn, "B", 8.5)
    pdf.cell(0, 4, "Notes:", ln=True)
    pdf.set_font(fn, "", 7.5)
    pdf.multi_cell(
        0, 3.5,
        "- MDI (Market Demand Index): Proprietary composite index evaluating volume, growth momentum, and organic stability.\n"
        "- Weekend ratio > 25% signals direct B2C discretionary interest rather than academic/work lookup."
    )

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    pdf.output(output_path)