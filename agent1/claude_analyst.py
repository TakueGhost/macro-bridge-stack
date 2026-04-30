import os
import requests
from dotenv import load_dotenv

load_dotenv()

def get_claude_analysis(regime, votes, indicators):
    prompt = f"""You are a macroeconomic research analyst writing for institutional investors.

Current Macro Regime: {regime}

Regime Vote Breakdown: {votes}

Key Indicators:
- 10Y-2Y Yield Curve Spread: {indicators['yield_curve_spread']}%
- CPI Year-over-Year: {indicators['cpi_yoy_pct']}%
- Unemployment Rate: {indicators['unemployment_rate']}%
- Unemployment 3-Month Change: {indicators['unemployment_3m_change']} percentage points
- Nonfarm Payrolls MoM: {indicators['payrolls_mom_thousands']:,.0f}k jobs
- Industrial Production MoM: {indicators['industrial_production_mom_pct']}%

Write a 3-paragraph institutional research memo:

Paragraph 1: State the regime clearly. Reference the specific numbers. Explain what the indicator combination is telling you about where we are in the cycle.

Paragraph 2: What this regime historically implies for equity positioning, duration exposure, and credit spreads. Be specific about asset class implications.

Paragraph 3: The three most important risks that could trigger a regime shift in the next 90 days. What specific data releases or thresholds to watch.

Tone: Bloomberg Intelligence meets Bridgewater Daily Observations. Precise, confident, no hedging language."""

    response = requests.post(
        url="https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
            "Content-Type": "application/json"
        },
        json={
            "model": "anthropic/claude-sonnet-4-5",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 1000
        }
    )

    return response.json()["choices"][0]["message"]["content"]