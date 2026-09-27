import argparse
import json
import os
import sys

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from analyzer import analyze_traffic
from report import generate_chart, generate_pdf
from wiki_client import fetch_pageviews, resolve_titles


def run_pipeline(topic: str, langs_str: str, source_lang: str = "en", years: int = 2, fmt: str = "full", output_dir: str = "output") -> dict:
    langs = [l.strip().lower() for l in langs_str.split(",") if l.strip()]
    titles = resolve_titles(topic, langs, source_lang=source_lang)

    metrics_summary = {}
    series_map = {}

    for lang in langs:
        if lang not in titles:
            metrics_summary[lang] = {
                "error": f"Article not found in {lang}.wikipedia."
            }
            continue

        title = titles[lang]
        try:
            views_data = fetch_pageviews(title, lang, years=years)
            analysis = analyze_traffic(views_data)

            if "error" in analysis:
                metrics_summary[lang] = {
                    "resolved_title": title,
                    "error": analysis["error"]
                }
                continue

            metrics_summary[lang] = {
                "resolved_title": title,
                "tam_annual_views": analysis["tam_annual_views"],
                "daily_avg": analysis["daily_avg"],
                "yoy_growth_percent": analysis["yoy_growth_percent"],
                "qoq_growth_percent": analysis["qoq_growth_percent"],
                "spike_share_percent": analysis["spike_share_percent"],
                "weekend_ratio_percent": analysis["weekend_ratio_percent"],
                "volatility_cv": analysis["volatility_cv"],
                "confidence_score": analysis["confidence_score"],
                "hitl_required": analysis["hitl_required"],
                "hitl_reasons": analysis["hitl_reasons"],
                "mdi_score": analysis["mdi_score"],
                "mdi_tier": analysis["mdi_tier"],
                "mdi_action": analysis["mdi_action"]
            }
            series_map[lang] = analysis

        except Exception as e:
            metrics_summary[lang] = {
                "resolved_title": title,
                "error": str(e)
            }

    output = {
        "topic": topic,
        "markets": metrics_summary
    }

    if not series_map:
        return {
            "error": "Failed to retrieve valid telemetry for the requested scope.",
            "details": metrics_summary
        }

    if fmt == "full":
        os.makedirs(output_dir, exist_ok=True)
        clean_topic = topic.replace(" ", "_").lower()
        chart_file = os.path.join(output_dir, f"trend_{clean_topic}.png")
        pdf_file = os.path.join(output_dir, f"report_{clean_topic}.pdf")

        generate_chart(series_map, chart_file)
        generate_pdf(topic, metrics_summary, chart_file, pdf_file)

        output["artifacts"] = {
            "chart_png": chart_file,
            "report_pdf": pdf_file
        }

    return output


def main():
    parser = argparse.ArgumentParser(description="WikiSignal Enterprise CLI")
    parser.add_argument("--topic", required=True, help="Product or niche name")
    parser.add_argument("--source_lang", default="en", help="Language for Wikidata disambiguation")
    parser.add_argument("--langs", type=str, default="en,uk", help="Target market ISO codes")
    parser.add_argument("--years", type=int, default=2, help="Historical analysis window")
    parser.add_argument("--format", choices=["json", "full"], default="full", help="'json' or 'full'")
    parser.add_argument("--output_dir", default="output", help="Artifacts storage")

    args = parser.parse_args()

    result = run_pipeline(
        topic=args.topic,
        langs_str=args.langs,
        source_lang=args.source_lang,
        years=args.years,
        fmt=args.format,
        output_dir=args.output_dir
    )

    print(json.dumps(result, indent=2, ensure_ascii=False, default=lambda x: float(x) if hasattr(x, "__float__") else str(x)))


if __name__ == "__main__":
    main()