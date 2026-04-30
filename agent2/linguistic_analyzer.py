import os
import re
import requests
import nltk
from dotenv import load_dotenv
from companies import HEDGE_WORDS, FORWARD_WORDS

load_dotenv()

nltk.download('punkt', quiet=True)
nltk.download('punkt_tab', quiet=True)

HF_API_URL = "https://api-inference.huggingface.co/models/ProsusAI/finbert"

def run_finbert(text):
    headers = {"Authorization": f"Bearer {os.getenv('HUGGINGFACE_API_KEY')}"}
    
    sentences = nltk.sent_tokenize(text)
    sentences = [s for s in sentences if len(s.split()) > 5][:30]
    
    scores = {"positive": 0, "negative": 0, "neutral": 0}
    count = 0
    
    for sentence in sentences:
        response = requests.post(
            HF_API_URL,
            headers=headers,
            json={"inputs": sentence[:512]}
        )
        if response.status_code == 200:
            result = response.json()
            if isinstance(result, list) and len(result) > 0:
                for item in result[0]:
                    label = item["label"].lower()
                    if label in scores:
                        scores[label] += item["score"]
                count += 1
    
    if count == 0:
        return {"positive": 0.33, "negative": 0.33, "neutral": 0.34}
    
    total = sum(scores.values())
    return {k: round(v / total, 4) for k, v in scores.items()}

def compute_uncertainty_index(text):
    words = text.lower().split()
    total_words = len(words)
    if total_words == 0:
        return 0
    
    hedge_count = sum(1 for phrase in HEDGE_WORDS if phrase in text.lower())
    return round((hedge_count / total_words) * 100, 4)

def compute_forward_looking_ratio(text):
    sentences = nltk.sent_tokenize(text)
    if not sentences:
        return 0
    
    forward_count = sum(
        1 for s in sentences
        if any(w in s.lower() for w in FORWARD_WORDS)
    )
    return round(forward_count / len(sentences), 4)

def compute_specificity_score(text):
    sentences = nltk.sent_tokenize(text)
    if not sentences:
        return 0
    
    number_pattern = re.compile(r'\b\d+\.?\d*\s*(%|percent|billion|million|bps|basis points)\b', re.IGNORECASE)
    specific_count = sum(1 for s in sentences if number_pattern.search(s))
    
    return round(specific_count / len(sentences), 4)

def analyze_transcript(text):
    sentiment = run_finbert(text)
    uncertainty = compute_uncertainty_index(text)
    forward_looking = compute_forward_looking_ratio(text)
    specificity = compute_specificity_score(text)
    
    composite_confidence = round(
        (sentiment["positive"] * 0.4) +
        ((1 - uncertainty / 50) * 0.2) +
        (forward_looking * 0.2) +
        (specificity * 0.2),
        4
    )
    
    return {
        "sentiment_positive": sentiment["positive"],
        "sentiment_negative": sentiment["negative"],
        "sentiment_neutral": sentiment["neutral"],
        "uncertainty_index": uncertainty,
        "forward_looking_ratio": forward_looking,
        "specificity_score": specificity,
        "composite_confidence": composite_confidence
    }