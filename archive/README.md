# Superseded

Kept for provenance. Not part of the reproduction path.

- **refix_figures.py** — redrew figures without a bootstrap. Called `fig_dose_9panel`
  and `fig_dose_row` without `draws=`, silently replacing banded figures with
  unbanded ones, and carried a hardcoded `kft_ci=(6.1e-4, 8.1e-3)` that goes stale
  whenever the fit changes. Use `./run_paper.sh --quick` instead.
- **figure_revisions.py** — bootstrap with rejection sampling of bound-hitting draws.
  Not a valid confidence interval.
- **finetune_v4.py** — short-interval upweighting above the engine's weight cap.
  Abandoned; the same-day weighting cell solved the underlying problem.
