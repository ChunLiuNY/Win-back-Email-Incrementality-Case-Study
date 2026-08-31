# Win-Back Email Incrementality: A Difference-in-Differences Case Study

## Business Question

An e-commerce company runs a win-back campaign: customers who haven't
purchased in 60+ days receive a re-engagement email. The targeting is not random, a CRM rule selects recipients based on their recency,
frequency, and monetary history.

The campaign reports well. Targeted customers converted at **10.2%** over the
following quarter, against **7.4%** for lapsed customers who weren't
targeted, an apparent **2.88pp lift** the campaign takes credit for.

But that number is inflated by **selection bias**: recipients were chosen
*because* they looked most valuable, so they were always the likelier group
to convert. And some lapsed customers could come back regardless.

**So how much of that 2.88pp did the campaign actually cause, and what should the
marketing team do differently once they know?**


## Findings

**The win-back campaign works, but it is worth meaningfully less than the reported lift — somewhere between 12% and 31% of that lift is selection bias, not campaign effect.**

| | Incremental Conversion | 95% CI |
|---|---|---|
| Naive (dashboard) comparison | 2.88pp | — |
| **PSM + DiD (preferred)** | **2.54pp** | [1.21, 3.87] |
| Shortened-window DiD | 2.59pp | [1.92, 3.27] |
| Regression Adjustment | 1.98pp | [1.43, 2.52] |
| **All three estimators consistent with** | **1.9 – 2.5pp** | |

Every method agrees the effect is real, positive, and smaller than the naive comparison. How much smaller depends on which estimator you trust: the DiD variants put selection bias at 10–12% of the apparent lift, regression adjustment at 31%. Either way, part of that 2.88pp is customers who were coming back anyway, credited to an email that did not cause it.

The credibility here does not rest on any single estimate. Shortened-window DiD is a **robustness check** - same identifying assumption, different handling of the problematic pre-period. Regression adjustment is **triangulation**. It rests on unconfoundedness rather than parallel trends, so it can fail independently. Its agreement is the part that matters.

### The finding that should change what the team does

Further splitting by lapse depth:

| segment | targeted | incremental effect | 95% CI | p |
|---|---|---|---|---|
| Moderate (60–119d) | 17,084 | **+4.14pp** | [2.51, 5.76] | <0.0001 |
| Deep (≥120d) | 7,432 | **−1.09pp** | [−3.38, 1.20] | 0.35 |

The gap is real, `lapse_bucket` was pre-specified in data. Regression adjustment reproduces the pattern independently (moderate +2.64pp, deep −0.12pp). Naive comparison shows deep-lapse customers converting at 6.19% versus 5.79% for untargeted ones - a positive-looking 0.40pp lift. Incrementally it is indistinguishable from zero. Those customers were cycling back on their own; the email is taking credit for a trajectory it did not change.


## Method

### 1. Identification strategy

Targeting was non-random, so comparing post-period *levels* confounds the
email's effect with who was selected to receive it. Difference-in-differences
compares each group's *change* instead — differencing away any customer trait
that is stable over time, whether or not it was measured.

That buys a different assumption in exchange: **parallel trends** — absent the
campaign, treated and control would have moved together.

**It was tested, and it failed.** A placebo test on the pre-period alone
returned a significant "effect" (−1.22pp, p = 0.0008), and a joint F-test on
all 11 pre-period leads rejected at p = 0.0002.

**Why it failed** follows directly from how targeting worked. The CRM rule
selected on RFM, so treated and control customers sit at systematically
different baseline RFM levels. And customers at different RFM levels follow
different purchase trajectories. 

**Conditional parallel trends** asks only that trends run parallel among
customers with *comparable* RFM, not across the raw groups — and matching on RFM
is how the estimation strategy below satisfies it.

### 2. Estimation strategy — PSM + DiD (headline)

Fit a logistic propensity model on RFM, match each treated customer to their
nearest control by propensity score (1-NN, 0.2 SD caliper, with replacement),
then run the DiD regression on the matched sample, weighting reused controls by
how often they were matched.

Matching drove covariate imbalance from **SMD ≈ 0.34 to ≈ 0.02**, with 100% of
treated customers finding a match inside the caliper.

**Why this is the headline spec, and not one of the other two:**

- **It is the only estimate whose own identifying assumption was tested and
  passed.** After matching, the placebo effect collapses from −1.22pp
  (p = 0.0008) to 0.04pp (p = 0.95), and the joint pre-trends test goes from
  rejecting to not rejecting.
- **It targets the diagnosed mechanism directly.** If baseline RFM imbalance is
  what broke parallel trends, equalising RFM is the fix aimed at that cause —
  not a generic robustness tweak.
- **It keeps DiD's structural advantage.** Differencing removes *unobserved*
  time-invariant confounders — brand affinity, tenure, channel preference —
  which a cross-sectional estimator cannot touch. In a real CRM system, targeting
  rules routinely use inputs absent from the analysis table, so this matters.

**The cost, stated plainly:** it carries the widest confidence interval of the
three (CI [1.21, 3.87], roughly triple regression adjustment's width). Matching
with replacement reuses 11,185 distinct controls to serve 24,516 treated
customers, so the effective sample behind the estimate is smaller than the
headcount suggests — a wider interval is the direct consequence. This spec is
chosen because its assumption survived testing, accepting a wider interval as
the trade.

![Event study: unmatched vs. PSM-matched sample](images/event_study_matched.png)

| sample | joint F-test | verdict |
|---|---|---|
| Unmatched | F(11) = 3.23, p = 0.0002 | reject parallel trends |
| PSM-matched | F(11) = 1.27, p = 0.24 | cannot reject parallel trends |

Individual matched-sample coefficients stay noisy (fewer distinct controls →
wider per-period error bars), so the chart alone is not decisive. Parallel
trends is a claim about *systematic drift*, not about every period sitting at
zero — and it is the drift that disappears: −0.038pp/wk before matching,
+0.006pp/wk after.

### 3. Robustness check — shortened-window DiD

Restrict the pre-period to the weeks where the violation was smallest and rerun
the same specification. Estimate: **2.59pp** [1.92, 3.27]; its own placebo test
comes back insignificant (−0.33pp, p = 0.15).

This asks a narrow question: *is the headline an artifact of how the bad
pre-period was handled?* It is **not** triangulation — it rests on the same
parallel-trends assumption as PSM + DiD, so the two were never likely to
disagree, and their agreement is weak evidence on its own.

### 4. Triangulation — regression adjustment

Regress the post-period outcome on `treated` plus the RFM covariates, with no
pre-period and no time dimension at all. Estimate: **1.98pp** [1.43, 2.52].

This is the check that carries evidential weight, because it can fail
*independently*. It rests on **unconfoundedness** — that RFM captures everything
driving both targeting and purchasing — rather than on parallel trends. Being
cross-sectional, it never looks at the pre-period, so the violation that broke
plain DiD cannot reach it.

Each method is therefore strong exactly where the other is weak: DiD handles
unobserved time-invariant confounders but needs a trend assumption; regression
adjustment needs no trend assumption but only controls for what is measured.
Their agreement (2.54pp vs. 1.98pp) is the central credibility claim — not the
two DiD variants agreeing with each other.

Full diagnostics (covariate-balance tables, this event study, and placebo tests
at multiple cutoffs) are in `causal_analysis.ipynb`, sections 3–9.

### Assumptions and limitations

Parallel trends failed the first test, and that shaped the entire analysis. **What fixed it, and how we know?** Matching on RFM drove covariate imbalance from SMD ≈ 0.34 to ≈ 0.02, and the matched-sample diagnostics cleared: placebo 0.04pp (p=0.95), joint F-test p=0.24, pre-period drift falling from −0.038pp/wk to +0.006pp/wk

**Assumptions the headline still rests on:**
- **Conditional parallel trends.** Tested and passed — though passing means *failing to detect* a violation, not proving none exists.
- **Unconfoundedness** (for the regression-adjustment leg). Untestable in principle. Credible here because targeting is a rule-based CRM process on observable RFM, but any unmeasured input to that rule, email engagement history, tenure, channel preference, would bias it. DiD differences such factors away if they are time-invariant; regression adjustment cannot.
- **No anticipation effects.** Customers did not change behaviour before receiving the email.
- **No spillovers.** Untargeted customers were unaffected by the campaign.

**Known weaknesses:**
- **The preferred estimate carries the widest interval.** PSM+DiD's CI is [1.21, 3.87], nearly triple regression adjustment's width — matching with replacement reuses 11,185 distinct controls to serve 24,516 treated customers, so the effective sample is smaller than the headcount implies. The spec was chosen because its assumption survived testing, with the wider interval accepted as the trade.
- **Regression adjustment is systematically lower** (1.98pp vs 2.54/2.59pp). The two DiD variants share an assumption, so their agreement was never independent evidence. Effectively there are two estimates — ~2.5pp from trend-based methods, ~2.0pp from the unconfoundedness-based one — and this analysis cannot fully adjudicate between them.
- **The deep-lapse subgroup is thin.** 7,432 treated matched against only 2,627 distinct controls, so its wide interval reflects limited power as much as a genuine null.

**Not implemented, and why:** formal sensitivity analysis (Rambachan & Roth 2023) requires the R-only `HonestDiD` package; synthetic DiD is built for few-units × many-periods panels, the opposite of this 45,000 × 24 shape. Both are cited as the rigorous treatments rather than approximated badly.

**What a randomized holdout would have given us.** All of the above is second-best identification. A randomized holdout — withholding the email from a random slice of the eligible list — would deliver the same estimate with no parallel-trends assumption, no unconfoundedness assumption, and no triangulation required. Lewis & Reiley (2014) and Gordon et al. (2018) both show observational estimators can miss experimental benchmarks even with rich covariates. The recommendation below reflects that gap.

## Marketing Recommendations

*Cost assumption: sends are treated as costless.*

### What the campaign actually delivered

Across 24,516 emails, roughly **710 incremental conversions** — essentially all of them from the moderate-lapse segment. Deep-lapse contributed nothing measurable: its point estimate is negative, but not distinguishable from zero, so it is treated as zero here rather than subtracted. At zero cost, the campaign is unambiguously worth running. **Keep it.**

### 1. Stop treating deep-lapse as a win-back audience

30% of the list (7,432 customers) is deeply lapsed, and that group produced no detectable incremental conversions. The naive comparison looks fine — 6.19% conversion versus 5.79% untargeted — but nearly all of that is customers who were returning regardless.

**At zero monetary cost, the argument to stop is not financial.** It is that email is never actually free:

- **Deliverability.** Sending to chronically unengaged addresses is precisely what inbox providers use to classify a sender as spam. That damage lands on *every* campaign, including the moderate-lapse sends that do work.
- **List attrition.** Every send to someone with no interest risks an unsubscribe, permanently removing a customer who may re-engage later through another channel.
- **Measurement distortion.** As long as deep-lapse stays in the campaign, blended reporting mixes a 4pp-effect segment with a 0pp-effect one and produces a number that describes neither.

**Recommendation:** remove deep-lapse from the standing win-back flow. Retain a small holdout there for ongoing measurement rather than dropping the segment blind.

### 2. Expand into the moderate-lapse customers who were never targeted

This is the largest opportunity in the analysis, and it is invisible in the naive framing.

**16,719 moderately-lapsed customers did not receive the email.** All of them fall inside the propensity-score range of the customers who were targeted, so extending to them is interpolation rather than extrapolation into unfamiliar territory.

At the measured 4.14pp incremental effect, reaching them implies **roughly 690 additional incremental conversions** — approximately doubling what the campaign produced, at zero incremental cost. **Treat that as an upper bound, not a forecast.** The untargeted group is systematically lower-value within the moderate bucket (frequency 3.3 vs 4.5, monetary $61 vs $79), and this analysis's own central finding is that effect size varies with customer profile — so a constant 4.14pp almost certainly overstates what they would deliver.

**Recommendation:** extend the campaign to untargeted moderate-lapse customers. **Roll it out as a randomized test, not a full send** — which also solves the measurement problem below.

### 3. The targeting logic is backwards, and that is the transferable lesson

The current rule prioritises customers by *how lapsed they are*. The data says incremental effect moves in the opposite direction: the further gone a customer is, the less an email changes their behaviour.

This is the Farahat & Bailey caution in a different guise. Their warning was about targeting customers who would convert anyway; here it is targeting customers who **will not convert regardless**. Both produce naive metrics that look reasonable and incremental value near zero. The common failure is optimising a targeting rule against *observed conversion* rather than *incremental conversion* — and those rank segments in genuinely different orders.

**Recommendation:** re-specify the targeting rule around estimated incremental response rather than lapse depth. Concretely: rank by predicted uplift, not by RFM score.

### 4. Run a holdout — the single highest-value next step

Every number above rests on assumptions that cannot be fully verified: parallel trends passed a placebo but was violated in the raw data, and unconfoundedness is untestable in principle. The two estimator families still disagree by about 0.5pp (2.5pp vs 2.0pp), and this analysis cannot adjudicate it.

A randomized holdout resolves all of it. **The expansion in recommendation 2 is the natural vehicle** — withhold the email from a random 10–20% of the newly-targeted moderate-lapse group. That yields an unbiased benchmark, costs nothing beyond forgone sends to a small slice, and validates or corrects every estimate here.

**Recommendation:** make the expansion a randomized rollout. There is no reason to run it any other way.


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

