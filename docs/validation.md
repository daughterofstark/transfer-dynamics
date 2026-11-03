# Validation of the v23 consolidation

Checked on macOS arm64 with Python 3.12.14, NumPy 2.5.3, SciPy 1.18.1, pandas 3.0.5 and matplotlib 3.11.2. Clang compiled the three C objectives. The local Xcode launcher required its direct compiler path and SDK via CC/CFLAGS; a configured Clang/GCC installation normally needs no override.

The staged source tree was exported into a separate directory with no historical analysis folders or compiled libraries. With only the two external NPZ inputs, it compiled, ran all model/benchmark/comparison replays, regenerated numerical tables and all four figures, and passed `tests/check_paper_outputs.py`. Six synthetic tests also passed in that separate source export. This was a fresh source checkout using the documented installed package versions, not a newly provisioned operating system.

## Numerical checks

- Cohort: 172,731 people; 409,486 test timepoints; 236,755 intervals; 96,461,780 gameplays. Daily segment sums reconcile to every interval.
- Re-evaluated all **500 primary**, **500 retest-saturation** and **200 aging-comparison** saved bootstrap fits. All reproduced their saved objective values (maximum discrepancy 0 in this runtime). Boundary-stationarity checks passed for 64, 60 and 19 fits respectively. No draw was discarded. These are audits of existing fits, **not 1,200 newly optimized fits**.
- Reconstructed all held-out predictions using the saved fitting-sample coefficients. Outcome perturbation checks passed. RMSE: primary 6.890850764; mean change 7.032379591; retest-only 6.972689529; no-forgetting 6.919613595; cumulative-use 6.916924694; aging 6.888298356; slowing decay 6.890548186.
- Fresh primary optimization: full-sample fit, CV fold 0 and bootstrap draw 0. Objective differences from the saved fits were below 6e-13; the largest half-life difference was 0.0044 day. This smoke check exercises independent optimization and resampling; it does not claim all bootstrap fits were freshly optimized during packaging.
- The independent tests check C/Python recurrences, analytic gradients, daily timing, participant weighting, nonzero retest gain at zero gameplay, nested comparators and separation of held-out outcomes from prediction/reference fitting.

## Paper reconciliation

Tables S1/S3 and later follow-up counts match exactly; within-person coefficients and cluster uncertainty agree to 1e-10; all Figure 3 aggregate numbers match exactly; all eight held-out RMSEs agree to 1e-10. The booster summaries match exactly. Rebuilt PNGs for Figures 1–4 are pixel-identical to the current manuscript exports. The 400-game cessation illustration and fixed SD denominators reproduce the paper's rounding.

Machine-readable evidence is in `paper/reference/packaging_validation.json`. To repeat the numerical reconciliation after a full saved-fit replay:

```sh
python tests/check_paper_outputs.py --output outputs
```

The original warehouse extraction, raw-log scoring and reference-map assembly are outside this package's executable reproduction boundary. Their definitions and standalone scoring primitives are preserved, while the run begins at the frozen scored cohort and selection inputs. Neither private inputs nor generated participant predictions are included in GitHub. The data release and Zenodo archive still require author review.
