import os
import sys
from datetime import date

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data_fetcher import fetch_macro_data
from regime_classifier import classify_regime
from claude_analyst import get_claude_analysis

def run_agent1():
    print("=" * 60)
    print("MACRO BRIDGE STACK — AGENT 1: REGIME CLASSIFIER")
    print("=" * 60)
    
    print("\n[1/3] Fetching data from FRED...")
    data = fetch_macro_data()
    print("     Done.")
    
    print("\n[2/3] Running regime classification...")
    regime, votes, indicators = classify_regime(data)
    
    print(f"\n     REGIME: {regime}")
    print(f"\n     Vote breakdown:")
    for r, v in sorted(votes.items(), key=lambda x: x[1], reverse=True):
        bar = "█" * v
        print(f"       {r:<15} {bar} ({v})")
    
    print(f"\n     Indicators:")
    for key, value in indicators.items():
        print(f"       {key}: {value}")
    
    print("\n[3/3] Generating research memo via Claude...")
    memo = get_claude_analysis(regime, votes, indicators)
    
    output = f"""MACRO REGIME MEMO
Week of {date.today()}
{"=" * 60}

REGIME: {regime}

INDICATOR SNAPSHOT:
  Yield Curve (10Y-2Y): {indicators['yield_curve_spread']}%
  CPI YoY:              {indicators['cpi_yoy_pct']}%
  Unemployment:         {indicators['unemployment_rate']}%
  Payrolls MoM:         {indicators['payrolls_mom_thousands']:,.0f}k
  Indust. Production:   {indicators['industrial_production_mom_pct']}%

{"=" * 60}

{memo}
"""
    
    filename = f"regime_memo_{date.today()}.txt"
    with open(filename, "w") as f:
        f.write(output)
    
    print("\n" + "=" * 60)
    print(output)
    print(f"\nMemo saved to: {filename}")

if __name__ == "__main__":
    run_agent1()