# Input data

Participant-level data are not distributed with this repository and must never be committed (`.gitignore` excludes `data/*`, `*.csv` and `*.npy`). Place the two extracts here, or pass their paths with `--data` and `--composite`.

## 1. Grand Index extract: `data/newsubset.csv`

One row per NCPT administration. Participants were restricted upstream to at least two administrations and no more than 25 gameplays before the first administration.

| Column | Use |
|---|---|
| `user_id` | Participant identifier |
| `nth_test` | Administration number (1 = baseline) |
| `test_run_id` | Sitting identifier |
| `battery_id` | Battery identifier, required by the default same-battery policy |
| `normed_score` | Grand Index (census-normed; mean 100, SD 15). The modeled outcome is its change from baseline |
| `num_plays_before` | Cumulative gameplays before the administration; interval gameplays are its differences |
| `days_since_signup` | Integer days from signup to the administration; interval days are its differences |
| `signup_date` | Day-first `DD/MM/YY`; used only to report dates |
| `age`, `gender`, `education_level` | Descriptive statistics only |
| `created_at`, `raw_score` | Not used |

Notes:
- Parse `signup_date` with `format="%d/%m/%y"`. Month-first parsing gives wrong dates.
- The original GI extract includes `battery_id`. The default `--gi-battery-policy same-battery` keeps each participant's initial sequence on one battery, ending at the first change. It raises an error when IDs are missing. Battery IDs 39 and 50 are the older and newer subscriber batteries; three subtests differ in version.
- `--gi-battery-policy retain` explicitly keeps all supplied GI records. This option reproduces the earlier GI cohort after correcting gameplay metadata. The presence or absence of an optional column never silently chooses the cohort. The original `v17-numbers` input was documented without a battery identifier; use that tag to reproduce the uncorrected manuscript numbers.

## 2. Short-interval composite extract: `data/short_intervals.csv`

One row per subtest result. Column names are matched case-insensitively.

| Column | Use |
|---|---|
| `USER_ID` | Participant identifier |
| `TEST_RUN_ID` | Sitting identifier |
| `BRAINPOWER_TEST_ID` | Battery; chains are restricted to one battery |
| `NTH_RUN` | Sitting number across all of a participant's sittings |
| `TEST_SECTION_ID` | Subtest |
| `INDEX_SCORE` | Census-referenced subtest index; 0 marks a subtest without norms |
| `TRESULT_CREATED_AT` | Subtest result time; a sitting's date is its first result |
| `GAMEPLAYS_BETWEEN_TEST_RUNS` | Gameplays since the previous sitting |
| `DAYS_BETWEEN_TEST_RUNS` | Not used for intervals (based on sitting creation times) |
| `AGE_AT_SIGNUP`, `GENDER`, `EDUCATION_LEVEL`, `SIGNUP_DATE` | Descriptive statistics only |

The file contains other columns, including `DATE_OF_BIRTH`. The analysis does not use them.

### How composite records are built (`composite_extract.py`, `paper_pipeline.build_merged`)

1. Each sitting's date and gameplay count are recorded from the untouched subtest rows, before any rows are dropped. The date is the first subtest result and the gameplay count is the sitting maximum.
2. Index scores of 0 are dropped. Where a subtest appears twice in a sitting, the first result is kept.
3. The composite is the mean of the remaining subtest index scores; at least three are required.
4. The raw sitting gameplay maximum is aligned with the retained composite sittings. A gameplay count carried by an excluded subtest remains available.
5. For each participant, the analysis keeps the leading run of consecutive sittings (by `NTH_RUN`) on the same battery. The run must start at `NTH_RUN` 1, so that the baseline is the participant's first NCPT administration.
6. Participants who also appear in the Grand Index extract are dropped from the composite records; their Grand Index records are kept.
7. Records are recast to the Grand Index schema (days from the first sitting, cumulative gameplays), with participant IDs prefixed `NIC_`.

## 3. Derived files (not committed)

- `out/v17/_data_cache/`: merged and Grand Index-only datasets plus a manifest of input checksums, policy, builder-code hashes and output checksums. A changed input, policy, builder or cached output triggers a rebuild. `--out` relocates both outputs and cache.
- `out/v17/`: analysis outputs (see the main README).
