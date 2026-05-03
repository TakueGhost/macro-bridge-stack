import os
from fredapi import Fred
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

def fetch_macro_data():
    fred = Fred(api_key=os.getenv("FRED_API_KEY"))

    series = {
        # --- NBER four coincident variables (Chauvet-Piger 2008 core) ---
        "payrolls":                     "PAYEMS",
        "industrial_production":        "INDPRO",
        "manufacturing_trade_sales":    "CMRMTSPL",
        "personal_income_ex_transfers": "W875RX1",

        # --- Leading / inflation overlay ---
        "yield_curve":                  "T10Y2Y",
        "cpi":                          "CPIAUCSL",
        "unemployment":                 "UNRATE",
    }

    data = {}
    for name, series_id in series.items():
        data[name] = fred.get_series(series_id, observation_start="2005-01-01")

    return data
