import glob
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from agent3.config import AGENT1_DIR, AGENT2_DIR, OUTPUT_DIR

REGIME_KEYWORDS = {
    "Expansion":  ["expansion", "expanding"],
    "Late Cycle": ["late cycle", "late-cycle"],
    "Stagflation":["stagflation", "stagflationary"],
    "Contraction":["contraction", "contracting", "recessionary"],
    "Crisis":     ["crisis", "systemic stress"],
}

REGIME_BEARISH = {"Contraction", "Crisis", "Stagflation"}
REGIME_BULLISH = {"Expansion", "Late Cycle"}

POINTS_PER_SOURCE  = 1.25
REGIME_BONUS       = 2.0
NARRATIVE_BONUS    = 1.5
SCORE_CAP          = 10.0
CONVICTION_THRESHOLD = 6.0
MIN_SOURCES        = 2


@dataclass
class CompanySignal:
    ticker: str
    name: str
    sector: str
    sources: list = field(default_factory=list)
    items: dict  = field(default_factory=dict)
    conviction:  float = 0.0
    regime_flag: bool  = False
    narrative_flag: bool = False
    summary: str = ""


def load_regime() -> str:
    outputs = OUTPUT_DIR / "outputs"
    pattern = str(outputs / "regime_memos" / "regime_memo_*.txt")
    files = sorted(glob.glob(pattern))
    if not files:
        pattern = str(OUTPUT_DIR / "regime_memo_*.txt")
        files = sorted(glob.glob(pattern))
    if not files:
        print(f"No regime memo found in {outputs}")
        return "Unknown"
    latest = files[-1]
    text = Path(latest).read_text(encoding="utf-8", errors="ignore").lower()
    for regime, kws in REGIME_KEYWORDS.items():
        for kw in kws:
            if kw in text:
                return regime
    print(f"Regime memo found but regime state not parsed: {latest}")
    return "Unknown"


def load_narratives() -> dict:
    pattern = str(OUTPUT_DIR / "outputs" / "narrative_reports" / "narrative_report_*.txt")
    files = sorted(glob.glob(pattern))
    if not files:
        return {}
    latest = files[-1]
    text = Path(latest).read_text(encoding="utf-8", errors="ignore")
    scores = {}
    for line in text.splitlines():
        parts = line.strip().split()
        if len(parts) < 2:
            continue
        tok = parts[0].upper().rstrip(":")
        line_lower = line.lower()
        if "bearish" in line_lower or "negative" in line_lower or "contradiction" in line_lower:
            scores[tok] = "bearish"
        elif "bullish" in line_lower or "positive" in line_lower:
            scores[tok] = "bullish"
        elif "neutral" in line_lower:
            scores[tok] = "neutral"
    return scores


def score_signal(sig: CompanySignal, regime: str, narratives: dict) -> CompanySignal:
    n = len(sig.sources)
    if n < MIN_SOURCES:
        sig.conviction = 0.0
        return sig

    base = min(n * POINTS_PER_SOURCE, SCORE_CAP)

    regime_contradiction = False
    narrative_contradiction = False

    if regime in REGIME_BEARISH:
        bullish_sources = [s for s in sig.sources if "contract_win" in s or "patent" in s or "hiring" in s]
        if bullish_sources:
            regime_contradiction = True
    elif regime in REGIME_BULLISH:
        bearish_sources = [s for s in sig.sources if "warn" in s or "layoff" in s or "violation" in s or "enforcement" in s]
        if bearish_sources:
            regime_contradiction = True

    nar = narratives.get(sig.ticker.upper(), "neutral")
    if regime in REGIME_BEARISH and nar == "bullish":
        narrative_contradiction = True
    elif regime in REGIME_BULLISH and nar == "bearish":
        narrative_contradiction = True

    score = base
    if regime_contradiction:
        score += REGIME_BONUS
    if narrative_contradiction:
        score += NARRATIVE_BONUS

    score = min(score, SCORE_CAP)

    sig.conviction      = round(score, 2)
    sig.regime_flag     = regime_contradiction
    sig.narrative_flag  = narrative_contradiction
    return sig


def detect_signals(raw: list[CompanySignal], regime: str, narratives: dict) -> list[CompanySignal]:
    scored = [score_signal(s, regime, narratives) for s in raw]
    flagged = [s for s in scored if s.conviction >= CONVICTION_THRESHOLD]
    flagged.sort(key=lambda x: x.conviction, reverse=True)
    return flagged
