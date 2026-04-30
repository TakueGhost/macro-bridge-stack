COMPANY_UNIVERSE = {
    "financials": {
        "JPM": {"name": "JPMorgan Chase", "cik": "0000019617"},
        "GS":  {"name": "Goldman Sachs",  "cik": "0000886982"},
        "BAC": {"name": "Bank of America","cik": "0000070858"},
    },
    "industrials": {
        "CAT": {"name": "Caterpillar", "cik": "0000018230"},
        "HON": {"name": "Honeywell",   "cik": "0000773840"},
        "MMM": {"name": "3M",          "cik": "0000066740"},
    },
    "energy": {
        "XOM": {"name": "ExxonMobil", "cik": "0000034088"},
        "CVX": {"name": "Chevron",    "cik": "0000093410"},
        "SLB": {"name": "SLB",        "cik": "0000087347"},
    }
}

REGIME_EXPECTATIONS = {
    "Expansion": {
        "description": "Broad confidence, high specificity, aggressive forward guidance",
        "thresholds": {"min_sentiment": 0.55, "max_uncertainty": 12, "min_forward_looking": 0.35}
    },
    "Late Cycle": {
        "description": "Selective confidence, rising hedging, narrowing guidance",
        "thresholds": {"min_sentiment": 0.40, "max_uncertainty": 22, "min_forward_looking": 0.25}
    },
    "Stagflation": {
        "description": "Margin pressure language, cost hedging, cautious capex",
        "thresholds": {"min_sentiment": 0.25, "max_uncertainty": 30, "min_forward_looking": 0.15}
    },
    "Contraction": {
        "description": "Defensive posture, cost cutting, withdrawn guidance",
        "thresholds": {"min_sentiment": 0.15, "max_uncertainty": 35, "min_forward_looking": 0.10}
    },
    "Crisis": {
        "description": "Survival language, liquidity focus, no forward guidance",
        "thresholds": {"min_sentiment": 0.05, "max_uncertainty": 45, "min_forward_looking": 0.05}
    }
}

HEDGE_WORDS = [
    "approximately", "roughly", "around", "about", "may", "might", "could",
    "uncertain", "challenging", "headwinds", "volatile", "cautious", "difficult",
    "potential", "possible", "expect to", "hope to", "aim to", "subject to",
    "depending on", "if conditions", "assuming", "contingent", "risk", "concern"
]

FORWARD_WORDS = [
    "will", "expect", "anticipate", "forecast", "guidance", "outlook", "next quarter",
    "next year", "going forward", "we plan", "we intend", "target", "goal",
    "fiscal year", "second half", "remainder of", "full year"
]