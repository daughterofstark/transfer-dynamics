# Input data

Participant-level data are not distributed with this repository and must never be committed (`.gitignore` excludes `data/*`, `*.csv` and `*.npy`). Place the two extracts here, or pass their paths with `--data` and `--nicole`.

## 1. Grand Index extract: `data/newsubset.csv`

One row per NCPT administration. Participants were restricted upstream to at least two administrations and no more than 25 gameplays before the first administration.

| Column | Use |
|---|---|
| `user_id` | Participant identifier |
| `nth_test` | Administration number (1 = baseline) |
| `test_run_id` | Sitting identifier |
| `normed_score` | Grand Index (census-normed; mean 100, SD 15). The modeled outcome is its change from baseline |
| `num_plays_before` | Cumulative gameplays before the administration; interval gameplays are its differences |
| `days_since_signup` | Integer days from signup to the administration; interval days are its differences |
| `signup_date` | Day-first `DD/MM/YY`; used only to report dates |
| `age`, `gender`, `education_level` | Descriptive statistics only |
| `created_at`, `raw_score` | Not used |

Notes:
- Parse `signup_date` with `format="%d/%m/%y"`. Month-first parsing gives wrong dates.
- The extract has no battery identifier; battery constancy is assumed to have been applied upstream.

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

### How composite records are built (`merge_nicole_refit.py`, `paper_pipeline.build_merged`)

1. Each sitting's date is the date of its first subtest result, recorded before any rows are dropped.
2. Index scores of 0 are dropped. Where a subtest appears twice in a sitting, the first result is kept.
3. The composite is the mean of the remaining subtest index scores; at least three are required.
4. Gameplays between sittings are recorded on only one row per sitting (other rows hold 0), so the per-sitting maximum is used.
5. For each participant, the analysis keeps the leading run of consecutive sittings (by `NTH_RUN`) on the same battery. The run must start at `NTH_RUN` 1, so that the baseline is the participant's first NCPT administration.
6. Participants who also appear in the Grand Index extract are dropped from the composite records; their Grand Index records are kept.
7. Records are recast to the Grand Index schema (days from the first sitting, cumulative gameplays), with participant IDs prefixed `NIC_`.

## 3. Derived files (not committed)

- `_verify_scratch/merged_cache.csv`, `_verify_scratch/orig_cache.csv`: the merged and Grand Index-only datasets, rebuilt with `--rebuild`.
- `out/v17/`: analysis outputs (see the main README).
