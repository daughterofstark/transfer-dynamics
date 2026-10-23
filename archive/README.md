# archive

Superseded code, kept for provenance. None of it is part of the reproduction workflow. Scripts may need to be run from the repository root with `PYTHONPATH=.`, and some may not run against the current modules.

| File | What it was |
|---|---|
| `finish_open_items.py`, `propagate_uncertainty.py` | Produced the v16 manuscript numbers (tag `v16-numbers`) |
| `paper_additions.py` | Static cumulative-dose comparator, removed in v17 |
| `intercept_check.py` | v16 model-free intercept check, replaced by the retest check in `run_v17.py` |
| `verify_numbers.py` | v16 verification and sensitivity refits; its data-build helper is now `data_build.py` |
| `finetune_v4.py`, `figure_revisions.py`, `refix_figures.py` | Earlier development scripts |
| `diagnostics/` | Read-only checks of the input extracts used during v17 (see `DECISIONS.md`) |

Diagnostics run from the repository root, for example `PYTHONPATH=. python archive/diagnostics/check_timestamps.py`. The timing section of `check_overlap.py` parses Grand Index dates month-first and is not valid. `check_v16_error.py` needs the v16 merged file `out/merged_for_fit.csv`.
