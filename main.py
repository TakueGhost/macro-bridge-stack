import os
import sys
from datetime import date

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data_fetcher      import fetch_macro_data
from regime_classifier import classify_regime
from claude_analyst    import get_claude_analysis


def run_agent1():
    print("=" * 65)
    print("MACRO BRIDGE STACK -- AGENT 1: REGIME CLASSIFIER  (DFMS v3)")
    print("Chauvet-Piger (2008) + Kim-Nelson (1998) + 5-state HMM")
    print("=" * 65)

    print("\n[1/3] Fetching data from FRED...")
    data = fetch_macro_data()
    print(f"      Loaded: {list(data.keys())}")

    print("\n[2/3] Running full DFMS classification pipeline...")
    regime, regime_probs, indicators = classify_regime(data)

    print(f"\n      DOMINANT REGIME : {regime}")
    print(f"      Confidence margin: {indicators['regime_confidence_margin']}")

    print("\n      Five-regime probability vector:")
    for r, p in sorted(regime_probs.items(), key=lambda x: x[1], reverse=True):
        bar    = "█" * int(p * 35)
        marker = " <-- dominant" if r == regime else ""
        print(f"        {r:<15} {bar:<35} {p:.4f}{marker}")

    print("\n      Bayesian Markov-switching:")
    print(f"        P(recession | data)       : {indicators['recession_probability']}")
    print(f"        3-month trajectory        : {indicators['recession_prob_3m_trajectory']}")
    print(f"        Confirmed state (80/20)   : {indicators['confirmed_state_80_20_rule'].upper()}")
    print(f"        P(stay recession) mean/std: {indicators['posterior_p_stay_recession']} / {indicators['posterior_p_recession_std']}")
    print(f"        P(stay expansion)         : {indicators['posterior_p_stay_expansion']}")

    print("\n      Common factor:")
    print(f"        Explained variance: {indicators['factor_explained_variance_pct']}%")
    print(f"        Loadings          : {indicators['factor_loadings']}")

    print("\n      Leading indicators (not fed into model):")
    print(f"        Yield curve  : {indicators['yield_curve_spread']}%")
    print(f"        CPI YoY      : {indicators['cpi_yoy_pct']}%")
    print(f"        Unemployment : {indicators['unemployment_rate']}%")
    print(f"        Payrolls MoM : {indicators['payrolls_mom_thousands']:,.0f}k")

    print("\n[3/3] Generating memo via Claude...")
    memo = get_claude_analysis(regime, regime_probs, indicators)

    probs_str = "\n".join(
        f"  {r:<15} {p:.4f}  ({p*100:.1f}%)"
        for r, p in sorted(regime_probs.items(), key=lambda x: x[1], reverse=True)
    )

    output = f"""MACRO REGIME MEMO  (DFMS v3)
Week of {date.today()}
{"=" * 65}
DOMINANT REGIME: {regime}

{probs_str}

P(recession | data): {indicators['recession_probability']}
Confirmed state   : {indicators['confirmed_state_80_20_rule'].upper()}
{"=" * 65}

{memo}
"""

    filename = f"regime_memo_{date.today()}.txt"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(output)

    print(output)
    print(f"Saved to: {filename}")


if __name__ == "__main__":
    run_agent1()
