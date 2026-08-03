# Inputs

Not committed — participant-level records stay out of version control.

| File | Grain | Key columns |
|---|---|---|
| `newsubset.csv` | one row per NCPT administration | `user_id`, `nth_test`, `normed_score` (Grand Index, 100/15), `num_plays_before` (cumulative gameplays), `days_since_signup` |
| `short_intervals.csv` | one row per subtest per run | `user_id`, `nth_run`, `index_score`, `brainpower_test_id` (battery), days/gameplays between runs |

`newsubset.csv` carries no battery identifier; constancy is enforced upstream by the
standard Grand Index construction. `short_intervals.csv` does, and
`merge_nicole_refit.py` restricts each participant to their leading run of
consecutive same-battery administrations.

Override paths: `DATA=a.csv NICOLE=b.csv ./run_paper.sh`
