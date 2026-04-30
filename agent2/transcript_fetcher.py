import requests
import re
import time
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "MacroBridgeStack GWU-Research tkchirindo@gmail.com"}

def get_recent_filings(cik, count=2):
    cik_padded = str(int(cik)).zfill(10)
    url = f"https://data.sec.gov/submissions/CIK{cik_padded}.json"
    
    response = requests.get(url, headers=HEADERS)
    data = response.json()
    
    filings = data.get("filings", {}).get("recent", {})
    form_types = filings.get("form", [])
    accession_numbers = filings.get("accessionNumber", [])
    filing_dates = filings.get("filingDate", [])
    
    results = []
    for i, form in enumerate(form_types):
        if form == "8-K" and len(results) < count:
            results.append({
                "accession": accession_numbers[i],
                "date": filing_dates[i],
                "cik": str(int(cik))
            })
    
    return results

def fetch_filing_text(cik, accession_number):
    accession_clean = accession_number.replace("-", "")
    cik_int = str(int(cik))
    
    index_url = f"https://www.sec.gov/Archives/edgar/data/{cik_int}/{accession_clean}/{accession_number}-index.htm"
    
    time.sleep(0.5)
    response = requests.get(index_url, headers=HEADERS)
    
    if response.status_code != 200:
        return None
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    doc_url = None
    for link in soup.find_all('a', href=True):
        href = link['href']
        text = link.get_text().lower()
        if ('ex99' in href.lower() or 'ex-99' in href.lower() or
                'exhibit 99' in text or 'press release' in text):
            if href.endswith('.htm') or href.endswith('.html'):
                doc_url = f"https://www.sec.gov{href}"
                break
    
    if not doc_url:
        for link in soup.find_all('a', href=True):
            href = link['href']
            if (href.endswith('.htm') or href.endswith('.html')) and '/Archives/' in href:
                doc_url = f"https://www.sec.gov{href}"
                break
    
    if not doc_url:
        return None
    
    time.sleep(0.5)
    doc_response = requests.get(doc_url, headers=HEADERS)
    doc_soup = BeautifulSoup(doc_response.text, 'html.parser')
    
    text = doc_soup.get_text(separator=' ', strip=True)
    text = re.sub(r'\s+', ' ', text)
    
    return text[:40000]

def fetch_transcripts_for_company(ticker, cik, count=2):
    print(f"     Fetching {ticker}...")
    filings = get_recent_filings(cik, count)
    
    transcripts = []
    for filing in filings:
        text = fetch_filing_text(filing["cik"], filing["accession"])
        if text:
            transcripts.append({
                "ticker": ticker,
                "date": filing["date"],
                "text": text
            })
    
    return transcripts