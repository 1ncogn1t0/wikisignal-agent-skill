import os

import matplotlib

matplotlib.use("Agg")
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

    plt.title("WikiSignal: Cleaned Organic Demand Trend", fontsize=12, weight="bold")
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

    growing = [c for c in candidates if c[1]["yoy_growth_percent"] > 0 and c[1]["confidence_score"] >= 70]
    declining = [c for c in candidates if c[1]["yoy_growth_percent"] < 0]
    low_confidence = [l for l, m in candidates if m["confidence_score"] < 60]

    lines = []

    if growing:
        top_lang, top_m = sorted(growing, key=lambda x: x[1]["yoy_growth_percent"], reverse=True)[0]
        lines.append(
            f"Пріоритетний ринок: {top_lang.upper()} — органічне зростання YoY "
            f"+{top_m['yoy_growth_percent']}% при довірі {top_m['confidence_score']}/100. Рекомендовано для пілоту."
        )
    elif len(declining) == len(candidates):
        top_vol = sorted(candidates, key=lambda x: x[1]["daily_avg"], reverse=True)[0]
        lines.append(
            f"Високий ризик: усі аналізовані ринки демонструють спадний тренд (YoY < 0%). "
            f"Найбільша залишкова аудиторія у {top_vol[0].upper()} ({top_vol[1]['daily_avg']} переглядів/день), "
            f"але загальний інтерес до теми охолоджується."
        )
    else:
        lines.append("Змішана динаміка: чіткого лідера зростання не виявлено, потрібна додаткова валідація ніші.")

    if low_confidence:
        lines.append(
            f"Застереження: для {', '.join(l.upper() for l in low_confidence)} виявлено підвищену "
            f"волатильність/шум — не приймайте рішень без перевірки пошукових трендів."
        )

    return "\n".join(lines)


class OnePagerPDF(FPDF):
    def __init__(self):
        super().__init__(orientation="P", unit="mm", format="A4")
        if os.path.exists(FONT_REGULAR) and os.path.exists(FONT_BOLD):
            self.add_font("DejaVu", "", FONT_REGULAR)
            self.add_font("DejaVu", "B", FONT_BOLD)
            self.font = "DejaVu"
        else:
            self.font = "Helvetica"

    def header(self):
        self.set_fill_color(219, 234, 254)
        self.rect(0, 0, 210, 16, "F")
        self.set_text_color(30, 58, 138)
        self.set_font(self.font, "B", 13)
        self.set_xy(12, 4)
        self.cell(0, 6, "WikiSignal: Market Demand Brief", ln=True)
        self.set_font(self.font, "", 8)
        self.set_text_color(71, 105, 180)
        self.set_xy(12, 10)
        self.cell(0, 4, "Wikipedia pageview trend analysis", ln=True)
        self.ln(6)


def generate_pdf(topic_name: str, metrics: dict, chart_path: str, output_path: str):
    pdf = OnePagerPDF()
    pdf.add_page()
    fn = pdf.font

    pdf.set_font(fn, "B", 11)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 7, f"Topic: {topic_name}", ln=True)
    pdf.ln(2)

    col_w = [16, 45, 28, 22, 26, 28, 24]
    headers = ["Lang", "Article", "Daily Avg", "YoY", "Spikes", "Weekend", "Confidence"]

    pdf.set_font(fn, "B", 8)
    pdf.set_fill_color(241, 245, 249)
    pdf.set_text_color(71, 85, 105)
    for w, h in zip(col_w, headers):
        pdf.cell(w, 6, h, border=1, align="C", fill=True)
    pdf.ln()

    pdf.set_font(fn, "", 8)
    for lang, m in metrics.items():
        if "error" in m:
            pdf.set_text_color(220, 38, 38)
            pdf.cell(sum(col_w), 6, f"{lang.upper()}: {m['error']}", border=1)
            pdf.ln()
            continue

        pdf.set_text_color(15, 23, 42)
        pdf.cell(col_w[0], 6, lang.upper(), border=1, align="C")

        title = m.get("resolved_title", "")
        title = title[:22] + ".." if len(title) > 24 else title
        pdf.cell(col_w[1], 6, title, border=1, align="L")

        pdf.cell(col_w[2], 6, f"{m['daily_avg']:,}", border=1, align="C")

        yoy = m["yoy_growth_percent"]
        pdf.set_text_color(220, 38, 38) if yoy < 0 else pdf.set_text_color(15, 23, 42)
        pdf.cell(col_w[3], 6, f"{'+' if yoy > 0 else ''}{yoy}%", border=1, align="C")

        spike = m["spike_share_percent"]
        pdf.set_text_color(220, 38, 38) if spike > 20 else pdf.set_text_color(15, 23, 42)
        pdf.cell(col_w[4], 6, f"{spike}%", border=1, align="C")

        pdf.set_text_color(15, 23, 42)
        pdf.cell(col_w[5], 6, f"{m['weekend_ratio_percent']}%", border=1, align="C")

        conf = m["confidence_score"]
        pdf.set_text_color(220, 38, 38) if conf < 60 else pdf.set_text_color(15, 23, 42)
        pdf.cell(col_w[6], 6, f"{conf}/100", border=1, align="C")

        pdf.set_text_color(15, 23, 42)
        pdf.ln()

    pdf.ln(4)

    if os.path.exists(chart_path):
        pdf.image(chart_path, x=12, w=186)
        pdf.set_y(pdf.get_y() + 4)

    pdf.set_font(fn, "B", 9)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 5, "Recommendation:", ln=True)
    pdf.set_font(fn, "", 8.5)
    pdf.set_text_color(51, 65, 85)
    pdf.multi_cell(0, 4.2, build_recommendation(metrics))

    pdf.ln(2)
    pdf.set_font(fn, "", 7)
    pdf.set_text_color(148, 163, 184)
    pdf.multi_cell(0, 3.5,
                   "Caveats: Wikipedia interest is a top-of-funnel proxy, not commercial intent. "
                   "Weekend share >25% suggests discretionary reading rather than academic use."
                   )

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    pdf.output(output_path)
