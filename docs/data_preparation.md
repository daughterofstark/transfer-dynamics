# Frozen cohort and scoring provenance

This repository's runnable reproduction starts with the cleaned, scored input arrays. The upstream warehouse extraction used private Lumos Labs records and is not recreated by the public workflow. Original identifiers, dates of birth, raw test logs and warehouse credentials are intentionally absent. The authors should retain the original extraction/scoring audit alongside the eventual data archive.

## Eligibility and follow-up

- Known DOB; age at first-ever NCPT test from 18 through 89 inclusive (exact age <90).
- Non-staff, non-research, non-deleted accounts, based on the verified user flags.
- English-language users in US, Canada, Australia or New Zealand.
- At most 25 gameplays before T1. No restriction to testing within seven days of signup.
- Batteries 17, 32, 39, 50 and 60. Excludes school-study default_leap, all batteries with verbal list learning, and research battery 25.
- Same battery and exact subtest composition throughout each retained trajectory. T1–T5 only; stop before the first invalid/missing/incompatible visit. Retain a valid earlier prefix if at least T1/T2 remain. Never bridge a failed test.
- Every consecutive interval satisfies `gameplays <= 20*(calendar-day difference + 1)`, including same-day testing. No fixed 2,000-gameplay or calendar-duration cap.
- GI between 40 and 160 inclusive. Consecutive GI change between -26.59388096492413 and 32.36921748058884 inclusive. Thresholds were fixed from the earlier untrimmed reference distribution, not recalculated after exclusions.

## Scores and normalization

Each complete battery has all required subtests, no gap between successive subtest results longer than 24 hours, and no interleaved testing sessions. Timing measures are oriented so higher is better. Times must be positive; trail-making times cannot exceed 900,000 ms. Other count scores must be nonnegative.

Complex Span uses the greatest mixed letter–digit sequence length with correct recall **and arithmetic** on the same trial, with a floor of zero for valid logs without a successful trial. Malformed/incomplete logs and inconsistent sequence progression are excluded.

Older Digit Symbol (38) uses `90*correct/duration`. Valid duration is >0 and <=90 seconds, with nonnegative finite correct count. Completion requires >=89 seconds OR 66–69 total responses and >=20 seconds, with finite nonnegative errors in the early-ending branch. These are operational tolerances, not verified historical code constants. The newer task (45) retains its correct count. The same rules apply to norming and analysis.

Census-weighted Jaffe-style normalization uses first-ever valid tests with <=25 prior gameplays and known education. Each battery covers all 18 age-by-education cells; the minimum observed cell is 31. Weighted midrank percentiles account for ties; percentile interpolation clamps to endpoint midranks; inverse-normal transformation gives mean 100/SD15. Average subtest standardized scores, then transform that composite again to GI. The reference maps are frozen and follow-up scores never update them. These are population-weighted maps, **not within-age norms**. Other/missing education does not enter map fitting but can receive scores from the fixed maps.

`paper/specification/score_policy.json` records the exact cutoffs. Battery definitions and aggregate norming counts are included. Standalone score/norming primitives are in `paper/preprocessing/`; the private extraction and assembly pipeline is outside this package's reproduction boundary.

## Observed daily training

Gameplays are assigned to consecutive intervals using recorded timestamps and the earliest subtest-result timestamp at each test boundary, then aggregated by calendar date. The daily segment counts reconcile to the cumulative gameplay-count differences at every boundary: 96,461,780 gameplays across 236,755 intervals. Exact partial-day lengths are retained; inactive spans can be compressed because zero-training decay composes exactly. The NPZ validator rechecks these totals, segment boundaries, prefix structure, age/battery/rate/score rules and file hashes before replay.

## Descriptive population

The baseline-eligible comparison comprises 391,238 people. Returned-for-testing includes any later recorded NCPT test, even if the battery changes or the later test is not complete/valid. Selection labels in the private handoff preserve the mutually exclusive first-failure ordering; tables recount these labels. The model cohort is a subset of repeat testers, not an independent third group. Battery-level norming-reference counts are frozen aggregate provenance, not refitted from the model cohort.
