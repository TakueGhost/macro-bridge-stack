"""
regime_hmm.py
Macro Bridge Stack -- Agent 1 Layer 2b

Implements Recommendation 2: replace the sigmoid expert-system mapping
with a proper 5-state Gaussian HMM learned from data.

The HMM is trained on a 2D feature matrix:
    [common_factor, cpi_deviation_from_trend]

States are initialized to economic prior centroids so that the EM
algorithm converges to economically interpretable regimes rather than
arbitrary clusters. The Hungarian algorithm (linear_sum_assignment)
then matches the learned state centroids back to regime names.

This separates cleanly from Layer 2a (the Bayesian 2-state model).
Layer 2a answers: are we in recession or expansion?
Layer 2b answers: which of the five regimes are we in, and with
                  what probability?
"""

import numpy as np
import pandas as pd
from hmmlearn.hmm import GaussianHMM
from scipy.optimize import linear_sum_assignment
import warnings
warnings.filterwarnings("ignore")

REGIME_NAMES = ["Expansion", "Late Cycle", "Stagflation", "Contraction", "Crisis"]


def _cpi_deviation_from_trend(data):
    """
    CPI YoY minus its 12-month rolling mean.
    Captures inflation pressure relative to recent trend, which is what
    regime transitions respond to, not the absolute CPI level.
    """
    cpi     = data["cpi"].dropna()
    cpi_yoy = ((cpi - cpi.shift(12)) / cpi.shift(12) * 100).dropna()
    trend   = cpi_yoy.rolling(12, min_periods=6).mean()
    return (cpi_yoy - trend).dropna()


def build_feature_matrix(factor_series, data):
    """
    Assemble the 2D input matrix for the HMM.

    Feature 1: common factor from Layer 1 (real activity)
    Feature 2: CPI deviation from trend (inflation pressure)

    Both are standardized to zero mean and unit variance so that
    the HMM's distance calculations are not distorted by scale.
    """
    cpi_dev      = _cpi_deviation_from_trend(data)
    common_dates = factor_series.index.intersection(cpi_dev.index)

    f = factor_series.loc[common_dates].values.astype(float)
    c = cpi_dev.loc[common_dates].values.astype(float)

    f = (f - f.mean()) / (f.std() + 1e-10)
    c = (c - c.mean()) / (c.std() + 1e-10)

    X = np.column_stack([f, c])
    return X, common_dates


def _economic_prior_means():
    """
    Prior centroids for the five regimes in [factor, cpi_dev] space.
    Both axes are standardized so units are in standard deviations.

    Expansion   : strong real activity, below-trend inflation
    Late Cycle  : moderate activity, above-trend inflation
    Stagflation : near-zero activity, high inflation pressure
    Contraction : negative activity, contained inflation
    Crisis      : severe contraction, deflationary pressure
    """
    return np.array([
        [ 1.5, -0.8],
        [ 0.5,  0.6],
        [-0.3,  1.4],
        [-1.2,  0.0],
        [-2.3, -0.8],
    ])


def _match_states_to_regimes(learned_means):
    """
    Hungarian algorithm assignment of learned HMM states to regime names.
    Minimizes total Euclidean distance between learned centroids and
    economic prior centroids.

    Returns
    -------
    state_to_regime_idx : dict  {hmm_state_int: regime_name_list_index}
    """
    prior  = _economic_prior_means()
    cost   = np.zeros((5, 5))
    for i in range(5):
        for j in range(5):
            cost[i, j] = float(np.linalg.norm(learned_means[i] - prior[j]))

    row_ind, col_ind = linear_sum_assignment(cost)
    return dict(zip(row_ind.tolist(), col_ind.tolist()))


def fit_regime_hmm(factor_series, data, n_restarts=8):
    """
    Fit a 5-state Gaussian HMM with economic initialization.

    Multiple random restarts guard against local optima.
    The best model (highest log-likelihood) is selected.

    Parameters
    ----------
    factor_series : pd.Series  -- common factor from Layer 1
    data          : dict       -- raw FRED data (for CPI)
    n_restarts    : int        -- number of random restarts (default 8)

    Returns
    -------
    regime_probs : pd.DataFrame
        Smoothed state probabilities, shape (T, 5), columns = REGIME_NAMES
    hmm_meta     : dict
        Convergence status, log-likelihood, learned centroids.
    """
    X, dates     = build_feature_matrix(factor_series, data)
    init_means   = _economic_prior_means()

    best_score   = -np.inf
    best_model   = None

    for restart in range(n_restarts):
        try:
            model = GaussianHMM(
                n_components=5,
                covariance_type="diag",
                n_iter=300,
                tol=1e-5,
                random_state=restart * 13,
                init_params="stc",
                params="stmc",
            )
            # Seed means to economic priors with small perturbation
            model.means_ = (
                init_means + np.random.default_rng(restart).normal(0, 0.15, init_means.shape)
            )
            model.fit(X)
            score = model.score(X)

            if score > best_score:
                best_score = score
                best_model = model

        except Exception:
            continue

    if best_model is None:
        probs = pd.DataFrame(
            np.ones((len(dates), 5)) / 5,
            index=dates,
            columns=REGIME_NAMES,
        )
        return probs, {"hmm_converged": False, "log_likelihood": None}

    raw_probs      = best_model.predict_proba(X)
    state_to_regime = _match_states_to_regimes(best_model.means_)

    reordered = np.zeros((len(dates), 5))
    for hmm_state, regime_idx in state_to_regime.items():
        reordered[:, regime_idx] += raw_probs[:, hmm_state]

    regime_probs = pd.DataFrame(reordered, index=dates, columns=REGIME_NAMES)

    hmm_meta = {
        "hmm_converged":   True,
        "log_likelihood":  round(float(best_score), 2),
        "n_restarts_used": n_restarts,
        "learned_centroids": {
            REGIME_NAMES[state_to_regime[k]]: {
                "factor":  round(float(best_model.means_[k, 0]), 3),
                "cpi_dev": round(float(best_model.means_[k, 1]), 3),
            }
            for k in range(5)
        },
    }

    return regime_probs, hmm_meta
