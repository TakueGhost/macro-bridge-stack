import time
import requests
from datetime import datetime, timedelta
from agent3.config import FEDERAL_REGISTER_BASE, LOOKBACK_DAYS, REQUEST_DELAY


def fetch(company: dict) -> list[dict]:
    cutoff = (datetime.today() - timedelta(days=LOOKBACK_DAYS)).strftime("%Y-%m-%d")
    seen = set()
    hits = []

    for term in company["fr_terms"]:
        params = [
            ("conditions[term]", term),
            ("conditions[publication_date][gte]", cutoff),
            ("fields[]", "title"),
            ("fields[]", "publication_date"),
            ("fields[]", "document_number"),
            ("fields[]", "type"),
            ("fields[]", "abstract"),
            ("fields[]", "agencies"),
            ("fields[]", "html_url"),
            ("per_page", 20),
            ("order", "newest"),
        ]
        try:
            r = requests.get(
                f"{FEDERAL_REGISTER_BASE}.json",
                params=params,
                timeout=15
            )
            if r.status_code != 200:
                print(f"FR API error {r.status_code} for {company['ticker']} term '{term}'")
                time.sleep(REQUEST_DELAY)
                continue

            docs = r.json().get("results", [])
            for doc in docs:
                doc_num = doc.get("document_number")
                if not doc_num or doc_num in seen:
                    continue
                seen.add(doc_num)
                agencies = [a.get("name", "") for a in (doc.get("agencies") or [])]
                hits.append({
                    "source":          "federal_register",
                    "ticker":          company["ticker"],
                    "term_matched":    term,
                    "title":           doc.get("title", ""),
                    "date":            doc.get("publication_date", ""),
                    "type":            doc.get("type", ""),
                    "abstract":        (doc.get("abstract") or "")[:400],
                    "agencies":        ", ".join(agencies),
                    "url":             doc.get("html_url", ""),
                    "document_number": doc_num,
                })
        except Exception as e:
            print(f"FR fetch failed for {company['ticker']} term '{term}': {e}")

        time.sleep(REQUEST_DELAY)

    return hits
