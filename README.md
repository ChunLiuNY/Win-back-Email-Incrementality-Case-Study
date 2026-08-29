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

**The win-back campaign works, but it is worth about 12% less than the reported lift.**

| | Incremental Conversion | 95% CI |
|---|---|---|
| Naive (dashboard) comparison | 2.88pp | — |
| **PSM + DiD (preferred)** | **2.54pp** | [1.21, 3.87] |
| Shortened-window DiD | 2.59pp | [1.92, 3.27] |
| Regression Adjustment | 1.98pp | [1.43, 2.52] |
| **All three estimators consistent with** | **1.9 – 2.5pp** | |

Every method agrees the effect is real, positive, and smaller than the naive comparison. ~12% of the apparent lift is selection bias - customers who were coming back anyway, credited to an email that did not cause it.

The credibility here does not rest on any single estimate. Shortened-window DiD is a **robustness check** - same identifying assumption, different handling of the problematic pre-period. Regression adjustment is **triangulation**. It rests on unconfoundedness rather than parallel trends, so it can fail independently. Its agreement is the part that matters.

### The finding that should change what the team does

Further splitting by lapse depth:

| segment | targeted | incremental effect | 95% CI | p |
|---|---|---|---|---|
| Moderate (60–119d) | 17,084 | **+4.14pp** | [2.51, 5.76] | <0.0001 |
| Deep (≥120d) | 7,432 | **−1.09pp** | [−3.38, 1.20] | 0.35 |

The gap is real, `lapse_bucket` was pre-specified in data. Regression adjustment reproduces the pattern independently (moderate +2.64pp, deep −0.12pp). Naive comparison shows deep-lapse customers converting at 6.19% versus 5.79% for untargeted ones - a positive-looking 0.40pp lift. Incrementally it is indistinguishable from zero. Those customers were cycling back on their own; the email is taking credit for a trajectory it did not change.


## Method

The identification strategy is difference-in-differences: compare each
group's *change* in conversion rate (pre- vs. post-campaign), not just their
post-period levels. 

**The parallel-trends assumption was tested, not assumed, and it failed
the first test.** A placebo test on the pre-period alone returned a
significant "effect" (p < 0.001), and a formal joint pre-trends test
rejected at p = 0.0002. Rather than proceed on a violated assumption, the
analysis was rebuilt around three complementary strategies:

1. **Propensity-score matching + DiD** (headline spec): match treated and
   control customers on their pre-period RFM profile first, closing the
   baseline-level gap driving the violation, then re-run DiD on the matched
   sample. The matched-sample placebo test came back clean (p = 0.95).
2. **Shortened-window DiD**: a robustness check restricting the pre-period
   to the window where the violation was smallest.
3. **Regression adjustment**: the independence anchor. It doesn't rely on
   parallel trends at all, so it can fail for entirely different reasons
   than the DiD-family estimates. Its agreement with PSM + DiD matters, not the DiD variants agreeing with each
   other (which share the same vulnerability).

![Event study: unmatched vs. PSM-matched sample](images/event_study_matched.png)

Matching flattens the systematic pre-period drift visible in the unmatched
series (blue). A formal joint test on all 11 pre-period coefficients
confirms it's not just visual:

| sample | joint F-test | verdict |
|---|---|---|
| Unmatched | F(11) = 3.23, p = 0.0002 | reject parallel trends |
| PSM-matched | F(11) = 1.27, p = 0.24 | cannot reject parallel trends |

Individual matched-sample coefficients stay noisy (fewer distinct controls
→ wider error bars per period) — the joint test, not the chart alone, is
what adjudicates.

Full diagnostics (covariate-balance tables, this event study, and the
placebo tests at multiple cutoffs) are in `causal_analysis.ipynb`, sections
3–9.

### Assumptions and limitations

Parallel trends failed the first test, and that shaped the entire analysis. **What fixed it, and how we know?** Matching on RFM drove covariate imbalance from SMD ≈ 0.34 to ≈ 0.02, and the matched-sample diagnostics cleared: placebo 0.04pp (p=0.95), joint F-test p=0.24, pre-period drift falling from −0.038pp/wk to +0.006pp/wk

**Assumptions the headline still rests on:**
- **Conditional parallel trends.** Tested and passed. 
- **Unconfoundedness** (for the regression-adjustment leg). Untestable in principle. Credible here because targeting is a rule-based CRM process on observable RFM, but any unmeasured input to that rule, email engagement history, tenure, channel preference, would bias it. DiD differences such factors away if they are time-invariant; regression adjustment cannot.
- **No anticipation effects.** Customers did not change behaviour before receiving the email.
- **No spillovers.** Untargeted customers were unaffected by the campaign.

**Known weaknesses:**
- **The preferred estimate is the least precise.** PSM+DiD's CI is [1.21, 3.87], nearly triple regression adjustment's width — the price of matching with replacement, which reuses 11,185 distinct controls to serve 24,516 treated customers. It is preferred for diagnostic strength, not precision.
- **Regression adjustment is systematically lower** (1.98pp vs 2.54/2.59pp). The two DiD variants share an assumption, so their agreement was never independent evidence. Effectively there are two estimates — ~2.5pp from trend-based methods, ~2.0pp from the unconfoundedness-based one — and this analysis cannot fully adjudicate between them.
- **The deep-lapse subgroup is thin.** 7,432 treated matched against only 2,627 distinct controls, so its wide interval reflects limited power as much as a genuine null.

**Not implemented, and why:** formal sensitivity analysis (Rambachan & Roth 2023) requires the R-only `HonestDiD` package; synthetic DiD is built for few-units × many-periods panels, the opposite of this 45,000 × 24 shape. Both are cited as the rigorous treatments rather than approximated badly.

**Simulated data.** The dataset is simulated, not company data. Base rates were chosen as plausible values rather than drawn from published benchmarks. The methodology transfers; the specific magnitudes should not be quoted as industry figures.

**What a randomized holdout would have given us.** All of the above is second-best identification. A randomized holdout — withholding the email from a random slice of the eligible list — would deliver the same estimate with no parallel-trends assumption, no unconfoundedness assumption, and no triangulation required. Lewis & Reiley (2014) and Gordon et al. (2018) both show observational estimators can miss experimental benchmarks even with rich covariates. The recommendation below reflects that gap.

## Marketing Recommendations

*Cost assumption: sends are treated as costless.*

### What the campaign actually delivered

Across 24,516 emails, roughly **620 incremental conversions**, about 710 generated in the moderate-lapse segment, offset by a statistically insignificant negative in deep-lapse. At zero cost, the campaign is unambiguously worth running. **Keep it.**

### 1. Stop treating deep-lapse as a win-back audience

30% of the list (7,432 customers) is deeply lapsed, and that group produced no detectable incremental conversions. The naive comparison looks fine — 6.19% conversion versus 5.79% untargeted — but nearly all of that is customers who were returning regardless.

**At zero monetary cost, the argument to stop is not financial.** It is that email is never actually free:

- **Deliverability.** Sending to chronically unengaged addresses is precisely what inbox providers use to classify a sender as spam. That damage lands on *every* campaign, including the moderate-lapse sends that do work.
- **List attrition.** Every send to someone with no interest risks an unsubscribe, permanently removing a customer who may re-engage later through another channel.
- **Measurement distortion.** As long as deep-lapse stays in the campaign, blended reporting mixes a 4pp-effect segment with a 0pp-effect one and produces a number that describes neither.

**Recommendation:** remove deep-lapse from the standing win-back flow. Retain a small holdout there for ongoing measurement rather than dropping the segment blind.

### 2. Expand into the moderate-lapse customers who were never targeted

This is the largest opportunity in the analysis, and it is invisible in the naive framing.

**16,719 moderately-lapsed customers did not receive the email.** They sit inside the same covariate range as the ones who did — matching found a within-caliper control for 100% of treated customers, so this is interpolation, not extrapolation into unfamiliar territory. At the measured 4.14pp incremental effect, reaching them implies **roughly 690 additional incremental conversions** — approximately doubling what the campaign produced, at zero incremental cost.

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

