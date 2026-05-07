import time
import requests
from datetime import datetime, timedelta
from agent3.config import USASPENDING_BASE, LOOKBACK_DAYS, REQUEST_DELAY

HEADERS = {"User-Agent": "MacroBridgeStack/1.0 tkchirindo@gmail.com"}


def fetch(company: dict) -> list[dict]:
    cutoff = (datetime.today() - timedelta(days=LOOKBACK_DAYS)).strftime("%Y-%m-%d")
    today  = datetime.today().strftime("%Y-%m-%d")
    hits   = []
    seen   = set()

    for term in company["contract_terms"]:
        page = 1
        while True:
            payload = {
                "filters": {
                    "time_period": [{"start_date": cutoff, "end_date": today}],
                    "award_type_codes": ["A", "B", "C", "D"],
                    "recipient_search_text": [term],
                },
                "fields": [
                    "Award ID", "Recipient Name", "Award Amount",
                    "Awarding Agency", "Awarding Sub Agency",
                    "Award Type", "Description", "Period of Performance Start Date",
                    "Period of Performance Current End Date", "Contract Award Type",
                ],
                "page": page,
                "limit": 25,
                "sort": "Award Amount",
                "order": "desc",
            }
            try:
                r = requests.post(
                    f"{USASPENDING_BASE}/search/spending_by_award/",
                    json=payload,
                    headers=HEADERS,
                    timeout=20,
                )
                if r.status_code != 200:
                    print(f"USASpending error {r.status_code} for {company['ticker']} term '{term}'")
                    break

                data    = r.json()
                results = data.get("results", [])
                if not results:
                    break

                for rec in results:
                    award_id = rec.get("Award ID", "")
                    if not award_id or award_id in seen:
                        continue
                    seen.add(award_id)
                    hits.append({
                        "source":        "contracts",
                        "ticker":        company["ticker"],
                        "term_matched":  term,
                        "award_id":      award_id,
                        "recipient":     rec.get("Recipient Name", ""),
                        "amount":        rec.get("Award Amount", 0),
                        "agency":        rec.get("Awarding Agency", ""),
                        "sub_agency":    rec.get("Awarding Sub Agency", ""),
                        "award_type":    rec.get("Award Type", ""),
                        "description":   (rec.get("Description") or "")[:300],
                        "start_date":    rec.get("Period of Performance Start Date", ""),
                        "end_date":      rec.get("Period of Performance Current End Date", ""),
                        "url":           f"https://www.usaspending.gov/award/{award_id}",
                    })

                if page >= data.get("page_metadata", {}).get("last_page", 1):
                    break
                page += 1

            except Exception as e:
                print(f"USASpending fetch failed for {company['ticker']} term '{term}': {e}")
                break

            time.sleep(REQUEST_DELAY)

    return hits
