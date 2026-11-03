# Modeling the durability and maintenance of cognitive training effects

Reproducible analysis for manuscript **v23**, prepared for **Communications Psychology**. The current workflow uses 172,731 participants, 409,486 NCPT battery completions and 96,461,780 intervening gameplays. The manuscript and supplement are in [`paper/manuscript`](paper/manuscript); their prose is not modified by analysis commands.

The analysis uses observed daily gameplay timing, separate training and retest decay, age-dependent retest input, an age-referenced baseline correction, and equal participant weighting. There are seven outcome coefficients (six nonlinear coefficients and one profiled baseline coefficient), plus three nuisance coefficients for the quadratic baseline-age reference. See [model specification](docs/model.md) and [data preparation](docs/data_preparation.md).

## Start here

Use Python 3.12 and a C compiler (Clang or GCC). The compiled C objective is built automatically on first import; no Snowflake client, notebooks, R, or private helper repositories are required.

```sh
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
```

Obtain the two **private** input files from Bob and place them in `data/`:

- `timing_input.npz`: cleaned/scored longitudinal cohort and observed daily training segments.
- `selection_input.npz`: anonymous baseline characteristics and exclusion labels for Tables S1/S3.

They are not in GitHub. The [input dictionary](data/README.md) defines their fields. `paper/specification/inputs.json` fixes the SHA-256 checksums and participant ordering. Public data release/Zenodo is a separate author decision.

```sh
python reproduce.py validate
python reproduce.py all --comparisons --audit-bootstrap
```

The second command **replays saved coefficients**, rather than fitting them again. It reconstructs held-out predictions; audits the objectives and stationarity of all 500 primary and 500 retest-saturation bootstrap fits and 200 aging-comparison fits; rebuilds numerical tables, effect-size/maintenance summaries, and Figures 1–4. It writes only to `outputs/`. The slowing-decay comparison includes the original adaptive integration at rare partial-day boundaries and takes longer than the primary replay.

For a quicker first pass, omit `--comparisons --audit-bootstrap`. The primary/saturation models and four predictive benchmarks still replay. Table S5's unrun comparison RMSE entries are explicitly blank, not copied from prior results.

All commands accept `--input`, `--selection`, and `--output` paths. Nothing depends on Bob's local folder structure. Generated participant predictions stay under the ignored output directory.

## Refit from the cleaned data

Refits do not overwrite the saved reference fits or manuscript. Use a separate output directory:

```sh
python reproduce.py fit --model primary --phase point --output outputs/refit
python reproduce.py fit --model primary --phase cv --workers 4 --output outputs/refit
python reproduce.py fit --model primary --phase bootstrap --workers 4 --output outputs/refit

python reproduce.py fit --model saturating --phase point --output outputs/refit
python reproduce.py fit --model saturating --phase cv --workers 4 --output outputs/refit
python reproduce.py fit --model saturating --phase bootstrap --workers 4 --output outputs/refit

python reproduce.py fit --model benchmarks --phase point --output outputs/refit
python reproduce.py fit --model benchmarks --phase cv --workers 4 --output outputs/refit

python reproduce.py fit --model drift --phase point --output outputs/refit
python reproduce.py fit --model drift --phase cv --workers 4 --output outputs/refit
python reproduce.py fit --model drift --phase bootstrap --workers 4 --output outputs/refit

python reproduce.py fit --model slowing --phase point --output outputs/refit
python reproduce.py fit --model slowing --phase cv --workers 3 --output outputs/refit

python reproduce.py all --results outputs/refit/fits --output outputs/refit/report --comparisons --audit-bootstrap
```

Primary and saturation bootstraps use the same 500 saved participant seeds; drift uses their first 200. Slowing decay and predictive benchmarks have no parameter bootstrap. Folds use seed 291029. Fit files save completed jobs and resume; a source/input/runtime manifest prevents silently mixing different runs. Failed fits are errors, never silently dropped. Independent refits can differ slightly numerically from saved fits; compare objectives and reporting precision, not bitwise parameter equality.

For a smoke run, `--fold 0` fits one CV fold and `--draws 1` fits one bootstrap draw after the point fit. A partial run is deliberately rejected for full paper reporting. Each worker loads the approximately 305 MB model input; choose workers for available memory.

## What is here

| Location | Purpose |
| --- | --- |
| `reproduce.py` | Single command-line entry point |
| `paper/analysis/` | Current model, selected comparisons, resampling, reporting |
| `paper/specification/` | Fixed seeds, input hashes, scoring policy, battery definitions |
| `paper/reference/` | Saved fit coefficients and aggregate checks, no participant predictions |
| `paper/manuscript/` | v23 Markdown, references and current figure sources/exports |
| `tests/` | Independent recurrence/gradient, weighting, nesting and leakage checks |
| `legacy/v17/` | Previous tracked workflow, unchanged except location; not used by v23 |

The previous repository entry points belong to v17. They are preserved for provenance, not offered as another route to the current results. Historical local exploratory directories are not part of this PR.

See [handoff and release checks](docs/handoff.md), [output map](docs/outputs.md), and [validation evidence](docs/validation.md).
