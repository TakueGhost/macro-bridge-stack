import os
from fredapi import Fred
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

def fetch_macro_data():
    fred = Fred(api_key=os.getenv("FRED_API_KEY"))
    
    series = {
        "yield_curve": "T10Y2Y",
        "cpi": "CPIAUCSL",
        "unemployment": "UNRATE",
        "payrolls": "PAYEMS",
        "industrial_production": "INDPRO"
    }
    
    data = {}
    for name, series_id in series.items():
        data[name] = fred.get_series(series_id, observation_start="2020-01-01")
    
    return data