# Saved results

This directory contains aggregate results and fitted coefficients needed to reproduce the paper. Participant-level inputs and predictions are excluded from GitHub.

- `constant7_*`: primary full-sample fit, five validation fits and 500 bootstrap fits.
- `saturating8_*`: retest-saturation comparison, matched to the same folds and 500 resamples.
- `drift_*`: longitudinal age-related-change comparison, with the same 500 resamples.
- `slowing_*`: slowing-decay comparison, with the same 500 resamples and quadrature checks.
- `benchmark_*`: full-sample and cross-validation fits for the four simpler benchmarks.
- `tables/`: canonical numerical summaries, including correlations retained as diagnostics rather than a paper table.
- `figure_data/`: aggregate plotting data for Figure 3. Figures 4 and S1 read the primary fits directly; there are no duplicate fit copies here.
- `booster_comparison.json` and `supplementary_schedule_comparison.json`: reference maintenance/schedule summaries.
- Audit, reconciliation and manifest JSON files record verification and provenance. Draw/seed/fold numbers identify resamples, not people.

The output map in `docs/outputs.md` links these results to the current paper numbering. Historical filenames are retained so the calculations remain compatible. The CLI writes regenerated files to an output directory; it never replaces these references or edits manuscript prose.
