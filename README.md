# Acquisition and forgetting dynamics of cognitive training transfer

Analysis code for a dual-process dynamic model of change on an untrained cognitive
assessment among users of a commercial cognitive training program.

Manuscript: [`manuscript/manuscript_v7.md`](manuscript/manuscript_v7.md)

---

## Run it

```bash
pip install -r requirements.txt
# place inputs in data/ — see data/README.md
./run_paper.sh --quick     # ~10 min, 20 bootstrap resamples — checks the wiring
./run_paper.sh             # ~4 h, 200 resamples — the reported numbers
```

Output lands in `out/`. The canonical number block is echoed at the end of
`out/logs/pipeline_*.log` and mirrored in [`CANONICAL_NUMBERS.md`](CANONICAL_NUMBERS.md).

`run_paper.sh` greps the run manifest for `FAIL` and exits non-zero if it finds
any, so a skipped analysis step cannot pass silently.

---

## The model

Change from each participant's first assessment is the sum of two latent states.

**Practice effect** `S_D`, dosed at every administration toward a ceiling `A_d` with
learning rate `k_Ld`, decaying over elapsed days at `k_Fd`. Independent of gameplay.

**Transfer** `S_T`, accruing with gameplay toward a ceiling `A_t` with learning rate
`k_Lt`, decaying at `k_Ft`.

Six parameters, fitted by weighted least squares with frequency reweighting across
strata of gameplay and elapsed days.

---

## Locked specification

Every reported number comes from one fit. These are fixed:

| | |
|---|---|
| Sample | merged records, ≥2 administrations, first 5 (T1–T5) |
| Exclusions | none — all three available screens are non-binding |
| Weighting | inverse cell frequency, cap 5, gameplays (≤50 / 51–400 / 400+) × days (`-1, 0.5, 90, 150, 9999`) |
| Objective | weighted MSE, averaged within participant then across |
| Optimizer | L-BFGS-B, considered start + ±20% restarts, best reported |
| Uncertainty | 200 participant-level bootstrap resamples |

**The engine defaults do not reproduce this.** `transfer_model.py` ships with the
drop regime (winsorize off, caps 1000/730/20), no T1–T5 truncation, and 90/180 day
bins. Always go through `paper_pipeline.py`, which pins all of the above internally.

**Do not modify `transfer_model.py`.** It is validated to machine precision against
a scalar reference implementation. Every other module imports it unchanged as `ff`.

---

## Layout

```
transfer_model.py       the engine — do not modify
merge_nicole_refit.py   builds the merged dataset from both sources
paper_pipeline.py       canonical pipeline: fits → numbers → figures
figures.py              all figure builders
paper_additions.py      static cumulative-dose baseline

verify_numbers.py       distributions, sensitivities, bootstrap diagnostics
intercept_check.py      model-free check on the practice-effect intercept

run_paper.sh            one command, full reproduction
CANONICAL_NUMBERS.md    every reported number, with provenance
DECISIONS.md            analysis decisions and their rationale
data/                   inputs (gitignored)
out/                    generated output (gitignored)
manuscript/
archive/                superseded scripts — see archive/README.md
```

---

## Entry points

| Command | Runtime |
|---|---|
| `./run_paper.sh` | ~4 h |
| `./run_paper.sh --quick` | ~10 min |
| `python verify_numbers.py --only exposure` | ~1 min |
| `python verify_numbers.py --only sweep` | ~10 min |
| `python verify_numbers.py --only rescale unweighted` | ~5 min |
| `python verify_numbers.py --only halflife` | ~4 h |
| `python intercept_check.py` | ~1 min |

`verify_numbers.py` caches the merged dataset in `_verify_scratch/`; only the first
call pays the build cost. `--rebuild` forces a refresh.

---

## Known issues

**Optional imports fail quietly.** `paper_pipeline.py` wraps `paper_additions` and
`reanalysis_v3` in `try/except`. A missing module skips an analysis step. The
`reanalysis_v3` case now prints a NOTE, and `run_paper.sh` fails the build on any
manifest `FAIL`, but check the manifest before trusting a run.

**`reanalysis_v3.py` is absent.** The exclusion sweep it provided is covered by
`verify_numbers.py --only sweep`, which reports the same four regimes.

**A second optimum exists.** A restart at a fast transfer-forgetting rate converges
to WMSE 53.659 against 53.641, with `k_Lt ≈ 0.23` — implying 80% of the transfer
ceiling after roughly six gameplays. Rejected as inconsistent with the observed
dose-response, which saturates over several hundred. It appears in the Phase 3 probe
output of every run; see `DECISIONS.md`.

---

## Citation

[To complete on acceptance.]
