# Modeling the durability and maintenance of cognitive training gains in 172,731 adults

Reproducible analysis for the current manuscript, prepared for **Communications Psychology**. The current workflow uses 172,731 participants, 409,486 NCPT battery completions and 96,461,780 intervening gameplays. The authoritative Markdown manuscript and supplement are in [`paper/manuscript`](paper/manuscript); their prose is not modified by analysis commands.

The analysis uses observed daily game counts and calendar-day forgetting, separate training and retest decay, age-dependent retest input, an age-referenced baseline correction, and equal participant weighting. There are seven outcome coefficients (six nonlinear coefficients and one profiled baseline coefficient), plus three nuisance coefficients for the quadratic baseline-age reference. See [model specification](docs/model.md) and [data preparation](docs/data_preparation.md).

## Start here

Use Python 3.12 and a C compiler (Clang or GCC). The compiled C objective is built automatically on first import; no Snowflake client, notebooks, R, or private helper repositories are required.

```sh
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
```

Place the model input from the private data archive in `data/`; the aggregate supplement file is included:

- `timing_input.npz`: cleaned/scored longitudinal cohort and observed daily training segments.
- `supplement_aggregates.json`: aggregate statistics for Tables S1/S3; no participant records.

The participant-level model input is not in GitHub; the supplementary aggregate statistics are included. The [input dictionary](data/README.md) defines their fields. `paper/specification/inputs.json` fixes the SHA-256 checksums and participant ordering. The prior private Zenodo draft predates this calendar-day input. Obtain the current file from Bob and validate its checksum; refreshing Zenodo is a separate next step.

```sh
python reproduce.py validate
python reproduce.py all --comparisons
python tests/check_paper_outputs.py --output outputs
```

The `all` command **replays saved coefficients**. It reconstructs held-out predictions and rebuilds numerical tables, effect-size/maintenance summaries, Figures 1–4 and Supplementary Figure 1. The final command checks these outputs against the saved reference results. Generated files stay in `outputs/`; manuscript sources are not modified. Add `--audit-bootstrap` to `all` to independently re-evaluate all 2,000 saved bootstrap objectives and convergence checks; this takes longer.

For a quicker first pass, omit `--comparisons`. The primary/saturation models and four predictive benchmarks still replay. Table S4's unrun comparison RMSE entries are explicitly blank, not copied from prior results.

All commands accept `--input`, `--selection`, and `--output` paths. Nothing depends on Bob's local folder structure. Generated participant predictions stay under the ignored output directory.

## Independent refitting

The [refitting guide](docs/refitting.md) lists full-sample, cross-validation and matched 500-resample fits for each model, plus resumable smoke checks. These commands optimize coefficients from the cleaned input and write to a separate output directory.

## What is here

| Location | Purpose |
| --- | --- |
| `reproduce.py` | Single command-line entry point |
| `paper/analysis/` | Current model, selected comparisons, resampling, reporting |
| `paper/specification/` | Fixed seeds, input hashes, scoring policy, battery definitions |
| `paper/reference/` | Saved fit coefficients and aggregate checks, no participant predictions |
| `paper/manuscript/` | the current manuscript Markdown, references and current figure sources/exports |
| `tests/` | Independent recurrence/gradient, weighting, nesting and leakage checks |
| `legacy/v17/` | Previous tracked workflow, unchanged except location; not used by the current manuscript |

The previous repository entry points belong to v17. They are preserved for provenance, not offered as another route to the current results. Historical local exploratory directories are not part of this PR.

See [handoff and release checks](docs/handoff.md), [output map](docs/outputs.md), and [validation evidence](docs/validation.md).
