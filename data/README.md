# Data dictionary and minimization

The archive begins after private extraction, eligibility checks and scoring. No account/user/test IDs, DOBs, names, contact details, absolute calendar dates, geography, individual education or individual gender are distributed. The model input still contains detailed real participant trajectories and is not a guarantee of anonymity.

## `timing_input.npz`

Load with `numpy.load(path, allow_pickle=False)`. All fields are numeric. `n=172731`; up to four follow-ups correspond to T2–T5. Input age is **whole-year attained age at T1**, stored as float64, ranging from 18 to 89; it is not fractional age.

| Field | Shape | Meaning and reason retained |
| --- | --- | --- |
| `age` | n | Whole-year age at T1; retest input, baseline-age reference, within-person and aging comparisons |
| `GI0` | n | Baseline Grand Index; baseline correction, GI reconstruction and descriptive summaries |
| `Y` | n × 4 | GI at each follow-up minus GI at T1; modeled outcome |
| `P` | n × 4 | Gameplays in each consecutive interval; dose benchmarks, interval checks and plots |
| `D` | n × 4 | Calendar-date difference between consecutive tests; forgetting, time comparisons and gameplay eligibility |
| `ptr` | n × 4 × 2, int64 | Start-inclusive/end-exclusive offsets into `dt` and `plays`; indexes array segments, not people in an external system |
| `dt` | 12,268,394 | Integer calendar-day difference from the event containing the associated games to the next training or testing event; may be zero |
| `plays` | 12,268,394 | Observed game count before advancing the corresponding number of calendar days |

All fields except the int64 pointer array are float64. P, D and gameplay counts have integer values. Missing follow-ups are NaN in Y/P/D; their pointers are ignored. Every row has T2. Valid follow-ups are consecutive; no interval bridges an excluded visit. Segments are contiguous and ordered by row, interval and time. Their duration/count sums reconcile to D/P. These interval totals are retained as explicit analysis and reconciliation fields even though they can also be summed from segments.

Elapsed days are relative integer differences between calendar dates. The model input contains no timestamps, absolute dates or intraday time values. Games were assigned to the appropriate side of tests before these arrays were prepared.

Row order is fixed because seeds generate folds/bootstrap draws by row position. Do not reorder it without remapping those assignments. There is no exported lookup from row positions to accounts; row position is nevertheless a consistent index within this archive.

## `supplement_aggregates.json`

This 5.8 KiB file summarizes the 391,238 baseline-eligible users for Tables S1/S3. It has no participant rows or cross-file person key.

`schema_version` is 1. `groups` contains three explicitly overlapping/complementary populations: T1-only (183,320), any repeat test (207,918), and model participants (172,731, a subset of repeat testers).

For each group:

- `n`: number of participants.
- `mean_sd`: count, mean and sample SD (ddof=1) for age at T1 and baseline GI.
- `quantiles`: nonmissing count and 25th/50th/75th percentiles for pre-T1 gameplays and signup-to-T1 elapsed days. Percentiles use pandas' linear interpolation. No minima, maxima or participant-level order statistics are exported.
- `category_counts`: marginal gender and education counts for the manuscript categories; denominators are group n. These are not person-level demographics or cross-tabulated cells.
- `baseline_age_moments`: n, three means, and a 3 × 3 sample covariance matrix for `[GI, t, t²]`, with `t=(whole-year age at T1−50)/20`. For coefficients c0/c1/c2, the corrected mean is `w @ means − c0` and its sample variance is `w @ covariance @ w`, where `w=[1,−c1,−c2]`. This supports updated quadratic reference coefficients without individual baseline records.

`selection_counts` contains baseline-eligible, returned and included totals; mutually exclusive `first_failure` counts; and `later_failure` participant/omitted-visit totals. Failure codes are battery_change, subtest_composition, invalid_GI, gameplay_rate and four_SD. These counts reconstruct the flow tables but cannot independently reapply exclusions to the source population. Upstream eligibility/scoring definitions are in `docs/data_preparation.md`.

## Battery summary

`paper/specification/battery_summary.json` contains five aggregate rows for Table S2: battery code, named subtests, norming-reference count, model participant count and model test-completion count. Participant-level battery identity is not distributed and is not used in model fitting. Counts are fixed for this cohort and reconcile to the model totals; source eligibility and same-battery checks occurred before this archive was assembled.

## Reference results

`paper/reference` contains fitted coefficients, aggregate check targets and optimizer diagnostics. `draw` and `seed` identify bootstrap replicates; `fold` identifies a fitting fold. None is a participant identifier. No participant predictions, residuals or fitted-row extracts are included. Running the analysis generates predictions locally under the requested output directory.
