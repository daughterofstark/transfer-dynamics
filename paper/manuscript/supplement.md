# Supplementary information

**Modeling the durability and maintenance of cognitive training gains in 172,731 adults**

Medha Sharma and Robert John Schafer

NCPT denotes the NeuroCognitive Performance Test, a battery of cognitive tests. The Grand Index (GI) is its overall composite score. T1–T5 denote successive NCPT testing timepoints; each battery completion contributes one GI. A gameplay is one recorded play of a cognitive training game.

## Supplementary Table 1

Participant characteristics among baseline-eligible users who completed only T1, those who returned for testing, and the final model cohort.

| Characteristic | T1 only | Returned for testing | Model cohort |
| --- | --- | --- | --- |
| Participants, n | 183,320 | 207,918 | 172,731 |
| Age at T1, mean (SD), years | 45.98 (17.05) | 53.04 (15.82) | 52.85 (15.73) |
| GI at T1, mean (SD) | 101.71 (14.46) | 99.56 (14.25) | 100.08 (14.07) |
| Age-referenced baseline GI, mean (SD) | -1.71 (11.79) | -0.40 (11.40) | 0.00 (11.28) |
| Gameplays before T1, median [IQR] | 14.0 [9.0, 18.0] | 15.0 [11.0, 18.0] | 15.0 [11.0, 18.0] |
| Days from signup to T1, median [IQR] | 7.7 [2.8, 127.1] | 7.2 [3.1, 91.1] | 7.1 [3.0, 82.5] |
| Female, n (%) | 89,216 (48.7%) | 114,566 (55.1%) | 94,641 (54.8%) |
| Male, n (%) | 75,078 (41.0%) | 74,494 (35.8%) | 62,343 (36.1%) |
| Gender not reported, n (%) | 19,026 (10.4%) | 18,858 (9.1%) | 15,747 (9.1%) |
| High school or less, n (%) | 21,414 (11.7%) | 20,906 (10.1%) | 17,123 (9.9%) |
| Some college or undergraduate degree, n (%) | 98,451 (53.7%) | 110,027 (52.9%) | 91,340 (52.9%) |
| Professional or graduate education, n (%) | 40,261 (22.0%) | 53,891 (25.9%) | 45,043 (26.1%) |
| Other education, n (%) | 3,245 (1.8%) | 3,545 (1.7%) | 2,847 (1.6%) |
| Education not reported, n (%) | 19,949 (10.9%) | 19,549 (9.4%) | 16,378 (9.5%) |

The comparison population contains 391,238 users with a valid, baseline-eligible first test (T1). Returned for testing includes users with any subsequent recorded NCPT test, including tests later excluded from the model. The final model cohort is a subset of those who returned. The age-reference curve is estimated in the model cohort and applied to each comparison group. Historical subscription continuity and individual invitation receipt were unavailable. Values are counts (%), means (SD), or medians [interquartile range], as labeled.

## Supplementary Table 2

Battery composition and sample sizes. Reference participants supplied the distributions used to construct GI scores; model participants completed an eligible NCPT battery at least twice.

| Battery ID | Subtests | Reference participants, n | Model participants, n | NCPT battery completions |
| --- | --- | ---: | ---: | ---: |
| 17 | Divided visual attention; Forward memory span (v1); Arithmetic reasoning; Grammatical reasoning; Progressive matrices; Go/no-go (v2) | 37,394 | 19,544 | 45,933 |
| 32 | Divided visual attention; Forward memory span (v1); Arithmetic reasoning; Grammatical reasoning; Progressive matrices; Reverse memory span (v1); Digit symbol coding (v1); Trail making part A; Trail making part B | 51,992 | 27,461 | 62,285 |
| 39 | Forward memory span (v1); Arithmetic reasoning; Grammatical reasoning; Progressive matrices; Reverse memory span (v1); Digit symbol coding (v1); Trail making part A; Trail making part B | 103,610 | 59,304 | 136,202 |
| 50 | Arithmetic reasoning; Grammatical reasoning; Progressive matrices; Trail making part A; Trail making part B; Forward memory span (v2); Reverse memory span (v2); Digit symbol coding (v2) | 148,583 | 65,245 | 161,870 |
| 60 | Scale balance; Posner cueing; Complex memory span; Object recognition; Dual search | 3,390 | 1,177 | 3,196 |
| Total | | 344,969 | 172,731 | 409,486 |

Subtest names and version labels follow Jaffe et al. [reference 21 in the main text]. Versions distinguish the earlier and later forward memory span, reverse memory span, and digit symbol coding tasks; the Go/no-go task in battery 17 is version 2. Complex memory span is referred to as Complex Span in Supplementary Note 1. Each modeled participant completed the same battery and subtest versions throughout follow-up.

## Supplementary Table 3

Participant selection from the baseline-eligible comparison population. Exclusions are applied sequentially and are mutually exclusive at the second test.

| Stage | Excluded n | Remaining n |
| --- | --- | --- |
| Baseline-eligible users in the comparison table | 0 | 391,238 |
| No subsequent recorded NCPT test | 183,320 | 207,918 |
| Different battery at the second test | 4,324 | 203,594 |
| Required subtests missing at the second test | 18,566 | 185,028 |
| No valid second-test GI despite the required subtests being present | 9,244 | 175,784 |
| First interval exceeded 20 gameplays per (calendar-day difference + 1) | 2,835 | 172,949 |
| Second-test GI or first-interval GI change outside the fixed four-SD bounds | 218 | 172,731 |
| Final model cohort | 0 | 172,731 |

Baseline eligibility already incorporates account, population, prior-training, complete-battery, and valid-T1-score requirements. This table therefore starts with users who have an eligible baseline rather than all subscribers. The final cohort contributes 409,486 NCPT battery completions and 236,755 follow-up intervals, with 96,461,780 intervening gameplays (96.5 million when rounded).

### Later follow-up ending before T5

| First reason follow-up ended | Retained participants | Later tests omitted |
| --- | --- | --- |
| Battery change | 4,481 | 6,789 |
| Required subtests missing | 8,168 | 8,274 |
| Invalid GI | 3,024 | 4,594 |
| Training-rate criterion | 631 | 1,098 |
| Four-SD score criterion | 61 | 84 |

These participants remain in the model with their valid earlier tests. Counts of omitted tests cover the remaining recorded tests within T1–T5 after the first failure. No interval bridges an excluded test. Participants contributing at T1–T5 number 172,731; 172,731; 46,868; 12,466; and 4,690, respectively.

## Supplementary Table 4

Prediction of NCPT composite-score improvement in held-out participants. All models use the same five participant folds, equal participant weighting, and an age-referenced baseline correction estimated within training folds. RMSE is root mean squared prediction error, expressed in GI points; lower values indicate more accurate predictions.

| Model | Held-out RMSE (GI points) |
| --- | --- |
| Mean follow-up change | 7.0324 |
| Retest learning only | 6.9727 |
| Learning without forgetting | 6.9196 |
| Cumulative training without elapsed time | 6.9169 |
| Primary learning-and-forgetting model | 6.8909 |

The primary model had lower prediction error than each benchmark in all five folds. The mean model estimates one average follow-up change; the retest-only model includes age-dependent test input and retest decay; the no-forgetting model sets both forgetting rates to zero. The static dose-response model combines a saturating cumulative-gameplay curve with separate age-dependent intercepts at T2–T5 and contains no calendar-time term. Each benchmark estimates its own baseline correction. The cumulative-training benchmark and the primary model are fitted to the same data for the comparison reported in the abstract and Discussion.

## Supplementary Table 5

Selected model comparisons. Each comparison preserves the cohort, observed daily timing, participant weighting, and age-referenced baseline correction. These are focused checks of the retest, longitudinal-change, and forgetting specifications.

| Quantity | Primary | Retest saturation | Age-related change | Slowing decay |
| --- | --- | --- | --- | --- |
| Training half-life or half-retention time, days | 143.4 (119.3–170.1) | 143.4 (119.6–170.1) | 178 (142–218) | 152 |
| Retest half-life, days | 1333.4 (1129.9–1604.2) | 1333.4 (1129.9–1604.2) | At near-zero decay bound | 1,052 |
| Maintenance dose for 80% of maximum gain, gameplays/day | 3.1 (2.7–3.7) | 3.1 (2.7–3.7) | 2.53 (2.10–3.09) | 4.17 |
| Maintenance dose for a 3-point GI gain, gameplays/day | 2.4 (2.0–2.9) | 2.4 (2.0–2.9) | 1.99 (1.63–2.47) | 2.49 |
| Held-out RMSE, GI | 6.89085 | 6.89085 | 6.88830 | 6.89055 |

The retest saturation parameter α was 0 in the full-sample fit and all five held-out-fold fits. Its bootstrap percentile interval was 0.000–0.000; 494 of 500 fits reached zero. The largest bootstrap estimate was 0.0120. The interval collapses at the boundary because almost all estimates are zero. All 500 fits passed the numerical audits. The primary and retest comparison use the same 500 participant resamples. The age-related-change comparison uses 200 paired resamples; the slowing-decay comparison reports point estimates without a parameter bootstrap.

For the slowing-decay comparison, the initial course was 400 gameplays over 90 days, distributed as four or five gameplays per day using the same schedule as Figure 4, followed by cessation. The reported training half-retention time depends on this history. Under this shared schedule, the primary model gives 143 days and the slowing-decay model gives 152 days. After one year without training, the remaining fractions are 17.1% for exponential decay and 29.4% for slowing decay. Percentage maintenance targets refer to each model’s own estimated maximum. Sustaining the primary model’s 80% target of 3.17 GI points requires 3.23 games/day under the slowing-decay model. The fixed 3-GI row compares an identical absolute target.

The age-related-change model estimates a linear age-dependent drift over follow-up. It moves retest forgetting to the near-zero bound, so the corresponding numerical half-life is not reported as a finite biological estimate. Its maintenance-dose rows describe the training contribution separately from the modeled age-related change.

## Supplementary Table 6

Correlations among the seven model coefficient estimates across 500 participant bootstrap fits. Symbols match main-text Table 1: kL is the learning rate per gameplay, kG is the training-related forgetting rate, A is the maximum training-related gain, q50 is retest learning input at age 50, β is its age coefficient, kR is the retest-related forgetting rate, and γ is the baseline correction.

|  | kL | kG | A | q50 | β | kR | γ |
| --- | --- | --- | --- | --- | --- | --- | --- |
| kL | 1.00 | 0.45 | -0.48 | -0.22 | -0.03 | -0.43 | -0.04 |
| kG | 0.45 | 1.00 | -0.03 | 0.35 | 0.30 | -0.36 | 0.03 |
| A | -0.48 | -0.03 | 1.00 | -0.40 | -0.38 | -0.18 | 0.04 |
| q50 | -0.22 | 0.35 | -0.40 | 1.00 | 0.68 | 0.54 | 0.06 |
| β | -0.03 | 0.30 | -0.38 | 0.68 | 1.00 | 0.24 | 0.02 |
| kR | -0.43 | -0.36 | -0.18 | 0.54 | 0.24 | 1.00 | 0.11 |
| γ | -0.04 | 0.03 | 0.04 | 0.06 | 0.02 | 0.11 | 1.00 |

The correlation between log-transformed training and retest half-lives was −0.356. Each resample also refitted the age-reference curve μ(a) = c0 + c1t + c2t², t = (a − 50)/20. The full-sample coefficients were c0 = 103.127 (95% CI 103.049–103.204), c1 = −10.617 (−10.682 to −10.547), and c2 = −2.401 (−2.485 to −2.315).

## Supplementary Methods

### Supplementary Note 1. Score construction and quality criteria

The reference distribution for each battery included first-ever NCPT tests from eligible adults with known education and no more than 25 prior gameplays. Participants with missing or other education could receive a GI from the fixed maps but did not contribute to map estimation. Each battery represented all 18 age-by-education groups; the smallest reference cell contained 31 participants. The oldest reference group was restricted to 70–89 years, matching analysis eligibility.

Weighted empirical percentiles used the cumulative mass below each unique score plus half the mass at that score. Intermediate scores were interpolated linearly in percentile space; scores beyond the reference range used endpoint midrank percentiles. Percentiles were converted to normal scores with mean 100 and SD 15. The arithmetic mean across subtests was transformed again to obtain the GI. Follow-up outcomes did not alter the reference maps. These census-weighted maps are not within-age norms.

Complex Span used the greatest mixed letter–digit sequence length with correct recall and arithmetic on the same trial. A valid record with no successful trial received a floor score of zero. Incomplete or malformed logs and inconsistent sequence progression were excluded.

The older Digit Symbol task (subtest 38) could end when its finite item list was exhausted. Valid elapsed time was greater than zero and at most 90 seconds, and the correct count was finite and nonnegative. Completion required at least 89 seconds, or 66–69 total responses and at least 20 seconds. Total responses were correct plus errors; error counts in the early-ending branch had to be finite and nonnegative. These analyst-selected operational tolerances retained plausible exhaustion of the finite item list while excluding markedly incomplete or rushed records. The score was 90 × correct responses / elapsed seconds. The newer fixed-duration Digit Symbol task (subtest 45) retained its correct-response count. The same scoring and completion rules were applied to the reference and longitudinal samples.

Timed reaction and trail-making measures were oriented so higher values indicated better performance before transformation. Recorded times had to be positive, and trail-making times could not exceed 900,000 milliseconds. Other count scores had to be nonnegative. Complete batteries required every constituent subtest score and no gap between successive subtest results longer than 24 hours. Interleaved testing sessions were excluded.

GI bounds were 40–160, four normative SDs from 100. Consecutive-change bounds were −26.5938809649 to 32.3692174806, calculated as 2.8876682578 ± 4 × 7.3703873057. The reference for these change bounds was the pool of eligible T1–T2 and T2–T3 intervals before completion and score exclusions. The thresholds were fixed once, then applied to every retained interval through T5; they were not recalculated after exclusions. This screening SD differs from the final cohort’s T1–T2 SD used for effect-size standardization.

### Daily cognitive training and partial calendar days

Observed gameplay counts were reconciled with the cumulative counts at every NCPT boundary: 96,461,780 gameplays across 236,755 intervals. The daily training records covered every participant and interval in the final analysis cohort. The earliest recorded subtest-result timestamp defined each testing boundary. Gameplays were assigned to the intervening interval using their recorded timestamps, then aggregated by calendar date. Retest learning from a test affected subsequent scores, not that test's own score.

Within a segment of duration δ days containing p gameplays, we used a constant rate p/δ. The learning fraction ℓ and segment update were:

$$
\ell  = 1 - {(1 - {k}_{L})}^{\frac{p}{\delta }},   r = 1 - \ell  - {k}_{G} \tag{S1}
$$

$$
{G}_{out} = {G}_{in}{r}^{\delta } + \ell A \frac{1 - {r}^{\delta }}{1 - r} \tag{S2}
$$

With no training, the gain is multiplied by (1 − kG) raised to δ. Whole calendar days use δ = 1; first and last partial days use exact elapsed duration. The daily record does not resolve the distribution of gameplays within each partial or full day. Retest forgetting uses the exact elapsed test interval.

The implementation bounds r between 10⁻⁹ and 1 − 10⁻¹² and G between zero and A. Rare partial-day segments can reach this numerical retention bound. At such nonsmooth points, stationarity was checked along the boundary and by perturbations on both sides rather than by an ordinary gradient alone. This did not require a new participant exclusion.

### Fitting and numerical verification

The nonlinear coefficient order is (kL, kG, A, q50, β, kR); the saturating comparison adds α, bounded between zero and 0.99. The baseline coefficient γ is profiled by weighted least squares at each optimizer evaluation. The quadratic baseline-age curve is estimated from T1 scores with one observation per participant and the fitting sample’s participant weights. It is re-estimated in each training fold and bootstrap resample.

Optimization used scaled parameters, analytic derivatives, L-BFGS-B, up to 500 iterations per attempt, ftol = 10⁻¹³, and gtol = 10⁻⁹. Fits failing a projected-gradient audit were continued at tighter tolerance, with additional starting values or a boundary-stationarity check when needed. Full-sample and fold fits used multiple starts. Bootstrap fits used the full-sample estimate and a second start, with additional starts after failed convergence checks. The lowest converged objective was retained; no bootstrap draw was discarded. Exact starts, bounds, seeds, and audit records are stored in the analysis package.

Independent Python recurrences agreed with compiled predictions, and finite differences checked analytic derivatives. The consolidated implementation reproduced the adopted full-sample fit, all held-out predictions, and the objectives and stationarity checks of all 500 primary bootstrap fits. Prediction was also checked after perturbing held-out outcomes to verify that those outcomes did not determine predictions. Primary bootstrap fits were reused after independent re-evaluation; the retest-saturation comparison was freshly fitted to the same 500 participant resamples.

Five participant folds were generated with seed 291029. Participant weighting averages squared follow-up errors within each person before averaging across people. It gives a person with five tests the same total weight as a person with two. Bootstrap multiplicities replace the participant weights during resampling. Eligibility, score maps, and the participant ordering are held fixed.

### Within-person regression

The within-person check used 110,892 consecutive test intervals from 46,868 participants with T3 or later. The outcome was the GI change within an interval. Training intensity was log[1 + gameplays/(calendar-day difference + 1)]. A participant fixed effect removed stable differences in mean interval gain. Covariates included test-occasion indicators, log(1 + exact interval days) and its square, log(1 + prior cumulative gameplays), and age-by-occasion and baseline-GI-by-occasion interactions. Each participant had total weight one, and uncertainty used a participant-clustered sandwich covariance, accounting for the shared test in adjacent changes. The contrast from one to three games per inclusive calendar day is a change of log(4) − log(2) in the exposure variable.

### Selected specification comparisons

The retest comparison uses Rout = [(1 − α)Rin + q(a)] × (1 − kR)^D. Setting α = 0 recovers the primary model exactly. This parameter represents diminishing retest input as retained retest learning accumulates. All other coefficients, including the baseline reference and correction, are refitted. The primary and saturating models use matched participant bootstrap samples and validation folds.

The longitudinal-change comparison adds d50T + dage[(a − 50)T/20 + T²/40], where T is elapsed years since T1. This integrates an annual change rate that varies linearly with attained age. The two coefficients are fitted from longitudinal outcomes rather than inferred from cross-sectional age differences. Their addition produced little improvement in overall prediction and moved retest forgetting to its lower bound. The model has nine outcome coefficients plus three baseline-reference coefficients. Two hundred matched bootstrap samples were fitted for this comparison.

The slowing-decay alternative uses isolated-input retention 1/(1 + λt), with λ = −log(1 − kG) and fixed exponent one. A continuous mixture of exponential traces implements this function, with relative trace rates distributed exponentially. Each trace receives the same learning input toward its maximum; the weighted aggregate preserves the primary full-day learning term. Retest dynamics and the baseline correction are unchanged. Numerical quadrature and adaptive integration were checked for the partial-day boundaries. The alternative has seven outcome coefficients plus three baseline-reference coefficients, the same count as the primary model. Full-sample fits used 48-node quadrature; held-out predictions used 128 nodes with adaptive integration for histories affected by partial-day clamp boundaries. No parameter-bootstrap confidence intervals were calculated for this limited comparison.

### Cognitive-training contrasts and standardization

The primary effect-size example compares 400 versus zero gameplays over 90 days at the same age, baseline GI, and testing history. The modeled GI difference is 3.20 points (95% CI 3.10–3.30). Dividing by the fixed observed T1–T2 change-score SD of 7.219 gives 0.443 change-score SD units (95% CI 0.429–0.457). For comparison with studies using baseline variation, dividing by the cohort's baseline SD of 14.070 gives 0.227 baseline-SD units (95% CI 0.220–0.235). These standardized differences use model-predicted gains and the observed score variability of the cohort. The baseline SD includes variation across a wide age range. Both denominators are fixed across the simulated training schedules.

### Maintenance doses and training-regimen simulations

The maintenance doses in Supplementary Table 5 describe constant daily training that sustains a specified training-related gain when learning balances forgetting (main-text equations 8–9). The 80% target refers to each model's estimated maximum training-related gain; the three-point GI target is the same absolute gain across models.

Figure 4 compares continuous training and periodic boosters after a common initial course of 400 gameplays over 90 days. Both maintenance regimens provide 840 gameplays over the next 270 days. Continuous training distributes these as three or four gameplays per day; boosters provide 20 gameplays per day on days 167–180, 257–270, and 347–360. The plotted training schedule shows phase-average daily rates, while predicted gains use the integer daily counts. Gains are summarized at each day and averaged over end-of-day values for days 91–360, capturing both the sustained average and the fluctuations between booster courses. Retest learning and baseline contributions cancel because the compared schedules share age, baseline GI, and testing history. Each schedule is evaluated with the same 500 participant-bootstrap fits, and their differences are calculated within each fit. Approximate minute equivalents assume three minutes per gameplay and are rounded ballpark translations.
