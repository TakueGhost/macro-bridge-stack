def classify_regime(data):
    yield_curve = data["yield_curve"].dropna().iloc[-1]
    
    cpi = data["cpi"].dropna()
    cpi_yoy = ((cpi.iloc[-1] - cpi.iloc[-13]) / cpi.iloc[-13]) * 100
    
    unemployment = data["unemployment"].dropna()
    unemployment_change = unemployment.iloc[-1] - unemployment.iloc[-4]
    
    payrolls = data["payrolls"].dropna()
    payrolls_mom = payrolls.iloc[-1] - payrolls.iloc[-2]
    
    indpro = data["industrial_production"].dropna()
    indpro_mom = ((indpro.iloc[-1] - indpro.iloc[-2]) / indpro.iloc[-2]) * 100
    
    votes = {
        "Expansion": 0,
        "Late Cycle": 0,
        "Stagflation": 0,
        "Contraction": 0,
        "Crisis": 0
    }
    
    if yield_curve > 0.5:
        votes["Expansion"] += 2
    elif yield_curve > 0:
        votes["Late Cycle"] += 2
    elif yield_curve > -0.5:
        votes["Contraction"] += 2
    else:
        votes["Crisis"] += 2
    
    if cpi_yoy < 2:
        votes["Contraction"] += 1
    elif cpi_yoy <= 4:
        votes["Expansion"] += 1
    elif cpi_yoy <= 6:
        votes["Stagflation"] += 1
        votes["Late Cycle"] += 1
    else:
        votes["Stagflation"] += 2
    
    if unemployment_change < -0.2:
        votes["Expansion"] += 1
    elif unemployment_change <= 0.1:
        votes["Late Cycle"] += 1
    elif unemployment_change <= 0.5:
        votes["Contraction"] += 1
    else:
        votes["Crisis"] += 2
    
    if payrolls_mom > 200:
        votes["Expansion"] += 1
    elif payrolls_mom > 0:
        votes["Late Cycle"] += 1
    elif payrolls_mom > -100:
        votes["Contraction"] += 1
    else:
        votes["Crisis"] += 2
    
    if indpro_mom > 0.3:
        votes["Expansion"] += 1
    elif indpro_mom > -0.1:
        votes["Late Cycle"] += 1
    else:
        votes["Contraction"] += 1
    
    regime = max(votes, key=votes.get)
    
    indicators = {
        "yield_curve_spread": round(yield_curve, 3),
        "cpi_yoy_pct": round(cpi_yoy, 2),
        "unemployment_rate": round(unemployment.iloc[-1], 1),
        "unemployment_3m_change": round(unemployment_change, 2),
        "payrolls_mom_thousands": round(payrolls_mom, 0),
        "industrial_production_mom_pct": round(indpro_mom, 3)
    }
    
    return regime, votes, indicators