import json
import os
from companies import REGIME_EXPECTATIONS

HISTORY_FILE = "data/narrative_history.json"

def load_history():
    if not os.path.exists(HISTORY_FILE):
        return {}
    with open(HISTORY_FILE, "r") as f:
        content = f.read().strip()
        return json.loads(content) if content else {}

def save_history(history):
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)

def store_scores(ticker, date, scores):
    history = load_history()
    if ticker not in history:
        history[ticker] = []
    
    history[ticker].append({"date": date, "scores": scores})
    history[ticker] = sorted(history[ticker], key=lambda x: x["date"])[-4:]
    
    save_history(history)

def compute_drift(ticker):
    history = load_history()
    records = history.get(ticker, [])
    
    if len(records) < 2:
        return None
    
    current = records[-1]["scores"]
    previous = records[-2]["scores"]
    
    drift = {}
    for key in current:
        drift[key] = round(current[key] - previous[key], 4)
    
    drift_summary = {
        "sentiment_drift": drift.get("sentiment_positive", 0),
        "uncertainty_drift": drift.get("uncertainty_index", 0),
        "forward_looking_drift": drift.get("forward_looking_ratio", 0),
        "specificity_drift": drift.get("specificity_score", 0),
        "confidence_drift": drift.get("composite_confidence", 0),
        "direction": "deteriorating" if drift.get("composite_confidence", 0) < -0.05
                     else "improving" if drift.get("composite_confidence", 0) > 0.05
                     else "stable"
    }
    
    return drift_summary

def check_regime_contradiction(ticker, scores, current_regime):
    expectations = REGIME_EXPECTATIONS.get(current_regime, {})
    thresholds = expectations.get("thresholds", {})
    
    contradictions = []
    
    if scores["sentiment_positive"] < thresholds.get("min_sentiment", 0):
        contradictions.append(
            f"Sentiment ({scores['sentiment_positive']:.2f}) below {current_regime} floor "
            f"({thresholds['min_sentiment']})"
        )
    
    if scores["uncertainty_index"] > thresholds.get("max_uncertainty", 100):
        contradictions.append(
            f"Uncertainty ({scores['uncertainty_index']:.2f}) above {current_regime} ceiling "
            f"({thresholds['max_uncertainty']})"
        )
    
    if scores["forward_looking_ratio"] < thresholds.get("min_forward_looking", 0):
        contradictions.append(
            f"Forward guidance ratio ({scores['forward_looking_ratio']:.2f}) below "
            f"{current_regime} floor ({thresholds['min_forward_looking']})"
        )
    
    return contradictions