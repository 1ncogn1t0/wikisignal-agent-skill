import time
import urllib.parse
from datetime import datetime, timedelta
import requests

USER_AGENT = "WikiSignalBot/1.0 (https://github.com/1ncogn1t0/wikisignal-agent-skill; case-submission@example.com)"
HEADERS = {"User-Agent": USER_AGENT}


def resolve_qid(query: str, source_lang: str = "en") -> str | None:
    url = "https://www.wikidata.org/w/api.php"
    params = {
        "action": "wbsearchentities",
        "search": query,
        "language": source_lang,
        "format": "json",
        "limit": 1,
    }
    resp = requests.get(url, params=params, headers=HEADERS, timeout=10)
    resp.raise_for_status()
    results = resp.json().get("search", [])
    return results[0]["id"] if results else None


def resolve_titles(query: str, langs: list[str], source_lang: str = "en") -> dict[str, str]:
    titles: dict[str, str] = {}
    qid = resolve_qid(query, source_lang)

    if qid:
        url = "https://www.wikidata.org/w/api.php"
        params = {
            "action": "wbgetentities",
            "ids": qid,
            "props": "sitelinks",
            "format": "json",
        }
        resp = requests.get(url, params=params, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        entity = resp.json()["entities"][qid]
        sitelinks = entity.get("sitelinks", {})
        for lang in langs:
            site_key = f"{lang}wiki"
            if site_key in sitelinks:
                titles[lang] = sitelinks[site_key]["title"]

    for lang in [l for l in langs if l not in titles]:
        fallback = _opensearch_fallback(query, lang)
        if fallback:
            titles[lang] = fallback

    return titles


def _opensearch_fallback(query: str, lang: str) -> str | None:
    url = f"https://{lang}.wikipedia.org/w/api.php"
    params = {
        "action": "opensearch",
        "search": query,
        "limit": 1,
        "namespace": 0,
        "format": "json",
    }
    try:
        resp = requests.get(url, params=params, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if len(data) > 1 and data[1]:
            return data[1][0]
    except Exception:
        pass
    return None


def fetch_pageviews(article: str, lang: str, years: int = 2, retries: int = 3) -> list[dict]:
    end_date = datetime.now() - timedelta(days=1)
    start_date = end_date - timedelta(days=years * 365)

    start_str = start_date.strftime("%Y%m%d00")
    end_str = end_date.strftime("%Y%m%d00")

    slug = urllib.parse.quote(article.replace(" ", "_"), safe="")
    url = (
        f"https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/"
        f"{lang}.wikipedia/all-access/user/{slug}/daily/{start_str}/{end_str}"
    )

    last_error = None
    for attempt in range(retries):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            if resp.status_code == 404:
                raise ValueError(f"Статтю '{article}' не знайдено у {lang}.wikipedia.")
            if resp.status_code == 429:
                time.sleep(2 ** attempt)
                continue
            resp.raise_for_status()
            items = resp.json().get("items", [])
            result = []
            for item in items:
                ts = item["timestamp"][:8]
                result.append({
                    "date": datetime.strptime(ts, "%Y%m%d").strftime("%Y-%m-%d"),
                    "views": int(item["views"])
                })
            return result
        except ValueError:
            raise
        except requests.RequestException as e:
            last_error = e
            time.sleep(2 ** attempt)

    raise RuntimeError(f"Не вдалося отримати дані для {lang}.wikipedia/{article}: {last_error}")
