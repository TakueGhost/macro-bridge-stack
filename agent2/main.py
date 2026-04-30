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

def get_current_regime():
    memos = glob.glob("regime_memo_*.txt")
    if not memos:
        return "Late Cycle"
    
    latest = sorted(memos)[-1]
    with open(latest, "r") as f:
        for line in f:
            if line.startswith("REGIME:"):
                return line.replace("REGIME:", "").strip()
    return "Late Cycle"

def run_agent2():
    print("=" * 60)
    print("MACRO BRIDGE STACK — AGENT 2: NARRATIVE TRACKER")
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
            
            scores = analyze_transcript(latest["text"])
            store_scores(ticker, latest["date"], scores)
            drift = compute_drift(ticker)
            contradictions = check_regime_contradiction(ticker, scores, current_regime)
            
            result = {
                "ticker": ticker,
                "sector": sector,
                "name": info["name"],
                "date": latest["date"],
                "scores": scores,
                "drift": drift,
                "contradictions": contradictions
            }
            
            all_results.append(result)
            
            status = "⚠ CONTRADICTION" if contradictions else "✓ Aligned"
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
    
    filename = f"narrative_report_{date.today()}.txt"
    with open(filename, "w") as f:
        f.write(output)
    
    print(f"\n{output}")
    print(f"Report saved to: {filename}")

if __name__ == "__main__":
    run_agent2()