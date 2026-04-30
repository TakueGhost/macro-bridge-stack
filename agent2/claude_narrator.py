import os
import requests
from dotenv import load_dotenv

load_dotenv()

def generate_drift_report(company_results, current_regime):
    payload_text = f"Current Macro Regime (Agent 1): {current_regime}\n\n"
    
    for result in company_results:
        ticker = result["ticker"]
        sector = result["sector"]
        scores = result["scores"]
        drift = result.get("drift")
        contradictions = result.get("contradictions", [])
        
        payload_text += f"""
{ticker} ({sector.upper()})
  Composite Confidence: {scores['composite_confidence']}
  FinBERT Sentiment: +{scores['sentiment_positive']} / -{scores['sentiment_negative']}
  Uncertainty Index: {scores['uncertainty_index']}
  Forward-Looking Ratio: {scores['forward_looking_ratio']}
  Specificity Score: {scores['specificity_score']}
"""
        if drift:
            payload_text += f"  QoQ Drift: Confidence {drift['confidence_drift']:+.4f} ({drift['direction']})\n"
        
        if contradictions:
            payload_text += f"  REGIME CONTRADICTIONS: {'; '.join(contradictions)}\n"
        
        payload_text += "\n"
    
    prompt = f"""You are a senior equity research analyst at a top-tier hedge fund.

{payload_text}

Write an institutional narrative drift report with three sections:

SECTION 1 — REGIME ALIGNMENT SUMMARY
Which companies are behaving consistently with the {current_regime} macro regime? 
Which are contradicting it? Why does this matter for positioning?

SECTION 2 — NOTABLE DRIFT SIGNALS
Flag the two or three most significant quarter-over-quarter narrative shifts. 
A company becoming more vague while claiming confidence is a red flag. 
A company quietly reducing forward guidance is a leading indicator.
Be specific about which metrics moved and by how much.

SECTION 3 — INVESTMENT IMPLICATIONS
Given the regime contradictions and drift signals, what are the highest-conviction 
positioning implications across financials, industrials, and energy?
Name specific companies. State directional views with reasoning.

Tone: Bridgewater meets Goldman Research. No hedging language. Institutional precision."""

    response = requests.post(
        url="https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
            "Content-Type": "application/json"
        },
        json={
            "model": "anthropic/claude-sonnet-4-5",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 1500
        }
    )
    
    return response.json()["choices"][0]["message"]["content"]