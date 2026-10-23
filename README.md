# Acquisition and forgetting dynamics of cognitive training transfer

Analysis code for the manuscript *Modeling the durability and maintenance of cognitive training transfer* (in preparation).

The analysis fits a six-parameter dynamic model to longitudinal records from Lumosity, a digital cognitive training program. Change in the overall composite score of the NeuroCognitive Performance Test (NCPT), a battery of cognitive tests separate from the training tasks, is modeled as the sum of transfer from cognitive training and a retest effect from repeated NCPT testing. The fitted dynamics are used to estimate the daily training that maintains transfer and to compare training schedules with equal total training.

**Current version: v17.** Every reported number comes from `run_v17.py` and `descriptives_v17.py`; `CANONICAL_NUMBERS.md` lists them with their sources.

## Model

Two latent states, both zero at a participant's first NCPT administration:

- **Retest effect** `S_D`. Each administration adds `k_Ld * (A_d - S_D)`. The state decays by a daily proportion `k_Fd`.
- **Transfer** `S_T`. With `g = 1 - (1 - k_Lt)^p` for `p` gameplays per day, each day updates `S_T <- S_T * (1 - g - k_Ft) + g * A_t`. On days without training, `S_T` decays by `k_Ft`.

Predicted change from baseline is `S_D + S_T`. Training within an interval is spread evenly, and intervals are floored at one day. A half-life is `log(0.5) / log(1 - k)`. Under constant daily training, transfer approaches the steady state `S_T* / A_t = g / (g + k_Ft)`, which defines the maintenance dose.

## Data

Participant-level data are not included. The analysis needs two extracts from Lumos Labs, placed in `data/`; `data/README.md` describes the required files and columns. Data access: to be added.

## Setup

```
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

Tested with Python 3.13.5 on macOS.

## Reproduce

```
./run_paper.sh            # full analysis: 200 bootstrap samples and figures (~50 min)
./run_paper.sh --quick    # 20 bootstrap samples, no figures (~6 min)
```

`run_paper.sh` rebuilds the merged dataset from the raw inputs, runs `run_v17.py`, then runs `descriptives_v17.py`. Both modes write to `out/v17/`, so copy that folder first if you want to keep an earlier run. Input paths and the interpreter can be overridden: `DATA=... COMPOSITE=... PYTHON=... ./run_paper.sh`.

Equivalent manual commands:

```
.venv/bin/python run_v17.py --data data/newsubset.csv --composite data/short_intervals.csv --rebuild
.venv/bin/python descriptives_v17.py
```

## Outputs (`out/v17/`)

| File | Contents |
|---|---|
| `report.md` | Main fit, Table 1 intervals, derived quantities and schedule rankings, data checks, cross-validation, Grand Index-only fit |
| `descriptives.md` | Sample, exposure, weighting cells, demographics, dates, Results-text numbers, residuals, bootstrap convergence |
| `draws.npy`, `bootstrap_info.csv` | Bootstrap parameter draws and per-draw convergence |
| `derived_per_draw.csv` | Maintenance and schedule outcomes for each draw |
| `cv_deciles.csv` | Held-out observed and predicted means by decile |
| `supp_table1_weights.csv` | Weighting cells |
| `fig_main/`, `fig_supp/` | Figures |

| Manuscript | File |
|---|---|
| Fig. 1 | `fig_main/fig_exposure.png` |
| Fig. 2 | `fig_main/fig_param_bootstrap.png` |
| Fig. 3 | `fig_main/fig_dose_9panel.png` |
| Fig. 4 | `fig_main/fig_dose_partition.png` |
| Fig. 5 | `fig_main/fig_time_window.png` (440 gameplays) |
| Fig. 6 | `fig_main/fig_maintenance_concept.png` |
| Fig. 7 | `fig_main/fig_maintenance.png` |
| Fig. 8 | `fig_main/fig_schedules.png` |
| Supplementary Figs. 1-8 | `fig_supp/figS_cdf.png`, `fig_supp/viz5_dose_response.png`, `fig_main/fig_dose_time_heatmap.png`, `fig_supp/figS4_uncertainty.png`, `fig_supp/viz7_residuals.png`, `fig_supp/figS_calibration.png`, `fig_supp/viz12_regression_to_mean.png`, `fig_supp/figS_two_channel.png` |

## Analysis specification (v17)

| | |
|---|---|
| Sample | Both extracts merged; at least two NCPT administrations; first five per participant; no exclusions on interval length or gameplays |
| Outcome | Change from the first administration in the NCPT overall composite: the Grand Index, or the mean of valid subtest index scores (see `data/README.md`) |
| Intervals | Calendar days between the dates the tests were taken |
| Weighting | Inverse cell frequency over 3 gameplay bands (<=50, 51-400, >400) x 3 interval bands (0-90 including same-day, 91-150, >=151 days); capped at 5; computed once and reused in the bootstrap and cross-validation |
| Objective | Weighted mean squared error, averaged within participant and then across participants |
| Starting values | Derived from Osman et al. (2023): k_Lt 0.0057832, k_Ft 0.00094907, k_Ld 0.5, k_Fd 0.00094907, A_t 3.11, A_d 2.9988 |
| Bounds | Rates [1e-6, 0.99]; ceilings [0, 30]; the same in every fit |
| Optimizer | L-BFGS-B, maxiter 10,000, ftol 1e-13, gtol 1e-9, single start |
| Uncertainty | 200 participant-level bootstrap samples (seed 7), each refitted from the point estimate with the same settings; failed fits are excluded and reported |
| Cross-validation | Five folds over participants (seed 0) |

## Reproducibility checks

- `descriptives_v17.py` refits the point estimate and warns if it differs from the reported v17 estimate by more than 0.1%.
- The merged dataset is cached in `_verify_scratch/`, and the cache is not keyed to the inputs. Always pass `--rebuild` after changing inputs or data-building code; `run_paper.sh` always rebuilds.

## Repository layout

```
run_paper.sh            one command: rebuild data, fit, bootstrap, figures, descriptives
run_v17.py              analysis entry point
descriptives_v17.py     descriptive numbers; writes Fig. 5 at 440 gameplays
transfer_model.py       model engine, imported unchanged (settings are applied in memory)
composite_extract.py    builds composite records from the short-interval extract
paper_pipeline.py       merges the two extracts and defines the weighting bands
figures.py              figure builders
data_build.py           builds or reuses the cached merged dataset
requirements.txt        pinned dependencies
CANONICAL_NUMBERS.md    every reported number and its source
DECISIONS.md            analysis decisions and their rationale
data/README.md          input data dictionary
archive/                superseded scripts and v17 data diagnostics; not part of the reproduction
```

## Earlier versions

Tag `v16-numbers` marks the code behind the v16 manuscript numbers. v16 read the short-interval extract differently (see `DECISIONS.md`), and its numbers are superseded.

## Citation and license

To be added.
