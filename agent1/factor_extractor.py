"""
factor_extractor.py
Macro Bridge Stack -- Agent 1 Layer 1

Extracts the latent common factor from the four NBER coincident variables
using PCA on standardized monthly growth rates.

Implements Recommendation 1 and Recommendation 3 jointly:
  - Recommendation 1: replace threshold voting with a latent common factor
  - Recommendation 3: the four coincident variables here are the ONLY
    inputs to the factor. CPI and yield curve are kept out entirely.
    They live in the leading indicator overlay in regime_classifier.py.
"""

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA


def extract_common_factor(data):
    """
    Extract the first principal component from the four NBER coincident
    variables as a proxy for the latent dynamic common factor in
    Chauvet-Piger (2008).

    Inputs (all from data dict, monthly FRED series):
        payrolls                     PAYEMS
        industrial_production        INDPRO
        manufacturing_trade_sales    CMRMTSPL
        personal_income_ex_transfers W875RX1

    Returns
    -------
    factor_series : pd.Series
        Standardized common factor, zero mean and unit variance.
    explained_var : float
        Share of variance captured by PC1. Above 0.50 = strong comovement.
    loadings : dict
        Factor loadings for each variable.
    """

    payrolls = data["payrolls"].dropna()
    indpro   = data["industrial_production"].dropna()
    mts      = data["manufacturing_trade_sales"].dropna()
    pix      = data["personal_income_ex_transfers"].dropna()

    df = pd.DataFrame({
        "payrolls": payrolls.diff() / payrolls.shift(1) * 100,
        "indpro":   indpro.pct_change() * 100,
        "mts":      mts.pct_change() * 100,
        "pix":      pix.pct_change() * 100,
    }).dropna()

    if len(df) < 36:
        raise ValueError(
            f"Only {len(df)} observations. Need at least 36 months."
        )

    scaler = StandardScaler()
    X      = scaler.fit_transform(df)

    pca    = PCA(n_components=1)
    raw    = pca.fit_transform(X).flatten()

    factor = (raw - raw.mean()) / (raw.std() + 1e-10)

    factor_series = pd.Series(factor, index=df.index, name="common_factor")
    explained_var = float(pca.explained_variance_ratio_[0])
    loadings      = dict(zip(df.columns, pca.components_[0]))

    return factor_series, explained_var, loadings
