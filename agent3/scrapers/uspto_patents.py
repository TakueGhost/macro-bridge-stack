def fetch(company: dict) -> list[dict]:
    print(f"USPTO patents: skipped for {company['ticker']} -- Google Patents blocks automated requests. Add Lens.org or SerpAPI key to enable.")
    return []