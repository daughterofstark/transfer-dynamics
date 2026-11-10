# Validation of the calendar-day analysis

Validated on 5 November 2026 with Python 3.12.14 and the pinned scientific libraries in `requirements.txt`. A C compiler builds the objectives automatically.

## Numerical checks

- Inputs: 172,731 participants, 409,486 NCPT test timepoints, 236,755 intervals and 96,461,780 gameplays. Counts and calendar-day gaps reconcile at every interval. Daily events contain observed integer game counts and nonnegative integer day gaps. Tests divide games chronologically before timestamp fields are removed.
- Primary fits include the full sample, all five held-out folds and all 500 participant bootstrap resamples. Retest saturation, longitudinal age-related change and slowing decay each include the same 500 matched participant bootstrap fits. All selected comparison and benchmark point/fold fits were regenerated using the calendar-day model.
- Independently re-evaluated every saved primary, saturation, aging and slowing-decay bootstrap loss and projected gradient: all 2,000 passed, with zero loss discrepancy in this runtime. No draw was discarded.
- Eight independent unit tests passed in a separate package directory. They cover compiled/Python recurrences, analytic gradients, equal participant weighting, held-out outcome independence, nested comparisons, same-date event ordering, retest input at zero training, and maintenance equilibrium.
- Slowing-decay predictions differed by at most 1.4e-8 GI points between 48- and 128-node quadrature. Selected histories agreed with independent adaptive integration within 3.3e-6 GI points, below the 1e-5 audit tolerance and reporting precision. All 500 slowing-decay bootstrap fits also passed 48-versus-128-node prediction checks; their maximum difference was 1.59e-08 GI points.

## Held-out prediction errors

- primary: 6.890729517 GI points.
- saturating: 6.890729518 GI points.
- mean_change: 7.032379591 GI points.
- retest_only: 6.972630552 GI points.
- no_forgetting: 6.919613595 GI points.
- static_dose_response: 6.916924694 GI points.
- drift: 6.888187533 GI points.
- slowing: 6.890460780 GI points.

## Reproduction boundary and paper reconciliation

The executable workflow starts with the frozen, scored cohort and an aggregate supplement file. Raw warehouse extraction and scoring from source logs are documented but are outside this package's execution boundary. The model file contains no account identifiers, dates of birth, timestamps, absolute dates or participant-level battery/demographic fields beyond whole-year age. Real score trajectories and relative timing remain sensitive data.

The package was copied to a separate directory without compiled libraries or historical project folders. Using the documented installed dependencies, it compiled, replayed all model comparisons and benchmarks, regenerated every numerical table and all five figures, and passed `tests/check_paper_outputs.py`. This validates portability within the installed runtime, not installation on a newly provisioned operating system. Figure exports were visually inspected.

Machine-readable validation and numerical reference outputs are in `paper/reference`. To repeat:

```sh
python -m unittest discover -s tests -v
python reproduce.py all --comparisons --audit-bootstrap
python tests/check_paper_outputs.py --output outputs
```

The local manuscript and supplement include the current equations, estimates, uncertainty, comparison tables and captions. Word export and synchronization to the shared repository/private Zenodo draft are separate publishing steps.

The four parameter-bootstrap sets share all 500 archived participant seeds. The aging set retains its validated first 200 resamples and adds the remaining 300; the slowing-decay set contains 500 newly optimized fits. Point estimates and validation-fold fits did not change. The latter model’s bootstrap half-retention times use the same 400-gameplay, 90-day initial course as the paper, followed by cessation. Numerical reporting uses all four complete bootstrap sets. See `matched_bootstrap_audit.json` for the per-model audit and `paired_bootstrap_summary.json` for paired derived comparisons.

## Repository cleanup and handoff

A fresh Git-file export was checked after consolidating the figure-input paths and documentation. All eight synthetic tests passed; all numerical tables, eight models’ held-out metrics and five figures reproduced. PNG exports are pixel-identical. Mathematical model code, scoring rules, private model input and saved fits are unchanged by this cleanup. See `paper/reference/repository_validation.json`. The 2,000-fit bootstrap audit was completed before cleanup and is retained in `matched_bootstrap_audit.json`; it was not rerun merely for documentation and path changes.

The handoff contains the current Markdown paper, topic-organized supplement with linked contents, five figures, aggregate supplement input and canonical reference outputs. Duplicate figure inputs and obsolete aggregate exports were removed from the repository and preserved in the local project history. No participant-level model input, predictions, absolute local paths or private access tokens are included in the Git candidate. Zenodo and Word builds are separate next steps.
