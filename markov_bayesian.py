"""
markov_bayesian.py
Macro Bridge Stack -- Agent 1 Layer 2a

Implements Recommendation 5: Bayesian estimation of the 2-state
Markov-switching model via the Gibbs sampler algorithm in
Kim and Nelson (1998).

The two-state model identifies recession vs expansion in the common
factor series. It serves as the foundation for the Chauvet-Piger
(2008) threshold rule.

Algorithm overview per Kim-Nelson (1998):
  Each iteration cycles through four draws:
    1. State sequence  -- Forward-Filtering Backward-Sampling (Carter-Kohn)
    2. Transition matrix -- Dirichlet posterior
    3. Regime means      -- Normal-Normal conjugate posterior
    4. Regime variances  -- Inverse-Gamma posterior

  Recession probability = posterior mean of the state sequence draws,
  marginalizing over all parameter uncertainty.
"""

import numpy as np
import pandas as pd


def _normal_pdf(x, mu, sigma):
    sigma = max(float(sigma), 1e-8)
    return (1.0 / (sigma * np.sqrt(2.0 * np.pi))) * np.exp(
        -0.5 * ((x - mu) / sigma) ** 2
    )


def gibbs_sampler(y_series, n_iter=1000, n_burn=300, random_seed=42):
    """
    Bayesian Gibbs sampler for 2-state Markov-switching model.

    Parameters
    ----------
    y_series   : pd.Series  -- the common factor time series
    n_iter     : int        -- total MCMC iterations (default 1000)
    n_burn     : int        -- burn-in iterations to discard (default 300)
    random_seed: int        -- reproducibility seed

    Returns
    -------
    recession_prob_series : pd.Series
        P(recession | all data), one value per time period.
        This is the Rao-Blackwellized posterior mean over all draws.

    posterior : dict
        Posterior means and standard deviations for key parameters.
        Use these to assess estimation uncertainty.
    """
    np.random.seed(random_seed)

    y = y_series.values if hasattr(y_series, "values") else np.array(y_series)
    T = len(y)

    # ----------------------------------------------------------------
    # Initialise parameters
    # ----------------------------------------------------------------
    median_y    = np.median(y)
    rec_mask    = y < median_y
    exp_mask    = ~rec_mask

    mu = np.array([
        float(y[rec_mask].mean()) if rec_mask.sum() > 0 else -1.0,
        float(y[exp_mask].mean()) if exp_mask.sum() > 0 else  1.0,
    ])
    sigma = np.array([
        max(float(y[rec_mask].std()), 0.05) if rec_mask.sum() > 1 else 0.5,
        max(float(y[exp_mask].std()), 0.05) if exp_mask.sum() > 1 else 0.5,
    ])
    P = np.array([[0.90, 0.10],
                  [0.10, 0.90]])

    # ----------------------------------------------------------------
    # Storage (post burn-in only)
    # ----------------------------------------------------------------
    n_save               = n_iter - n_burn
    recession_prob_draws = np.zeros((n_save, T))
    mu_draws             = np.zeros((n_save, 2))
    P_draws              = np.zeros((n_save, 2, 2))
    save_idx             = 0

    for iteration in range(n_iter):

        # --------------------------------------------------------
        # Step 1: Forward-Filtering Backward-Sampling (FFBS)
        # --------------------------------------------------------
        alpha = np.zeros((T, 2))

        for t in range(T):
            liks = np.array([
                _normal_pdf(y[t], mu[k], sigma[k]) for k in range(2)
            ])
            pred = np.array([0.5, 0.5]) if t == 0 else P.T @ alpha[t - 1]
            joint = liks * pred
            denom = joint.sum()
            alpha[t] = joint / denom if denom > 1e-300 else np.array([0.5, 0.5])

        states      = np.zeros(T, dtype=int)
        states[T-1] = np.random.choice(2, p=alpha[T-1])

        for t in range(T - 2, -1, -1):
            weights = alpha[t] * P[:, states[t + 1]]
            w_sum   = weights.sum()
            weights = weights / w_sum if w_sum > 1e-300 else np.array([0.5, 0.5])
            states[t] = np.random.choice(2, p=weights)

        # --------------------------------------------------------
        # Step 2: Transition matrix -- Dirichlet posterior
        # Prior encodes persistence: Dirichlet(8, 2) for staying in regime
        # --------------------------------------------------------
        for i in range(2):
            n_ij        = np.array([
                float(np.sum((states[:-1] == i) & (states[1:] == j)))
                for j in range(2)
            ])
            alpha_prior = np.array([8.0, 2.0]) if i == 0 else np.array([2.0, 8.0])
            P[i]        = np.random.dirichlet(n_ij + alpha_prior)

        # --------------------------------------------------------
        # Step 3: Regime means -- Normal-Normal posterior
        # Prior: mu_k ~ N(prior_mean_k, prior_var)
        # --------------------------------------------------------
        prior_var   = 4.0
        prior_means = np.array([-1.0, 1.0])

        for k in range(2):
            y_k = y[states == k]
            n_k = len(y_k)
            if n_k > 0:
                sig2_k    = sigma[k] ** 2
                post_var  = 1.0 / (n_k / sig2_k + 1.0 / prior_var)
                post_mean = post_var * (
                    y_k.sum() / sig2_k + prior_means[k] / prior_var
                )
                mu[k] = np.random.normal(post_mean, np.sqrt(post_var))

        # Enforce convention: state 0 = recession (lower mean)
        if mu[0] > mu[1]:
            mu    = mu[::-1].copy()
            sigma = sigma[::-1].copy()
            P     = P[::-1, :][:, ::-1].copy()
            states = 1 - states

        # --------------------------------------------------------
        # Step 4: Regime variances -- Inverse-Gamma posterior
        # Prior: sigma^2 ~ IG(a0=3, b0=1)
        # --------------------------------------------------------
        a0, b0 = 3.0, 1.0
        for k in range(2):
            y_k = y[states == k]
            n_k = len(y_k)
            if n_k > 1:
                ss       = float(np.sum((y_k - mu[k]) ** 2))
                a_post   = a0 + n_k / 2.0
                b_post   = b0 + ss  / 2.0
                var_draw = 1.0 / np.random.gamma(a_post, 1.0 / b_post)
                sigma[k] = np.sqrt(np.clip(var_draw, 1e-6, 20.0))

        # --------------------------------------------------------
        # Save post burn-in
        # --------------------------------------------------------
        if iteration >= n_burn:
            recession_prob_draws[save_idx] = states.astype(float)
            mu_draws[save_idx]             = mu.copy()
            P_draws[save_idx]              = P.copy()
            save_idx += 1

    # ----------------------------------------------------------------
    # Posterior means
    # ----------------------------------------------------------------
    recession_probs = recession_prob_draws.mean(axis=0)

    posterior = {
        "mu_recession":          round(float(mu_draws[:, 0].mean()), 4),
        "mu_expansion":          round(float(mu_draws[:, 1].mean()), 4),
        "mu_recession_std":      round(float(mu_draws[:, 0].std()),  4),
        "mu_expansion_std":      round(float(mu_draws[:, 1].std()),  4),
        "p_stay_recession":      round(float(P_draws[:, 0, 0].mean()), 4),
        "p_stay_expansion":      round(float(P_draws[:, 1, 1].mean()), 4),
        "p_stay_recession_std":  round(float(P_draws[:, 0, 0].std()),  4),
        "p_stay_expansion_std":  round(float(P_draws[:, 1, 1].std()),  4),
        "n_draws_used":          n_save,
    }

    idx = y_series.index if hasattr(y_series, "index") else range(T)
    recession_prob_series = pd.Series(
        recession_probs, index=idx, name="recession_prob_bayesian"
    )

    return recession_prob_series, posterior
