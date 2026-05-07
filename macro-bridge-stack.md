\# Macro Bridge Stack - Technical Context



\## Location

C:\\Users\\tkchi\\macro\_bridge\_stack



\## Virtual Environment

Activate: source venv/Scripts/activate

Run from: \~/macro\_bridge\_stack



\## API Keys (stored in .env)

\- FRED\_API\_KEY: Federal Reserve data

\- ANTHROPIC\_API\_KEY: Direct Claude access (billing issue, use OpenRouter instead)

\- OPENROUTER\_API\_KEY: Active workaround for Claude Sonnet

\- HUGGINGFACE\_API\_KEY: FinBERT inference via HuggingFace API



\## Current State

Agent 1: COMPLETE

\- File: agent1/main.py

\- Pulls 5 FRED indicators: yield curve (T10Y2Y), CPI (CPIAUCSL), 

&#x20; unemployment (UNRATE), payrolls (PAYEMS), industrial production (INDPRO)

\- Voting ensemble: yield curve gets 2 votes, others get 1

\- Outputs: Expansion, Late Cycle, Stagflation, Contraction, Crisis

\- Saves: regime\_memo\_YYYY-MM-DD.txt



Agent 2: COMPLETE

\- File: agent2/main.py

\- 9 companies: JPM, GS, BAC (financials), CAT, HON, MMM (industrials), 

&#x20; XOM, CVX, SLB (energy)

\- Data source: SEC EDGAR 8-K filings

\- Scores: FinBERT sentiment, uncertainty index, forward-looking ratio, 

&#x20; specificity score, composite confidence

\- Flags regime contradictions

\- Saves: narrative\_report\_YYYY-MM-DD.txt



Agent 3: NOT STARTED

\- Plan: alternative data miner

\- Job posting scraper detecting what companies do vs say

\- Extension of AAON thesis job posting discovery methodology



Agent 4: NOT STARTED

\- Plan: EM sovereign stress scorer

\- Uses NhauFinance once trained

\- Covers: SARB, CBN, BOG, CBK, RBZ



Orchestrator: NOT STARTED

\- Will combine all agents into one weekly memo

\- Publish to Substack automatically



\## Weekly Workflow

Every Monday:

1\. python agent1/main.py

2\. python agent2/main.py

3\. Review outputs in macro\_bridge\_stack folder

4\. Edit and publish to Takue Unhedged on Substack



\## Known Issues

\- Anthropic direct API billing not activating, using OpenRouter as workaround

\- FRED occasionally returns HTTP 500 errors, just re-run

\- FinBERT via HuggingFace free tier can be slow, wait 30 seconds between runs



\## Next Priority

Upgrade Agent 1 voting ensemble to Markov-switching dynamic factor model

Reference: Chauvet and Piger (2008) - Journal of Business and Economic Statistics

This produces regime probabilities instead of just regime labels

