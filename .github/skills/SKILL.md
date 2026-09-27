---
name: wikisignal
description: Analyzes Wikipedia pageview trends across languages to validate B2C product/course demand, detect news-driven noise, and prioritize which markets or topics to invest in next.
---

# WikiSignal Skill

## Purpose
Evaluate consumer demand, course launches, and localization opportunities for
B2C products using Wikimedia pageview data, cleaned of news-driven spikes.

## When to use this skill
- Whether interest in a topic/course is rising or falling in target regions.
- Comparing demand for the same topic across multiple language editions
  (e.g. Polish vs Czech vs Ukrainian), even when the user's query is written
  in only one of those languages.
- Whether a traffic surge reflects genuine, durable interest or a transient
  news/viral spike.

## Default Language Strategy
- **Default (No markets specified):** Analyze `en,uk` (Global benchmark + Ukraine).
- **Custom Markets:** If the user specifies countries, regions, or languages (e.g., "Польща", "pl,cs"), map them to ISO codes and pass via `--langs`.

## Execution Commands
Execute via workspace terminal:

### Default Run (en,uk):
```bash
python scripts/run_analysis.py --topic "<TOPIC>" --langs "en,uk" --years 2 --format full
```

## Custom Markets Run
```bash
python scripts/run_analysis.py \
  --topic "<TOPIC_NAME>" \
  --source_lang <LANG_OF_TOPIC_TEXT> \
  --langs "<LANG_1>,<LANG_2>" \
  --years 2 \
  --format full
```

- `--topic`: free-text topic, in any language. It is resolved to a Wikidata
  entity, then mapped to the exact article title in each requested language
  — so a Ukrainian query can be compared correctly across pl/cs/en/etc.
- `--source_lang`: the language the `--topic` text itself is written in
  (defaults to `en`). Set this to match the query, not the target markets.
- `--langs`: comma-separated Wikipedia language codes to compare.
- `--format json`: use this for quick, conversational follow-up questions
  (no chart/PDF generation — faster and cheaper). Use `--format full` only
  when the user wants a shareable one-page report.

## Interpreting the JSON output
- `daily_avg`: baseline market size (daily organic readers).
- `yoy_growth_percent`: year-over-year momentum (>15% = high growth,
  0–15% = stable, <0% = declining).
- `spike_share_percent`: share of traffic from abnormal spikes (>20% =
  news/PR-driven volatility, not evergreen demand — treat growth numbers
  with caution).
- `weekend_ratio_percent`: discretionary-reading index (>25% suggests
  personal interest rather than academic/homework usage).
- `confidence_score` (0–100): reliability of the trend, penalized by spike
  share and volatility. Below 60, state the caveat explicitly to the user
  rather than presenting the trend as settled.

## Handling follow-up and refined queries
Users commonly refine after the first answer ("what about 3 years instead",
"add German", "just compare growth, skip the PDF"). Re-run the CLI with
updated arguments rather than re-deriving numbers manually — it is
deterministic and cheap. Default to `--format json` for these follow-ups;
only regenerate the chart/PDF (`--format full`) when the user explicitly
wants a document to keep or share.

## Error handling
- A language missing from the output `markets` object means the topic could
  not be resolved to an article in that language — say so plainly rather
  than guessing a substitute topic.
- Fewer than ~60 days of history for a language returns an explicit
  "insufficient data" error — surface it rather than reporting a trend from
  too little data.
