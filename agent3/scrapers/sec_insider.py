import time
import requests
from datetime import datetime, timedelta
from agent3.config import EDGAR_SUBMISSIONS_BASE, EDGAR_SEARCH_BASE, LOOKBACK_DAYS, REQUEST_DELAY

HEADERS = {"User-Agent": "MacroBridgeStack/1.0 tkchirindo@gmail.com"}


def _get_cik(ticker: str) -> str | None:
    try:
        r = requests.get(
            "https://efts.sec.gov/LATEST/search-index?q=%22"
            + ticker
            + "%22&dateRange=custom&startdt=2020-01-01&forms=10-K",
            headers=HEADERS,
            timeout=15,
        )
        hits = r.json().get("hits", {}).get("hits", [])
        if not hits:
            return None
        return hits[0].get("_source", {}).get("entity_id")
    except Exception as e:
        print(f"CIK lookup failed for {ticker}: {e}")
        return None


def _pad_cik(cik: str) -> str:
    return str(cik).zfill(10)


def fetch(company: dict) -> list[dict]:
    cik = company.get("cik")
    ticker = company["ticker"]

    if not cik:
        cik = _get_cik(ticker)
    if not cik:
        print(f"SEC: no CIK found for {ticker}, skipping")
        return []

    cik_padded = _pad_cik(cik)
    cutoff = datetime.today() - timedelta(days=LOOKBACK_DAYS)
    hits = []

    try:
        r = requests.get(
            f"{EDGAR_SUBMISSIONS_BASE}/CIK{cik_padded}.json",
            headers=HEADERS,
            timeout=15,
        )
        if r.status_code != 200:
            print(f"SEC submissions error {r.status_code} for {ticker}")
            return []

        data = r.json()
        recent = data.get("filings", {}).get("recent", {})
        forms      = recent.get("form", [])
        dates      = recent.get("filingDate", [])
        accessions = recent.get("accessionNumber", [])
        descriptions = recent.get("primaryDocument", [])

        for form, date_str, acc, doc in zip(forms, dates, accessions, descriptions):
            if form not in ("4", "SC 13D", "SC 13G", "SC 13D/A", "SC 13G/A"):
                continue
            try:
                filing_date = datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                continue
            if filing_date < cutoff:
                continue

            acc_clean = acc.replace("-", "")
            url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{acc_clean}/{doc}"

            hits.append({
                "source":  "sec_insider",
                "ticker":  ticker,
                "form":    form,
                "date":    date_str,
                "accession": acc,
                "url":     url,
            })

    except Exception as e:
        print(f"SEC fetch failed for {ticker}: {e}")

    time.sleep(REQUEST_DELAY)
    return hits
