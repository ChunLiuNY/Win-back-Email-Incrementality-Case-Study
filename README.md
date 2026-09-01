# Win-Back Email Incrementality: A Difference-in-Differences Case Study

## Business Question

An e-commerce company runs a win-back campaign: customers who haven't
purchased in 60+ days receive a re-engagement email. The targeting is not random, a CRM rule selects recipients based on their recency,
frequency, and monetary (RFM) history.

The campaign reports well. Targeted customers converted at **10.2%** over the
following quarter, against **7.4%** for lapsed customers who weren't
targeted, an apparent **2.88pp lift** the campaign takes credit for.

But that number is inflated by **selection bias**: recipients were chosen
because they are most valuable based on RFM history, so they were always the likelier group
to convert. But some lapsed customers could come back regardless.

**So how much of that 2.88pp lift did the campaign actually cause, and what should the
marketing team do differently once they know?**


## Findings

**The win-back campaign works, but it is worth meaningfully less than the reported lift (2.88pp) — somewhere between 12% and 31% of that lift is selection bias, not campaign effect.**

| Method | Incremental Conversion | 95% CI |
|---|---|---|
| Naive comparison | 2.88pp | — |
| **PSM + DiD (headline)** | **2.54pp** | [1.21, 3.87] |
| Regression Adjustment | 1.98pp | [1.43, 2.52] |
| Shortened-window DiD | 2.59pp | [1.92, 3.27] |
| **All three estimators consistent with** | **1.9 – 2.5pp** | |

Every method agrees the effect is real, positive, and smaller than the naive comparison suggests. How much smaller depends on which estimator you trust: the DiD variants put selection bias at 10–12% of the apparent lift, regression adjustment at 31%. Either way, some of that 2.88pp reflects customers who were coming back anyway, credited to an email that did not cause it.

The credibility here does not rest on any single estimate. Instead, we triangulate across approaches that rely on different assumptions and check whether they agree.

### The finding that should change what the team does

Further splitting by lapse depth:

| Segment (based on recency) | Targeted | Incremental Effect | 95% CI | p |
|---|---|---|---|---|
| Moderate (60–119d) | 17,084 | **+4.14pp** | [2.51, 5.76] | <0.0001 |
| Deep (≥120d) | 7,432 | **−1.09pp** | [−3.38, 1.20] | 0.35 |

The gap is real and the effect is concentrated in the moderate segment (60-119 inactive days; `lapse_bucket` was pre-specified in the data). Regression adjustment reproduces the same pattern (moderate +2.64pp, deep −0.12pp). For deep-lapse customers, the naive comparison shows 6.19% converting versus 5.79% of untargeted ones — a positive-looking 0.40pp lift that is incrementally indistinguishable from zero. Those customers were cycling back on their own; the email is taking credit for a trajectory it did not change..


## Method

### 1. Identification

Targeting was non-random, so comparing post-period levels confounds the
email's effect with who was selected to receive it. The **treated** group is the 24,516 lapsed customers the CRM rule picked to receive the win-back email; the **control** group is the 20,484 lapsed customers who were not picked by the CRM rule. Difference-in-differences (DiD) gets around this by comparing each group's change instead of its level, differncing away time-invariant confounders. 

That buys a different assumption in exchange: **parallel trends** — absent the
campaign, treated and control would have moved together.

**Treatment and control were not moving in parallel in pre-period.** A placebo test on the pre-period returned a significant "effect" (−1.22pp, p = 0.0008), and an event study with a joint F-test across all 11 pre-period leads rejected parallel trends at p = 0.0002. Why the assumption failed follows directly from how targeting worked: treated and control customers sit at systematically
different baseline RFM levels which lead to different purchase trajectories. That rules out plain DiD on the raw groups, so the analysis falls back on a weaker assumption - **Conditional parallel trends**: trends need only run parallel among customers with comparable RFM. Matching on pre-period RFM is how the estimation below satisfies it.

### 2. Estimation

We use propensity score matching (PSM) ahead of DiD: fit a logistic propensity
model on RFM, match each treated customer to their nearest control by propensity
score (1-NN, 0.2 SD caliper, with replacement), then run the DiD regression on
the matched sample, weighting reused controls by how often they were matched.

Matching cut RFM imbalance from **SMD ≈ 0.34 to ≈ 0.02**, and 100% of treated
customers found a match inside the caliper.

**PSM + DiD estimate: 2.54pp** [1.21, 3.87], p = 0.0002.

**Its identifying assumption was tested, and held.** After matching, the placebo
effect collapses to 0.04pp (p = 0.95) from −1.22pp on the raw groups, and the
event study says the same: the 11 pre-period leads no longer drift, and the
joint F-test that rejected before now cannot reject. Passing means failing to
detect a violation, not proving none exists, but it is a test this
specification could have failed, and did not.

![Event study: unmatched vs. PSM-matched sample](images/event_study_matched.png)

| sample | joint F-test | verdict |
|---|---|---|
| Unmatched | F(11) = 3.23, p = 0.0002 | reject parallel trends |
| PSM-matched | F(11) = 1.27, p = 0.24 | cannot reject parallel trends |

#### Triangulation

One passing diagnostic is not proof. Two further estimators check whether the
result survives.

**Shortened-window DiD** — restrict the pre-period to weeks −7 onward, where the
pre-period parallel trends violation was smallest, and rerun the identical specification. Estimate:
**2.59pp** [1.92, 3.27]; its own placebo comes back insignificant (−0.33pp,
p = 0.15). But this rests on the same parallel-trends assumption as PSM + DiD,
so the two were not likely to disagree. 

**Regression adjustment** — regress the post-period outcome on `treated` plus the
RFM covariates, with no pre-period and no time dimension at all. Estimate:
**1.98pp** [1.43, 2.52]. This is the check that can fail in a way the DiD variants cannot: it rests on
**unconfoundedness** — that RFM captures everything driving both targeting and
purchasing rather than on parallel trends. Being cross-sectional, it never
looks at the pre-period, so a pre-trend problem cannot contaminate it.

DiD handles unobserved time-invariant confounders but needs a trend assumption; regression adjustment needs no trend assumption but controls only for what was measured. Together they serve as triangulation: two methods whose weaknesses do not overlap, so both would have to fail in the same direction for the answer to be wrong. That they land within 0.6pp of each other (2.54pp vs. 1.98pp) corroborates the PSM + DiD estimate. 

Full diagnostics — covariate-balance tables, this event study, and placebo tests
at multiple cutoffs — are in `causal_analysis.ipynb`, sections 3–9.

### 3. Limitations

- **The PSM+DiD estimated interval is still narrow.** PSM + DiD's CI is [1.21, 3.87], nearly triple regression
  adjustment's width, because matching with replacement reuses 11,185 distinct
  controls to serve 24,516 treated customers — the effective sample is far
  smaller than the headline N. On top of that, PSM + DiD is a two-step
  estimator. The reported standard errors treat the matched sample as fixed, so
  they carry DiD's sampling uncertainty and none of the first stage's. The
  honest interval is wider than the one reported.
- **The identifying assumption is weaker, not absent.** Matching buys
  conditional parallel trends rather than the raw-group version that failed,
  but it still has to hold. The event study cannot reject it, and a test that
  fails to reject is not a test that proves.
- **Only RFM was observed.** Matching and regression adjustment can balance
  only what is in the data. Other covariates such as browse activity, email engagement history, tenure that could also predict purchasing will bias regression adjustment. DiD differences time-invariant covariates away;
  regression adjustment cannot, which is one reason the two estimates need not
  agree exactly.
- **No controls for time-varying confounders.** Differencing cannot remove anything that moved
  differently across the two groups during the campaign window, e.g., a competitor promotion landing on high-value customers, a seasonal swing that hits frequent buyers harder - is uncontrolled by either method. 

**What a randomized holdout would have given us.** All of the above is second-best identification. A randomized holdout (withholding the email from a random slice of the eligible list) would deliver the true effect with no parallel-trends assumption, no unconfoundedness assumption, and no triangulation required. Lewis & Reiley (2014) and Gordon et al. (2018) both show observational estimators can miss experimental benchmarks even with rich covariates. The recommendation below reflects that gap.

## Marketing Recommendations

*Cost assumption: sends are treated as costless.*

### What the campaign actually delivered

Across 24,516 emails, roughly **710 incremental conversions** — essentially all of them from the moderate-lapse segment. Deep-lapse contributed nothing measurable: its point estimate is negative, but not distinguishable from zero, so it is treated as zero here rather than subtracted. At zero cost, the campaign is unambiguously worth running. **Keep it.**

### 1. Depriortize deep-lapse as a win-back audience

30% of the list (7,432 customers) is deeply lapsed, and that group produced no detectable incremental conversions. Those could be customers who were returning regardless. Also every send to someone with no interest risks an unsubscribe, permanently removing a customer who may re-engage later through another channel. **Deprioritize deep-lapse from the standing win-back flow. Retain a small holdout there for ongoing measurement rather than dropping the segment blind.**

### 2. Expand into the moderate-lapse customers who were never targeted

**16,719 moderately-lapsed customers did not receive the email.** All of them fall inside the propensity-score range of the customers who were targeted, so extending to them is interpolation rather than extrapolation into unfamiliar territory. At the measured 4.14pp incremental effect, reaching them implies **roughly 690 additional incremental conversions** — approximately doubling what the campaign produced, at zero incremental cost. **Extend the campaign to untargeted moderate-lapse customers.**

### 3. Run a holdout — the single highest-value next step

Every number above rests on assumptions that cannot be fully verified: parallel trends assumption cannot be fully verified, and unconfoundedness is untestable in principle. The two estimator families still disagree by about 0.5pp (2.5pp vs 2.0pp), and this analysis cannot adjudicate it.

A randomized holdout resolves all of it - withhold the email from a random 10–20% of the newly-targeted moderate-lapse group. That yields an unbiased benchmark, costs nothing beyond forgone sends to a small slice, and validates or corrects every estimate here.



## Repo structure

```
.
├── causal_analysis.ipynb                     the full analysis
├── simulate.py                               the data-generating process
├── requirements.txt
└── README.md
```

`data/customers.csv` and `data/panel.csv` are not committed — they're fully
reproducible (seeded) via `simulate.py`.

## Data

The dataset is **simulated**, not real company data. The simulation targets realistic RFM
distributions and a non-random, recency/frequency/monetary-driven targeting
rule, so that the selection-bias problem is genuine rather than illustrative.
Conversion-rate base rates are plausible assumptions, not published
benchmarks, and shouldn't be quoted as industry figures.

## References

- Card, D. & Krueger, A. (1994). *Minimum Wages and Employment: A Case
  Study of the Fast-Food Industry in New Jersey and Pennsylvania.*
- Farahat, A. & Bailey, M. (2012). *How Effective is Targeted Advertising?*
- Lewis, R. & Reiley, D. (2014). *Online Ads and Offline Sales.*
- Gordon, B., Zettelmeyer, F., Bhargava, N. & Chapsky, D. (2018). *A
  Comparison of Approaches to Advertising Measurement: Evidence from Big
  Field Experiments at Facebook.*
- Ellickson, P., Kar, W. & Reeder, J. (2022). *Estimating Marketing
  Component Effects: Double Machine Learning from Targeted Digital
  Promotions.*
- Rambachan, A. & Roth, J. (2023). *A More Credible Approach to Parallel
  Trends.*
- Ascarza, E. (2018). *Retention Futility: Targeting High-Risk Customers
  Might Be Ineffective.*

