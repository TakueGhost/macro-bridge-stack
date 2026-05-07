import requests
from agent3.config import OPENROUTER_API_KEY, OPENROUTER_MODEL, OPENROUTER_URL
from agent3.signal_detector import CompanySignal


def _build_prompt(sig: CompanySignal, regime: str) -> str:
    items_text = ""
    for source, docs in sig.items.items():
        items_text += f"\n{source.upper()}:\n"
        for d in docs[:3]:
            title = d.get("title") or d.get("description") or d.get("form") or ""
            date  = d.get("date") or d.get("start_date") or d.get("filing_date") or d.get("period") or ""
            items_text += f"  - {date}: {str(title)[:120]}\n"

    regime_flag_text = (
        "This signal CONTRADICTS the current macro regime. That is the key insight."
        if sig.regime_flag else
        "This signal is consistent with the current macro regime."
    )

    narrative_flag_text = (
        "Management narrative from recent filings also contradicts this signal, adding further conviction."
        if sig.narrative_flag else ""
    )

    return f"""You are an institutional equity research analyst writing a signal brief for a portfolio manager.

Company: {sig.name} ({sig.ticker})
Sector: {sig.sector}
Current macro regime: {regime}
Conviction score: {sig.conviction}/10
Sources flagged: {', '.join(sig.sources)}

{regime_flag_text} {narrative_flag_text}

Raw signals detected:
{items_text}

Write a concise 3-5 sentence signal brief. Structure it as follows:
1. What the data is showing across the sources flagged.
2. Why this matters for {sig.ticker} specifically.
3. What the investment implication is -- long, short, or event-driven.

Rules:
- No bullet points. Write in flowing prose.
- No em dashes.
- Do not use phrases like "it is worth noting" or "it is important to note".
- Do not hedge excessively. State the signal clearly.
- Write as if you are handing this to a portfolio manager who has 30 seconds to read it.
- Maximum 120 words."""


def narrate(sig: CompanySignal, regime: str) -> str:
    prompt = _build_prompt(sig, regime)

    payload = {
        "model": OPENROUTER_MODEL,
        "max_tokens": 300,
        "messages": [{"role": "user", "content": prompt}],
    }

    try:
        r = requests.post(
            OPENROUTER_URL,
            json=payload,
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/TakueGhost",
                "X-Title": "MacroBridgeStack",
            },
            timeout=30,
        )
        if r.status_code != 200:
            print(f"OpenRouter error {r.status_code} for {sig.ticker}: {r.text[:200]}")
            return f"[Narrative generation failed for {sig.ticker}]"

        return r.json()["choices"][0]["message"]["content"].strip()

    except Exception as e:
        print(f"Narrator failed for {sig.ticker}: {e}")
        return f"[Narrative generation failed for {sig.ticker}]"
