# Private analysis inputs

Do not commit participant-level files. Only this README is tracked here. Obtain the two NPZ files from Bob's v23 private data handoff; verify with `python reproduce.py validate`. NumPy loads use `allow_pickle=False`.

## timing_input.npz

One row per participant, in a fixed order. No user ID, DOB or absolute calendar timestamp is present. These remain private participant trajectories, not automatically cleared public data.

| Field | Shape / definition |
| --- | --- |
| `age` | `(n,)`, exact age in years at T1; eligibility is attained age 18–89 |
| `GI0` | `(n,)`, baseline Grand Index |
| `battery` | `(n,)`, same battery throughout retained T1–T5; 17, 32, 39, 50 or 60 |
| `Y` | `(n,4)`, cumulative GI change from T1 at T2–T5; NaN after follow-up ends |
| `P` | `(n,4)`, gameplays in consecutive intervals, not cumulative since T1 |
| `D` | `(n,4)`, difference between calendar dates; rate filter uses `P/(D+1)` |
| `D_exact` | `(n,4)`, exact elapsed days from test timestamps |
| `ptr` | `(n,4,2)`, int64 start/inclusive and end/exclusive offsets into segment arrays |
| `dt` | `(segments,)`, duration in days; exact partial days, full active days, compressed inactive spans |
| `plays` | `(segments,)`, observed gameplay count in each segment |

The valid-mask of P/D/D_exact equals Y's. Every participant has at least T2. Valid follow-ups form a prefix; there is no bridging across an excluded visit. Segments are ordered by participant, interval and time, contiguous in the global arrays. `sum(dt)` and `sum(plays)` within each pointer slice equal D_exact and P. `subset()` deliberately retains global segment arrays and their pointers.

## selection_input.npz

391,238 baseline-eligible participants, including T1-only testers. Row order is independent of the model array; there is **no cross-file identifier**. Fields are age_t1, grand_index, plays_before, days_signup_to_t1, education_level, battery_id, gender (f/m/empty), returned, in_analysis, first_failure, later_failure, omitted_visits.

`returned` includes any subsequent recorded test, even one later excluded. `in_analysis` identifies the final repeated-test cohort. Failure labels are sequential, mutually exclusive first failures: battery_change, subtest_composition, invalid_GI, gameplay_rate, four_SD, or empty. Later failures truncate an otherwise retained trajectory. These labels are inputs from the upstream extract/score/eligibility pipeline, not reclassified by the reporting code.

The data handoff begins **after** warehouse extraction, score normalization and eligibility decisions. It reproduces the model, validation, numerical paper outputs and descriptive table counts. It does not independently re-extract Snowflake or reconstruct original trial logs. See `docs/data_preparation.md` for those upstream definitions and release limitations.
