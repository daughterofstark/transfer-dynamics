# Canonical numbers

Every number in the manuscript, with the command that produces it. If a value is
not here, it has not been verified — regenerate it before use.

Source of record: `paper_pipeline.py` (main fit) and `verify_numbers.py`
(distributions, sensitivities). Last regenerated 2026-07-28.

---

## Sample

| Quantity | Value | Source |
|---|---|---|
| Participants | 81,939 | pipeline |
| Administrations | 197,843 | pipeline (`N_rows`) |
| Gameplays in window | 49,401,429 | verify, exposure |
| Administrations per participant, mean | 2.41 | derived |
| Exactly two administrations | 58,126 (70.94%) | derived |
| Three or more | 23,813 (29.06%) | pipeline, 9-panel |
| Excluded by any screen | 0 | pipeline |

All three screens (≥2 administrations, ≤25 gameplays before first, interval limits)
are non-binding on this sample.

## First-interval distributions

| | Days | Gameplays |
|---|---|---|
| Mode | 70 (n = 22,306; 27.22%) | — |
| p25 | 70 | 115 |
| Median | 73 | 223 |
| p75 | 93 | 373 |
| p90 | 174 | 680 |
| p95 | 304 | 1,008 |
| p99 | 617 | — |
| Max | 2,222 | 6,479 |

Same-day first interval: 3,171 participants (3.87%).
Longest interval at any position: 2,222 days.
Next most common intervals after 70 d: 71 d (10.16%), 72 d (5.01%), 90 d (4.18%).

## Gameplay strata (first interval)

| Stratum | n | % | Mean change at second administration |
|---|---|---|---|
| ≤50 | 9,721 | 11.86% | +2.101 |
| 51–200 | 27,232 | 33.23% | — |
| 201–500 | 31,872 | 38.90% | — |
| ≥501 | 13,114 | 16.00% | +4.921 |

One-retest non-gameplay share: 42.7% (lower bound on the non-gameplay component;
distinct from the asymptotic share).

## Parameters — main fit

| Parameter | Estimate | 95% CI | Half-life (days) |
|---|---|---|---|
| A_t | 3.1939 | 3.02 – 3.57 | — |
| k_Lt | 4.1567 × 10⁻³ | 3.32 – 5.39 × 10⁻³ | — |
| k_Ft | 1.9811 × 10⁻³ | 6.13 × 10⁻⁴ – 8.13 × 10⁻³ | 350 (85 – 1130) |
| A_d | 5.5453 | 4.20 – 7.40 | — |
| k_Ld | 0.39994 | 0.277 – 0.541 | — |
| k_Fd | 1.3245 × 10⁻³ | 7.47 × 10⁻⁴ – 1.86 × 10⁻³ | 523 (372 – 927) |

CIs from 200 participant-level bootstrap resamples (`figures._bootstrap`, single
start from the point estimate). Half-lives are the CI endpoints transformed by
`log(0.5)/log(1−k)`.

WMSE 53.6413. Static baseline 53.9231. ΔAIC 667.7 (descriptive — computed from
unweighted SSE treating within-participant administrations as independent, and it
scales with sample size).

Asymptotic direct share A_d/(A_t+A_d) = 63.5%.
Observable direct share at T5 = 56.4% (practice effect 3.632, transfer 2.807).
**These are different quantities. Never conflate them.**

## Derived

| Quantity | Value |
|---|---|
| Dose-response intercept at 108 d (mean interval) | 1.923 |
| One-dose practice effect k_Ld·A_d | 2.218 |
| Asymptote (intercept + A_t) | 5.12 |
| 80% of transfer ceiling, 90-day window | ~457 gameplays |
| 80% of transfer ceiling, 108-day mean interval | ~472 gameplays |
| Fixed-dose anchor for the time-window figure | 442 gameplays |

Maintenance steady state, `f(d) = g/(g+k_Ft)` with `g = 1−(1−k_Lt)^d`:

| Gameplays/day | % of transfer ceiling |
|---|---|
| 0.5 | 51 |
| 1.0 | 68 |
| 1.3 | 73 |
| 2.0 | 81 |
| 2.74 | 85 |
| 5.0 | 91 |

Schedules, 1,094 gameplays over 547 days:

| Schedule | End | Mean |
|---|---|---|
| Even, 2.00/day | 80% | 66% |
| Load 60 d @ 7/day, then 1.38/day | 74% | 73% |
| Load, then two ~48 d blocks 6 months apart | 75% | 71% |

Ordering by mean (load > boost > even) holds at every k_Ft in the CI. Even
distribution ends highest at every k_Ft. Only the boost/even ordering flips, at the
fast end.

## Fit quality

Residuals at second administration: mean 0.074, SD 7.018, MAE 5.48,
R²(T2) 0.017, R²(all) 0.026.
Five-fold out-of-sample: R² 0.017, MAE 5.48.
Regression to the mean: r(baseline, change) = −0.157.

## Model-free intercept check

| Sample | n | Mean change | 95% CI | Median interval |
|---|---|---|---|---|
| Merged | 6,102 | 1.997 | 1.805 – 2.188 | 0 d |
| Primary only | 2,841 | 1.873 | 1.595 – 2.150 | 127 d |

Modelled intercept 1.923 falls inside both.

## Robustness — exclusion regimes

| Regime | N | A_t | A_d | k_Ft | Half-life | ΔAIC |
|---|---|---|---|---|---|---|
| Drop extreme intervals | 71,027 | 3.015 | 4.343 | 3.21 × 10⁻⁴ | 2,156 d | 304 |
| Winsorize | 81,939 | 3.331 | 5.584 | 2.52 × 10⁻³ | 275 d | 632 |
| Raised plays limit (3000) | 81,939 | 3.211 | 5.693 | 2.13 × 10⁻³ | 326 d | 635 |
| No exclusion (main) | 81,939 | 3.194 | 5.545 | 1.98 × 10⁻³ | 350 d | 668 |

A_t range 3.02 – 3.33. Dynamic model preferred in 4/4.

## Robustness — analytic sensitivities

| Refit | A_t | k_Ft | Half-life | Note |
|---|---|---|---|---|
| Main | 3.194 | 1.98 × 10⁻³ | 350 d | — |
| Composite rescaled 15/12.2 | 3.047 (−4.6%) | 7.65 × 10⁻⁴ (−61%) | 906 d | inside CI |
| Unweighted | 3.435 (+7.5%) | 7.38 × 10⁻³ (+272%) | 94 d | inside CI |

Both sensitivities fall within the Table 1 resampling interval, so the uncertainty
these analytic choices introduce is already represented there. The drop-extreme
regime (3.21 × 10⁻⁴) falls outside, but removes 13.3% of participants and is
therefore a different sample rather than a different estimator.

## Second optimum

A restart at a fast forgetting rate converges to WMSE 53.659333 with k_Ft ≈ 0.371.
At that solution k_Lt ≈ 0.23, implying 80% of the transfer ceiling after ~6
gameplays. Rejected as inconsistent with the observed dose-response, which
saturates over several hundred. This appears in the Phase 3 probe output of every
run; it is reported in Methods rather than treated as a competing estimate.

A two-start bootstrap lands in that basin in 19/200 resamples (9.5%), which is why
the reported CI comes from the single-start bootstrap. The two bootstraps agree to
three decimals on the k_Ft lower bound (6.13 × 10⁻⁴) and on the whole A_t interval.

## Robustness fit — primary records, first three administrations

N 23,291. A_t 3.3378, A_d 7.1164, k_Lt 3.4958 × 10⁻³, k_Ft 8.1533 × 10⁻⁴,
k_Ld 0.28648, k_Fd 1.7185 × 10⁻³. WMSE 52.6445, ΔAIC 279.6.
One-retest non-gameplay share 36.7%.

WMSE is not comparable across fits — different data.

## Composite construction

134,295 subtest rows → 111,929 with non-zero index → 20,370 runs →
19,542 with ≥3 valid subtests. Composite mean 109.3, SD 12.2.
5,539 participants with ≥2 runs; 64.1% same battery across the first two;
3,480 retained with a same-battery chain ≥2, contributing 8,186 administrations;
522 with a chain ≥3.

**Open:** 7 subtest ids ({37,38,39,40,43,44,45}) are always zero beyond the
expected 12. Confirm they are genuinely un-normed rather than normed subtests
scoring zero — a normed subtest dropped as zero would inflate that run's mean
composite.
