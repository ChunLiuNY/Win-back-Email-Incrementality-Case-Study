"""
Data-generating process for the win-back email DiD project.

Design notes (see CLAUDE.md for the full business framing):
- Two tables: `customers` (one row per lapsed customer -- RFM features,
  targeting, ground-truth effect) and `panel` (customer x week purchase
  outcomes, 12 pre-weeks + 12 post-weeks).
- The outcome is a logistic model decomposed into a customer-specific
  LEVEL (`p_floor`, driven by `latent_quality` -- the source of selection
  bias, since targeting also depends on things correlated with quality)
  and a SHARED SHAPE function `A(t)` (decline into a trough approaching the
  campaign, partial recovery afterward) that is identical for every
  customer. This makes parallel trends true by construction on the logit
  scale while still producing a realistically non-flat trend.
- The true causal effect (`true_tau`) is added only for treated customers
  in the post-period, and is heterogeneous by how lapsed the customer is
  (Ascarza 2018 "retention futility": deeper-lapsed customers get a
  smaller true incremental effect).
- Ground truth (`true_tau`, `p_floor`, `latent_quality`) exists only for
  build-time power calibration and an optional appendix validation check --
  NOT the main analysis, which proceeds as if this were unknown (see
  CLAUDE.md "Credibility strategy: triangulation").
"""

import numpy as np
import pandas as pd

N_PRE = 12
N_POST = 12
PERIODS = list(range(-N_PRE, 0)) + list(range(1, N_POST + 1))  # -12..-1, 1..12


def _logit(p):
    return np.log(p / (1 - p))


def _sigmoid(x):
    return 1 / (1 + np.exp(-x))


def _zscore(x):
    return (x - x.mean()) / x.std()


def generate_customers(n=45_000, seed=42):
    rng = np.random.default_rng(seed)

    latent_quality = rng.normal(0, 1, n)

    # Frequency: purchases in trailing 12mo, right-skewed count, mean ~3.5/yr
    freq_lambda = np.exp(1.13 + 0.5 * latent_quality)
    frequency_pre = np.clip(rng.poisson(freq_lambda), 1, 20)

    # Monetary: historical avg order value, lognormal, median ~$55
    monetary_mu = np.log(55) + 0.2 * latent_quality
    monetary_pre = rng.lognormal(mean=monetary_mu, sigma=0.6)

    # Recency: days since last purchase, floored at 60 (eligibility cutoff)
    recency_theta = 32 * np.exp(-0.4 * latent_quality)
    recency_pre = 60 + rng.gamma(shape=1.3, scale=recency_theta)

    # p_floor: customer-specific baseline weekly purchase propensity (logit scale)
    floor_logit = -6.2 + 0.55 * latent_quality
    p_floor = _sigmoid(floor_logit)

    # True heterogeneous causal effect (log-odds) -- Ascarza "retention futility":
    # moderately-lapsed customers get a real effect, deeply-lapsed a much smaller one
    true_tau = np.maximum(0.05, 0.45 - 0.006 * (recency_pre - 60))

    # Targeting: non-random, based on standardized recency/frequency/monetary.
    # More-lapsed AND higher-value customers are prioritized -- a realistic
    # CRM rule, not a clean random holdout.
    propensity_logit = (
        0.2
        + 0.55 * _zscore(recency_pre)
        + 0.45 * _zscore(frequency_pre)
        + 0.35 * _zscore(monetary_pre)
    )
    propensity_true = _sigmoid(propensity_logit)
    treated = rng.binomial(1, propensity_true)

    lapse_bucket = np.where(recency_pre < 120, "moderate", "deep")

    customers = pd.DataFrame(
        {
            "customer_id": np.arange(n),
            "latent_quality": latent_quality,  # hidden -- not for analysis use
            "frequency_pre": frequency_pre,
            "monetary_pre": monetary_pre.round(2),
            "recency_pre": recency_pre.round(1),
            "p_floor": p_floor,
            "true_tau": true_tau,
            "propensity_true": propensity_true,
            "treated": treated,
            "lapse_bucket": lapse_bucket,
        }
    )
    return customers


def _shape_fn(t, decline_amp=2.55, tau_pre=4.0, recovery_amp=1.5, tau_post=5.0):
    """Shared trajectory shape (logit-scale add-on), identical across customers.

    Declines from `decline_amp` (12 weeks out) to 0 at the trough (week -1);
    partially recovers post-campaign toward `recovery_amp` (log-odds).
    """
    t = np.asarray(t, dtype=float)
    pre = decline_amp * (1 - np.exp((t + 1) / tau_pre))
    post = recovery_amp * (1 - np.exp(-t / tau_post))
    return np.where(t <= -1, pre, post)


def generate_panel(customers, seed=43):
    rng = np.random.default_rng(seed)

    floor_logit = _logit(customers["p_floor"].to_numpy())
    treated = customers["treated"].to_numpy()
    true_tau = customers["true_tau"].to_numpy()
    monetary_pre = customers["monetary_pre"].to_numpy()
    customer_id = customers["customer_id"].to_numpy()

    records = []
    for t in PERIODS:
        a_t = _shape_fn(t)
        is_post = t >= 1
        logit_p = floor_logit + a_t + np.where((treated == 1) & is_post, true_tau, 0.0)
        p = _sigmoid(logit_p)
        purchased = rng.binomial(1, p)
        order_value = np.where(
            purchased == 1,
            rng.lognormal(mean=np.log(monetary_pre), sigma=0.4),
            0.0,
        )
        records.append(
            pd.DataFrame(
                {
                    "customer_id": customer_id,
                    "period": t,
                    "is_post": int(is_post),
                    "purchased": purchased,
                    "order_value": order_value.round(2),
                }
            )
        )

    return pd.concat(records, ignore_index=True)


if __name__ == "__main__":
    customers = generate_customers()
    panel = generate_panel(customers)
    print(customers.describe())
    print(panel.groupby(["is_post"])["purchased"].mean())
