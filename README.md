\# Macro Bridge Stack



A multi-agent AI system that automatically produces 

institutional-grade investment research every week.



\## What It Does



\*\*Agent 1 - Macro Regime Classifier\*\*

Pulls 5 economic indicators from the Federal Reserve (FRED) 

database and classifies the current economic cycle into one 

of five regimes: Expansion, Late Cycle, Stagflation, 

Contraction, or Crisis. Uses a transparent voting model 

where each indicator casts independent votes.



\*\*Agent 2 - Corporate Narrative Tracker\*\*

Reads official SEC EDGAR earnings filings for 9 major 

companies across financials, industrials, and energy. 

Scores corporate language on 5 dimensions using FinBERT 

(financial-domain NLP). Flags companies whose narrative 

contradicts the current macro regime.



\## Live Output - April 29, 2026



Regime detected: Late Cycle (4/6 votes)

\- Yield curve: +0.50%

\- CPI YoY: 3.32%

\- Unemployment: 4.3%

\- Payrolls MoM: +178k

\- Industrial Production MoM: -0.54%



All 9 companies contradicted the Late Cycle regime.

JPM and GS showed zero forward guidance -- flagged as 

pre-recessionary CEO behavior.



\## Tech Stack



\- Python 3.10+

\- fredapi, pandas, anthropic, python-dotenv

\- FinBERT via HuggingFace Inference API

\- OpenRouter API (Claude Sonnet)

\- SEC EDGAR public API

\- NLTK, BeautifulSoup4



\## Setup



```bash

git clone https://github.com/TakueGhost/macro-bridge-stack

cd macro-bridge-stack

python -m venv venv

source venv/Scripts/activate

pip install -r requirements.txt

```



Create a .env file with your API keys:

