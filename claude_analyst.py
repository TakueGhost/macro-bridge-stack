import os
import requests
from dotenv import load_dotenv

load_dotenv()

def get_claude_analysis(regime, regime_probs, indicators):
    """
    Generate institutional research memo via Claude (OpenRouter).

    Parameters
    ----------
    regime       : str   -- dominant regime label
    regime_probs : dict  -- probability vector over five regimes
    indicators   : dict  -- full indicator snapshot from classify_regime()
    """

    rp_traj  = indicators.get("recession_prob_3m_trajectory", [])
    conf_str = (
        f"{rp_traj[0]} -> {rp_traj[1]} -> {rp_traj[2]}"
        if len(rp_traj) == 3 else str(rp_traj)
    )

    loadings = indicators.get("factor_loadings", {})
    loadings_str = ", ".join(
        f"{k}: {v:+.3f}" for k, v in loadings.items()
    )

    prob_lines = "\n".join(
        f"  {r:<15} {p:.4f} ({p*100:.1f}%)"
        for r, p in sorted(regime_probs.items(), key=lambda x: x[1], reverse=True)
    )

    prompt = f"""You are a macroeconomic research analyst writing for institutional investors.

REGIME CLASSIFICATION ENGINE: Chauvet-Piger (2008) Dynamic Factor Markov-Switching Model

Dominant Regime: {regime}
Regime Confidence Margin (top vs 2nd): {indicators.get('regime_confidence_margin', 'N/A')}

Five-Regime Probability Vector:
{prob_lines}

Markov-Switching Model Output:
- P(recession | all data): {indicators['recession_probability']}
- Recession prob 3-month trajectory: {conf_str}
- Confirmed state (80/20 threshold rule): {indicators['confirmed_state_80_20_rule'].upper()}
- P(stay in recession | in recession):  {indicators.get('transition_p_stay_recession', 'N/A')}
- P(stay in expansion | in expansion):  {indicators.get('transition_q_stay_expansion', 'N/A')}

Common Factor (NBER Coincident Variables):
- Factor value (current): {indicators['common_factor_current']}
- Explained variance: {indicators['factor_explained_variance_pct']}%
- Loadings: {loadings_str}

Key Macroeconomic Indicators:
- 10Y-2Y Yield Curve Spread: {indicators['yield_curve_spread']}%
- CPI Year-over-Year: {indicators['cpi_yoy_pct']}%
- Unemployment Rate: {indicators['unemployment_rate']}%
- Unemployment 3-Month Change: {indicators['unemployment_3m_change']} pp
- Nonfarm Payrolls MoM: {indicators['payrolls_mom_thousands']:,.0f}k jobs
- Industrial Production MoM: {indicators['industrial_production_mom_pct']}%

Write a 3-paragraph institutional research memo:

Paragraph 1: State the regime and the model's conviction level. Reference the recession probability, the 3-month trajectory, and what the common factor is signaling about the comovement structure of the real economy. Explain what the factor loadings reveal about which sectors are driving the cycle.

Paragraph 2: What this regime and the full probability vector imply for equity positioning, duration exposure, and credit spreads. Be specific about what the second-highest probability regime implies for tail-risk hedging. Reference the transition probabilities to discuss regime persistence.

Paragraph 3: The three most important risks that could shift the recession probability above the 0.80 threshold and trigger the confirmed recession call. Reference specific data releases and quantitative thresholds.

Tone: Bloomberg Intelligence meets Bridgewater Daily Observations. Precise, confident, no hedging language."""

    response = requests.post(
        url="https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
            "Content-Type":  "application/json",
        },
        json={
            "model":      "anthropic/claude-sonnet-4-5",
            "messages":   [{"role": "user", "content": prompt}],
            "max_tokens": 1200,
        },
    )

    return response.json()["choices"][0]["message"]["content"]
