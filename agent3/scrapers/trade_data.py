import time
import requests
from datetime import datetime
from agent3.config import CENSUS_TRADE_BASE, REQUEST_DELAY

HEADERS = {"User-Agent": "MacroBridgeStack/1.0 tkchirindo@gmail.com"}

SECTOR_HS_CODES = {
    "Industrials":           ["7213", "7214", "7217", "7301", "7312", "7314"],
    "Materials":             ["7213", "7214", "7217", "2823", "3206", "2804"],
    "Energy":                ["2709", "2710", "2711", "8413", "8432"],
    "Defence and Aerospace": ["8802", "8803", "8804", "9301", "9306"],
    "Healthcare and Biotech":["3001", "3002", "3003", "3004", "3822", "9018"],
    "Technology":            ["8517", "8525", "8526", "8542", "9013"],
    "Financials":            [],
    "Consumer":              ["6101", "6201", "6401", "6403", "9504"],
}

IMPORT_BASE = f"{CENSUS_TRADE_BASE}/timeseries/intltrade/imports/hs"
EXPORT_BASE = f"{CENSUS_TRADE_BASE}/timeseries/intltrade/exports/hs"


def _latest_period() -> str:
    now = datetime.today()
    month = now.month - 6
    year  = now.year
    if month <= 0:
        month += 12
        year  -= 1
    return f"{year}-{str(month).zfill(2)}"


def _fetch_hs(hs: str, period: str, flow: str) -> dict | None:
    if flow == "import":
        url     = IMPORT_BASE
        val_key = "GEN_VAL_MO"
        qty_key = "GEN_QY1_MO"
    else:
        url     = EXPORT_BASE
        val_key = "ALL_VAL_MO"
        qty_key = "QY1"

    params = {
        "get":         f"{val_key},{qty_key}",
        "I_COMMODITY": hs,
        "time":        period,
    }
    try:
        r = requests.get(url, params=params, headers=HEADERS, timeout=15)
        if r.status_code != 200:
            return None
        rows = r.json()
        if not rows or len(rows) < 2:
            return None
        hdr  = [str(h).lower() for h in rows[0]]
        data = dict(zip(hdr, rows[1]))
        return {
            "value_usd": data.get(val_key.lower(), ""),
            "quantity":  data.get(qty_key.lower(), ""),
        }
    except Exception:
        return None


def fetch(company: dict) -> list[dict]:
    sector   = company.get("sector", "")
    hs_codes = SECTOR_HS_CODES.get(sector, [])
    if not hs_codes:
        return []

    period = _latest_period()
    hits   = []

    for hs in hs_codes[:3]:
        for flow in ["import", "export"]:
            result = _fetch_hs(hs, period, flow)
            if result:
                hits.append({
                    "source":    "trade_data",
                    "ticker":    company["ticker"],
                    "sector":    sector,
                    "hs_code":   hs,
                    "flow":      flow,
                    "period":    period,
                    "value_usd": result["value_usd"],
                    "quantity":  result["quantity"],
                })
            time.sleep(REQUEST_DELAY)

    return hits
