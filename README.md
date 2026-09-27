# WikiSignal Agent Skill

Agent Skill: оцінює попит на тему за переглядами Wikipedia в різних мовних
розділах, відсіює новинні сплески від органічного інтересу, формує PDF-звіт
з рекомендацією. Призначено для AI-агента — він читає `SKILL.md`, сам
перетворює запит користувача ("чи росте інтерес до X в PL та CS") у виклик
CLI нижче. Команди тут — для ручної перевірки.

## Встановлення

```bash
git clone https://github.com/1ncogn1t0/wikisignal-agent-skill.git
cd wikisignal-agent-skill
python3 -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Запуск

```bash
# повний звіт, мови за замовчуванням (en,uk)
python3 scripts/run_analysis.py --topic "Machine Learning"

# лише метрики, без PDF (швидше)
python3 scripts/run_analysis.py --topic "Machine Learning" --format json

# свої мови + мова самого запиту
python3 scripts/run_analysis.py --topic "Machine Learning" --source_lang en --langs "pl,cs,uk" --years 2 --format full
```

`--source_lang` — мова тексту `--topic`, не мови порівняння.

## Параметри

| Параметр | За замовчуванням | Опис |
|---|---|---|
| `--topic` | — (обов'язковий) | Тема, будь-якою мовою |
| `--source_lang` | `en` | Мова тексту `--topic` |
| `--langs` | `en,uk` | Мовні коди Wikipedia для порівняння |
| `--years` | `2` | Історичний горизонт |
| `--format` | `full` | `json` — лише метрики; `full` — + графік і PDF |
| `--output_dir` | `output` | Куди зберігати артефакти |

## Резолвінг тем між мовами

`--topic` — вільний текст, не точна назва статті. Тема резолвиться через
Wikidata (один QID → назви статей у кожній мові за sitelinks), тому запит
українською коректно порівнюється з польською чи чеською вікі. Якщо для
мови немає sitelink — fallback-пошук напряму по цій вікі.

## Метрики в JSON

- `daily_avg` — середній щоденний трафік
- `yoy_growth_percent` — динаміка рік-до-року (>15% зростання, <0% спад)
- `spike_share_percent` — частка трафіку від новинних сплесків (>20% = хайп, не органіка)
- `weekend_ratio_percent` — частка перегляду у вихідні (>25% = дозвіллєвий інтерес)
- `confidence_score` (0–100) — надійність тренду

## Артефакти (`--format full`)

`output/trend_<topic>.png` — графік, `output/report_<topic>.pdf` — звіт на 1 сторінку.
