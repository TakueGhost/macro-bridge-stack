import io
import time
import requests
import pandas as pd
from bs4 import BeautifulSoup
from agent3.config import LOOKBACK_DAYS, REQUEST_DELAY

HEADERS = {"User-Agent": "MacroBridgeStack/1.0 tkchirindo@gmail.com"}

CA_WARN_PAGE = "https://edd.ca.gov/en/Jobs_and_Training/Layoff_Services_WARN"
NY_WARN_PAGE = "https://dol.ny.gov/warn-notices"
_ca_cache = None
_ny_cache = None

def _fetch_ca() -> pd.DataFrame:
    try:
        r = requests.get(CA_WARN_PAGE, headers=HEADERS, timeout=20)
        soup = BeautifulSoup(r.text, "html.parser")
        xlsx_url = None
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if ".xlsx" in href.lower() and "warn" in href.lower():
                xlsx_url = href if href.startswith("http") else "https://edd.ca.gov" + href
                break
        if not xlsx_url:
            print("CA WARN: could not find Excel file link")
            return pd.DataFrame()
        resp = requests.get(xlsx_url, headers=HEADERS, timeout=30)
        xls = pd.ExcelFile(io.BytesIO(resp.content), engine="openpyxl")
        print(f"CA WARN sheets: {xls.sheet_names}")
        df = pd.read_excel(xls, sheet_name=2, header=0)
        df.columns = [str(c).strip().lower() for c in df.columns]
        df = df.dropna(how="all")
        _ca_cache = df
        return df
    except Exception as e:
        print(f"CA WARN fetch failed: {e}")
        return pd.DataFrame()


def _fetch_ny() -> pd.DataFrame:
    global _ny_cache
    if _ny_cache is not None:
        return _ny_cache
    try:
        r = requests.get(NY_WARN_PAGE, headers=HEADERS, timeout=20)
        soup = BeautifulSoup(r.text, "html.parser")
        table = soup.find("table")
        if not table:
            print("NY WARN: no table found on page")
            return pd.DataFrame()
        rows = []
        headers_row = [th.get_text(strip=True).lower() for th in table.find_all("th")]
        for tr in table.find_all("tr")[1:]:
            cells = [td.get_text(strip=True) for td in tr.find_all("td")]
            if cells:
                rows.append(dict(zip(headers_row, cells)))
        _ny_cache = pd.DataFrame(rows)
        return _ny_cache
    except Exception as e:
        print(f"NY WARN fetch failed: {e}")
        return pd.DataFrame()


def fetch(company: dict) -> list[dict]:
    name = company["name"].split("(")[0].strip().lower()
    keywords = [name] + [t.lower() for t in company.get("contract_terms", [])]

    hits = []
    for source_name, df in [("warn_ca", _fetch_ca()), ("warn_ny", _fetch_ny())]:
        if df.empty:
            time.sleep(REQUEST_DELAY)
            continue

        text_cols = [c for c in df.columns if any(
            k in c for k in ["company", "employer", "name", "firm"]
        )]
        if not text_cols:
            text_cols = list(df.columns[:2])

        date_col    = next((c for c in df.columns if "date" in c or "notice" in c), None)
        layoff_col  = next((c for c in df.columns if any(
            k in c for k in ["layoff", "employee", "worker", "affected", "no."]
        )), None)
        company_col = text_cols[0] if text_cols else None

        for _, row in df.iterrows():
            row_text = " ".join(str(row.get(c, "")) for c in text_cols).lower()
            if not any(kw.split()[0] in row_text for kw in keywords if kw):
                continue
            hits.append({
                "source":             source_name,
                "ticker":             company["ticker"],
                "company_name":       str(row.get(company_col, "")) if company_col else "",
                "date":               str(row.get(date_col, "")) if date_col else "",
                "employees_affected": str(row.get(layoff_col, "")) if layoff_col else "",
                "raw":                row.to_dict(),
            })

        time.sleep(REQUEST_DELAY)

    return hits
