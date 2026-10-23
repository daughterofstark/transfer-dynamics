# Canonical numbers (v17)

Sources: `out/v17/report.md` (`run_v17.py`, commit 252d83b, 200 bootstrap samples, seed 7) and `out/v17/descriptives.md` (`descriptives_v17.py`, whose refit matched to 0.0034%). Environment: Python 3.13.5, NumPy 2.5.3, SciPy 1.18.1, pandas 3.0.5, matplotlib 3.11.2.

## Main fit

N 81,736; WMSE 53.303518; converged after 103 iterations; no parameter at a bound. Bootstrap: 198 of 200 samples converged; 2 ended with an abnormal line-search termination and are excluded; no converged draw at a bound.

| Parameter | Estimate | 95% interval | Half-life (days) |
|---|---|---|---|
| A_t, transfer ceiling (points) | 3.0535 | 2.8044-3.435 | |
| k_Lt, transfer learning rate (per gameplay) | 0.0045704 | 0.0035831-0.006945 | |
| k_Ft, transfer forgetting rate (per day) | 0.0021256 | 0.00049942-0.0086249 | 326 (80-1,388) |
| A_d, retest-effect ceiling (points) | 7.2487 | 5.6671-10.666 | |
| k_Ld, retest-effect learning rate (per administration) | 0.3076 | 0.19398-0.42005 | |
| k_Fd, retest-effect forgetting rate (per day) | 0.0014601 | 0.00083619-0.0020234 | 474 (342-829) |

First-retest gain k_Ld * A_d = 2.23 points.

## Derived quantities (point estimate; joint 95% interval across 198 draws)

| Quantity | Value |
|---|---|
| Steady state at 3 / 4 / 6 / 8 / 15 min per day (% of ceiling) | 68 (43-89) / 74 (50-92) / 81 (60-94) / 85 (67-96) / 91 (79-98) |
| Gameplays (hours) to 50 / 75 / 80% of ceiling over 90 days | 171 (8.5) / 356 (17.8) / 421 (21.0) |
| Predicted change at the mean first interval (110 d): no training / extensive training | 1.90 / 4.95 points |
| 440 gameplays over 1 d: total (retest, transfer) | 4.87 (2.23, 2.65) |
| 440 gameplays over 365 d: total (retest, transfer) | 3.38 (1.31, 2.07) |

## Schedules (1,094 gameplays over 547 days)

| Schedule | Endpoint | Average |
|---|---|---|
| Even training | 81% (60-94) | 68% (53-76) |
| Front-load plus maintenance | 75% (51-92) | 74% (55-85) |
| Front-load plus boosters | 75% (42-92) | 72% (51-83) |

Front-load plus maintenance had the highest average in 97% of draws; even training had the highest endpoint in 100%. Unrounded point values: 80.9/68.0, 74.9/73.9, 74.6/71.7.

## Data checks

- First intervals of 1-69 days: 3,294 (4.03%); same-day: 12.
- Hedges' g, <=50 vs >=501 first-interval gameplays: 0.388 (95% CI 0.360-0.415); difference 2.81 points.
- Participants with <=25 gameplays (n 4,649): observed change 1.86; predicted retest effect 1.91.
- Held-out decile means: within 0.31 points of predictions.
- In-sample residuals at the second administration: mean 0.07, SD 7.02, MAE 5.48.

## Sample

| Source | Participants | Administrations | Within first five |
|---|---|---|---|
| Grand Index extract | 78,459 | 189,657 | 189,657 |
| Composite extract | 3,277 | 7,759 | 7,330 |
| Total | 81,736 | 197,416 | 196,987 |

- Post-baseline administrations in the fit: 115,251.
- Participants with three or more administrations: 23,795.
- Total gameplays between retained administrations: 50,497,410.
- Grand Index administrations: 2013-12-04 to 2020-03-28. Composite sittings: 2013-03-12 to 2020-06-07.

## Grand Index records only (point estimates)

N 78,459; WMSE 52.724809; A_t 3.0885; k_Lt 0.0037062; k_Ft 0.0012173 (569 d); A_d 6.6371; k_Ld 0.3662; k_Fd 0.0016804 (412 d).

## Superseded

The v16 numbers (N 81,939; tag `v16-numbers`) used an incorrect reading of the short-interval extract (see `DECISIONS.md`). They should not be cited.
