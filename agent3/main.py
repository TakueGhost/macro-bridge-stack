import os
from datetime import datetime
from tqdm import tqdm

from agent3.config import COMPANIES, OUTPUT_DIR
from agent3.signal_detector import (
    CompanySignal, load_regime, load_narratives, detect_signals
)
from agent3.claude_narrator import narrate

from agent3.scrapers.federal_register import fetch as fetch_fr
from agent3.scrapers.sec_insider       import fetch as fetch_sec
from agent3.scrapers.contracts_scraper import fetch as fetch_contracts
from agent3.scrapers.warn_notices      import fetch as fetch_warn
from agent3.scrapers.uspto_patents     import fetch as fetch_patents
from agent3.scrapers.trade_data        import fetch as fetch_trade
from agent3.scrapers.osha_epa          import fetch as fetch_osha

SCRAPERS = [
    ("federal_register", fetch_fr),
    ("sec_insider",      fetch_sec),
    ("contracts",        fetch_contracts),
    ("warn_ca",          fetch_warn),
    ("uspto_patents",    fetch_patents),
    ("trade_data",       fetch_trade),
    ("osha",             fetch_osha),
    ("epa",              fetch_osha),
]


def run():
    print("\n=== MACRO BRIDGE STACK -- AGENT 3: ALTERNATIVE DATA ENGINE ===")
    print(f"Run date: {datetime.today().strftime('%Y-%m-%d %H:%M')}\n")

    regime     = load_regime()
    narratives = load_narratives()
    print(f"Macro regime loaded:    {regime}")
    print(f"Narrative scores loaded: {len(narratives)} companies\n")

    seen_scrapers = set()
    all_signals: list[CompanySignal] = []

    for company in tqdm(COMPANIES, desc="Scanning companies", unit="co"):
        ticker = company["ticker"]
        raw_items: dict[str, list] = {}

        for scraper_name, scraper_fn in SCRAPERS:
            if scraper_name in ("epa",):
                continue
            try:
                results = scraper_fn(company)
                if results:
                    raw_items[scraper_name] = results
            except Exception as e:
                print(f"\n  [{ticker}] {scraper_name} error: {e}")

        sig = CompanySignal(
            ticker  = ticker,
            name    = company["name"],
            sector  = company["sector"],
            sources = list(raw_items.keys()),
            items   = raw_items,
        )
        all_signals.append(sig)

    print(f"\nScanning complete. {len(all_signals)} companies processed.")

    flagged = detect_signals(all_signals, regime, narratives)
    print(f"High-conviction signals: {len(flagged)}\n")

    if not flagged:
        print("No signals above conviction threshold today.")
        _save_output("No signals above conviction threshold today.", regime)
        return

    lines = []
    lines.append(f"AGENT 3 -- ALTERNATIVE DATA SIGNALS")
    lines.append(f"Generated: {datetime.today().strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"Macro Regime: {regime}")
    lines.append(f"Companies scanned: {len(all_signals)}")
    lines.append(f"Signals flagged: {len(flagged)}")
    lines.append("=" * 70)

    for sig in tqdm(flagged, desc="Generating narratives", unit="signal"):
        narrative = narrate(sig, regime)

        lines.append(f"\n{sig.ticker} -- {sig.name}")
        lines.append(f"Sector: {sig.sector} | Conviction: {sig.conviction}/10")

        flags = []
        if sig.regime_flag:
            flags.append("REGIME CONTRADICTION")
        if sig.narrative_flag:
            flags.append("NARRATIVE CONTRADICTION")
        if flags:
            lines.append(f"Flags: {' | '.join(flags)}")

        lines.append(f"Sources: {', '.join(sig.sources)}")
        lines.append("")
        lines.append(narrative)
        lines.append("-" * 70)

        for source, docs in sig.items.items():
            lines.append(f"\n  [{source.upper()}] {len(docs)} item(s)")
            for d in docs[:3]:
                title = d.get("title") or d.get("description") or d.get("form") or d.get("publication_number") or ""
                date  = d.get("date") or d.get("start_date") or d.get("period") or ""
                url   = d.get("url", "")
                lines.append(f"    {date}  {str(title)[:100]}")
                if url:
                    lines.append(f"    {url}")

    output = "\n".join(lines)
    _save_output(output, regime)
    print(output)


def _save_output(content: str, regime: str):
    fname = f"alt_data_signals_{datetime.today().strftime('%Y-%m-%d')}.txt"
    path  = OUTPUT_DIR / "outputs" / "alt_data_signals" / fname
    os.makedirs(path.parent, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"\nOutput saved: {path}")


if __name__ == "__main__":
    run()
