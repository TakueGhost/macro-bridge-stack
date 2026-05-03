"""
regime_classifier.py
Macro Bridge Stack -- Agent 1 v3

Orchestrates the full DFMS architecture across three layers.

Layer 1  factor_extractor.py  -- PCA common factor from NBER coincident vars
Layer 2a markov_bayesian.py   -- Bayesian 2-state MS, Kim-Nelson 1998 Gibbs
Layer 2b regime_hmm.py        -- 5-state HMM, regime probability vector
Layer 3  this file            -- Leading indicator overlay, Chauvet-Piger rule,
                                 final regime output and indicator snapshot

Separation enforced per Recommendation 3:
  Coincident layer : payrolls, industrial production, mfg trade sales, personal income
  Leading layer    : yield curve (leading), CPI (inflation overlay), unemployment
  These two groups are NEVER mixed as inputs to the same model component.
"""

import numpy as np
import pandas as pd
import warnings
warnings.filterwarnings("ignore")

from factor_extractor import extract_common_factor
from markov_bayesian  import gibbs_sampler
from regime_hmm       import fit_regime_hmm


def _apply_chauvet_piger_rule(recession_prob_series):
    """
    Two-step threshold rule from Chauvet-Piger (2008).

    Recession confirmed  : P(recession) >= 0.80, 3 consecutive months
    Expansion confirmed  : P(recession) <= 0.20, 3 consecutive months
    """
    recent = list(recession_prob_series.iloc[-3:])
    if len(recent) < 3:
        return "uncertain"
    if all(p >= 0.80 for p in recent):
        return "recession"
    if all(p <= 0.20 for p in recent):
        return "expansion"
    return "uncertain"


def _get_leading_indicators(data):
    """
    Recommendation 3: Leading and inflation indicators isolated
    from the coincident factor. Computed here and passed only to
    the Claude prompt, never to the HMM or the Gibbs sampler.
    """
    yc = float(data["yield_curve"].dropna().iloc[-1])

    cpi     = data["cpi"].dropna()
    cpi_yoy = float(((cpi.iloc[-1] - cpi.iloc[-13]) / cpi.iloc[-13]) * 100)

    unemp   = data["unemployment"].dropna()
    u_rate  = float(unemp.iloc[-1])
    u_3m    = float(unemp.iloc[-1] - unemp.iloc[-4])

    pay     = data["payrolls"].dropna()
    pay_mom = float(pay.iloc[-1] - pay.iloc[-2])

    ip      = data["industrial_production"].dropna()
    ip_mom  = float((ip.iloc[-1] - ip.iloc[-2]) / ip.iloc[-2] * 100)

    return {
        "yield_curve_spread":            round(yc, 3),
        "cpi_yoy_pct":                   round(cpi_yoy, 2),
        "unemployment_rate":             round(u_rate, 1),
        "unemployment_3m_change":        round(u_3m, 2),
        "payrolls_mom_thousands":        round(pay_mom, 0),
        "industrial_production_mom_pct": round(ip_mom, 3),
    }


def classify_regime(data):
    """
    Main entry point for Agent 1.

    Returns
    -------
    regime       : str   -- dominant regime (argmax of probability vector)
    regime_probs : dict  -- five-regime probability vector
    indicators   : dict  -- full snapshot for memo and Claude prompt
    """

    print("     [Rec 3]  Isolating leading indicators from coincident factor...")
    leading = _get_leading_indicators(data)

    print("     [Rec 1]  Layer 1 -- Extracting NBER coincident common factor...")
    factor_series, explained_var, loadings = extract_common_factor(data)
    print(f"              PC1 explains {explained_var:.1%} of coincident variance")
    print(f"              Loadings: { {k: round(v,3) for k,v in loadings.items()} }")

    print("     [Rec 5]  Layer 2a -- Bayesian Gibbs sampler (Kim-Nelson 1998)...")
    recession_prob_series, posterior = gibbs_sampler(factor_series)
    rp_current      = float(recession_prob_series.iloc[-1])
    rp_3m           = [round(float(p), 4) for p in recession_prob_series.iloc[-3:]]
    confirmed_state = _apply_chauvet_piger_rule(recession_prob_series)
    print(f"              P(recession | data) = {rp_current:.4f}")
    print(f"              Confirmed state (80/20): {confirmed_state.upper()}")

    print("     [Rec 2]  Layer 2b -- 5-state HMM regime probability vector...")
    regime_probs_df, hmm_meta = fit_regime_hmm(factor_series, data)

    raw   = regime_probs_df.iloc[-1].to_dict()
    total = sum(raw.values())
    regime_probs = {k: round(float(v) / total, 4) for k, v in raw.items()}

    regime      = max(regime_probs, key=regime_probs.get)
    sorted_p    = sorted(regime_probs.values(), reverse=True)
    conf_margin = round(sorted_p[0] - sorted_p[1], 4)

    indicators = {
        **leading,
        "common_factor_current":         round(float(factor_series.iloc[-1]), 4),
        "factor_explained_variance_pct": round(explained_var * 100, 1),
        "factor_loadings":               {k: round(v, 3) for k, v in loadings.items()},
        "recession_probability":         round(rp_current, 4),
        "recession_prob_3m_trajectory":  rp_3m,
        "confirmed_state_80_20_rule":    confirmed_state,
        "posterior_mu_recession":        posterior["mu_recession"],
        "posterior_mu_expansion":        posterior["mu_expansion"],
        "posterior_mu_recession_std":    posterior["mu_recession_std"],
        "posterior_p_stay_recession":    posterior["p_stay_recession"],
        "posterior_p_stay_expansion":    posterior["p_stay_expansion"],
        "posterior_p_recession_std":     posterior["p_stay_recession_std"],
        "hmm_converged":                 hmm_meta["hmm_converged"],
        "hmm_log_likelihood":            hmm_meta.get("log_likelihood"),
        "hmm_learned_centroids":         hmm_meta.get("learned_centroids", {}),
        "regime_confidence_margin":      conf_margin,
    }

    return regime, regime_probs, indicators
