import time
import requests
from datetime import datetime, timedelta
from agent3.config import LOOKBACK_DAYS, REQUEST_DELAY

HEADERS = {"User-Agent": "MacroBridgeStack/1.0 tkchirindo@gmail.com"}
FR_BASE = "https://www.federalregister.gov/api/v1/documents.json"

OSHA_TEMPLATES = [
    "{name} OSHA citation",
    "{name} OSHA violation",
    "{name} OSHA penalty",
    "{name} occupational safety",
]

EPA_TEMPLATES = [
    "{name} EPA violation",
    "{name} EPA enforcement",
    "{name} EPA penalty",
    "{name} consent decree",
    "{name} PFAS",
    "{name} clean air act",
    "{name} clean water act",
]


def _search_fr(term: str, cutoff: str) -> list[dict]:
    params = [
        ("conditions[term]", term),
        ("conditions[publication_date][gte]", cutoff),
        ("fields[]", "title"),
        ("fields[]", "publication_date"),
        ("fields[]", "document_number"),
        ("fields[]", "type"),
        ("fields[]", "abstract"),
        ("fields[]", "html_url"),
        ("per_page", 5),
        ("order", "newest"),
    ]
    try:
        r = requests.get(FR_BASE, params=params, headers=HEADERS, timeout=15)
        if r.status_code != 200:
            return []
        return r.json().get("results", [])
    except Exception as e:
        print(f"OSHA/EPA search failed for '{term}': {e}")
        return []


def fetch(company: dict) -> list[dict]:
    cutoff = (datetime.today() - timedelta(days=LOOKBACK_DAYS)).strftime("%Y-%m-%d")
    name   = company["name"].split("(")[0].strip().split()[0]
    ticker = company["ticker"]
    hits   = []
    seen   = set()

    templates = OSHA_TEMPLATES + EPA_TEMPLATES
    for tmpl in templates:
        term = tmpl.format(name=name)
        src  = "osha" if "osha" in tmpl.lower() or "occupational" in tmpl.lower() else "epa"
        for doc in _search_fr(term, cutoff):
            doc_num = doc.get("document_number", "")
            if not doc_num or doc_num in seen:
                continue
            seen.add(doc_num)
            hits.append({
                "source":    src,
                "ticker":    ticker,
                "term":      term,
                "title":     doc.get("title", ""),
                "date":      doc.get("publication_date", ""),
                "type":      doc.get("type", ""),
                "abstract":  (doc.get("abstract") or "")[:400],
                "url":       doc.get("html_url", ""),
                "document_number": doc_num,
            })
        time.sleep(REQUEST_DELAY)

    return hits
