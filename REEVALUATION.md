# Corrected re-evaluation of v17

Completed 24 October 2026 against main commit `a76e92df2bf70910246a961459350deeb7e085be`, with the local fixes on this branch. The original `v17-numbers` snapshot remains available at `252d83b1bbf86554c905da73c15ea0dab4e26e50`. Full-precision numerical outputs and source hashes are recorded in the run manifest and JSON/CSV outputs; participant data remain outside Git.

## Recommendation

Adopt the gameplay metadata fix, enforce an explicit same-battery policy in both extracts, and correct the Figure 3 uncertainty calculation. The six-parameter model, Osman-anchored single start, bounds, optimizer tolerances, weighting scheme, resampling plan and schedules remain the v17 specification.

The supplied GI metadata identify older/newer batteries 39 and 50, with three subtests differing in version. Keeping the initial same-battery sequence holds the battery constant for the retest model. This follows the intended same-battery rule; the previous waiver relied on upstream filtering that the original input does not actually satisfy. The default now requires battery IDs. The explicit `retain` option supports an alternative cohort without letting optional columns silently choose the analysis.

## Changes from the manuscript snapshot

| Quantity | Original v17 | Corrected primary analysis |
|---|---:|---:|
| Participants | 81,736 | 81,717 |
| Retained administrations | 196,987 | 196,794 |
| Post-baseline administrations | 115,251 | 115,077 |
| Participants with three or more administrations | 23,795 | 23,683 |
| Gameplays between retained administrations | 50,497,410 | 50,580,247 |
| Transfer half-life, days (95% interval) | 326 (80–1,388) | 329 (83–1,340) |
| Retest-effect half-life, days (95% interval) | 474 (342–829) | 479 (331–892) |
| Training to 75% of ceiling over 90 days | 17.8 hours | 18.2 hours |
| Maintenance at 3 min/day, % of ceiling (95% interval) | 68 (43–89) | 68 (40–90) |
| Maintenance at 6 min/day, % of ceiling (95% interval) | 81 (60–94) | 81 (57–94) |
| Converged bootstrap fits | 198/200 | 200/200 |
| Maximum held-out decile mean discrepancy | 0.31 points | 0.27 points |

Gameplay metadata are aggregated from untouched subtest rows. In the original cohort, 492 retained follow-up sittings from 450 participants lost 120,387 gameplays after the carrier rows were excluded. Cognitive composite scores and sitting dates are unchanged by that fix.

The GI same-battery rule trims 174 administrations from 133 participants. Nineteen are left with baseline only and fail the existing two-administration requirement. The fitted GI component is therefore 78,440 participants and 189,464 administrations; the composite component remains 3,277 participants and 7,330 retained administrations.

## Main parameter estimates

Weighted mean squared error: 53.239894. Converged after 96 iterations; no parameter at a bound. All 200 successful bootstrap draws are retained in the reported intervals. A numerical outlier remains included; no successful draw is removed on the basis of its forgetting rate.

| Parameter | Estimate | 95% bootstrap interval |
|---|---:|---:|
| `A_t` | 3.048354 | 2.777881–3.447254 |
| `k_Lt` | 0.004455612 | 0.003508044–0.006856444 |
| `k_Ft` | 0.002105575 | 0.0005170684–0.008338996 |
| `A_d` | 6.964524 | 5.53658–11.73129 |
| `k_Ld` | 0.3222593 | 0.1781558–0.4326534 |
| `k_Fd` | 0.001446578 | 0.0007768525–0.002090968 |

## Schedules

Each schedule still totals 1,094 gameplays over 547 days. The daily-grid averaging convention is unchanged from v17 (states at baseline through day 547).

| Schedule | Endpoint, % (95% interval) | Average, % (95% interval) |
|---|---:|---:|
| Even training | 80.7 (57–94) | 67.5 (52–77) |
| Front-load plus maintenance | 74.6 (48–92) | 73.5 (52–85) |
| Front-load plus boosters | 74.4 (40–92) | 71.3 (49–83) |

Front-load plus maintenance has the highest average in 99% of draws; even training has the highest endpoint in 100%. The qualitative ordering is unchanged. The uncertainty intervals remain broad.

## Figure correction

For Figure 3 and the related three-panel plot, each parameter draw is evaluated at each participant’s observed interval inputs and predictions are then averaged within the cell. The central line and bootstrap interval now summarize the same group quantity. In the corrected cohort, the old approach differs by up to 0.20 points in its underlying central quantity and 0.37 points in an interval endpoint. This is a plotting calculation correction; the fitted parameters do not depend on it.

## Validation and reproducibility

- Main and GI-only fits converge; all five validation fits converge. The GI-only WMSE is 52.689696, with transfer/retest half-lives 545/417 days.
- All 200 bootstrap fits converge; none of the accepted estimates is at a parameter bound.
- The corrected input has no duplicate participant/test-number pairs, missing required model values, gaps in retained test numbers, or negative time/gameplay differences.
- Six synthetic regression tests pass: excluded-row gameplay metadata, explicit battery policy, cache invalidation, failed-fit handling, individual-prediction uncertainty, and serial/parallel bootstrap equivalence.
- All figure builders complete; the affected 3x3, maintenance and schedule figures were visually inspected.
- Cache contents are verified against raw inputs, builder code, cohort settings and cached outputs. Figure-only regeneration checks that saved draws match the inputs and model/runner source.
- Python 3.12.14; NumPy 2.5.3, SciPy 1.18.1, pandas 3.0.5, matplotlib 3.11.2, seaborn 0.13.2. No package dependencies were added.

Input SHA-256 checksums:

- GI: `753096e90f533423d2e19b0ca61bffe9cb4c17291b981efd2dcebc25e69dad08`
- Composite: `a5a98e88be56930b9dc4e3aa296a69c41784ea17402daa8648cf106e336d6a5b`

Rerun with the original GI extract containing battery IDs:

```bash
DATA=data/newsubset.csv COMPOSITE=data/short_intervals.csv WORKERS=4 OUTPUT=out/corrected ./run_paper.sh
```

`fits.json`, `run_manifest.json`, `bootstrap_info.csv`, `draws.npy`, `cv_fit_diagnostics.json`, `report.md` and `descriptives.md` provide the numerical audit trail. Original v17 results are preserved separately.

## Manuscript handoff

Update the sample flow, six-parameter table, numerical Results, maintenance/schedule intervals, bootstrap convergence count, supplementary weighting table and affected figure artwork. Describe the same-battery restriction in both extracts and raw-row aggregation of gameplay metadata. Report the 730-day values as chosen numerical starts; the exact values have not been derived quantitatively from Calamia et al. Demographic ages should retain their source definitions: the composite field is `AGE_AT_SIGNUP`; the GI age definition still needs source confirmation.
