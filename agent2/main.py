import os
import sys
import glob
from datetime import date

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from companies import COMPANY_UNIVERSE
from transcript_fetcher import fetch_transcripts_for_company
from linguistic_analyzer import analyze_transcript
from narrative_tracker import store_scores, compute_drift, check_regime_contradiction
from claude_narrator import generate_drift_report

# ----------------------------------------------------------------
# Directory structure -- all paths relative to project root
# ----------------------------------------------------------------
AGENT2_DIR    = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR   = os.path.dirname(AGENT2_DIR)
MEMOS_DIR     = os.path.join(PROJECT_DIR, "outputs", "regime_memos")
REPORTS_DIR   = os.path.join(PROJECT_DIR, "outputs", "narrative_reports")

os.makedirs(REPORTS_DIR, exist_ok=True)


def get_current_regime():
    """
    Read the dominant regime from the most recent Agent 1 memo.
    Supports both v1 format (REGIME:) and v3 format (DOMINANT REGIME:).
    Always looks in outputs/regime_memos/ regardless of where you
    run this script from.
    """
    memos = glob.glob(os.path.join(MEMOS_DIR, "regime_memo_*.txt"))

    if not memos:
        print(f"  [WARN] No regime memos found in {MEMOS_DIR}")
        print(f"         Run Agent 1 first: cd ../agent1 && python main.py")
        return "Late Cycle"

    latest = sorted(memos)[-1]
    print(f"  Reading regime from: {os.path.basename(latest)}")

    with open(latest, "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("DOMINANT REGIME:"):
                return line.replace("DOMINANT REGIME:", "").strip()
            if line.startswith("REGIME:"):
                return line.replace("REGIME:", "").strip()

    return "Late Cycle"


def run_agent2():
    print("=" * 60)
    print("MACRO BRIDGE STACK -- AGENT 2: NARRATIVE TRACKER")
    print(f"Memos read from  : {MEMOS_DIR}")
    print(f"Reports saved to : {REPORTS_DIR}")
    print("=" * 60)

    current_regime = get_current_regime()
    print(f"\nCurrent Regime from Agent 1: {current_regime}")

    all_results = []

    for sector, companies in COMPANY_UNIVERSE.items():
        print(f"\n[{sector.upper()}]")

        for ticker, info in companies.items():
            transcripts = fetch_transcripts_for_company(ticker, info["cik"], count=2)

            if not transcripts:
                print(f"     {ticker}: No filings found, skipping")
                continue

            latest = transcripts[0]
            print(f"     Analyzing {ticker} ({latest['date']})...")

            scores        = analyze_transcript(latest["text"])
            store_scores(ticker, latest["date"], scores)
            drift         = compute_drift(ticker)
            contradictions = check_regime_contradiction(ticker, scores, current_regime)

            result = {
                "ticker":         ticker,
                "sector":         sector,
                "name":           info["name"],
                "date":           latest["date"],
                "scores":         scores,
                "drift":          drift,
                "contradictions": contradictions,
            }

            all_results.append(result)

            status    = "CONTRADICTION" if contradictions else "Aligned"
            direction = f"| Drift: {drift['direction']}" if drift else ""
            print(f"     {ticker}: Confidence={scores['composite_confidence']:.3f} {direction} | {status}")

    print(f"\n{'=' * 60}")
    print("Generating narrative drift report via Claude...")

    report = generate_drift_report(all_results, current_regime)

    output = f"""NARRATIVE DRIFT REPORT
Week of {date.today()}
Regime Context: {current_regime}
{"=" * 60}

{report}
"""

    filename = os.path.join(REPORTS_DIR, f"narrative_report_{date.today()}.txt")
    with open(filename, "w", encoding="utf-8") as f:
        f.write(output)

    print(f"\n{output}")
    print(f"Report saved to: {filename}")


if __name__ == "__main__":
    run_agent2()
