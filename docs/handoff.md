# Reproduction and author handoff

1. Install the pinned dependencies in a Python 3.12 environment with a C compiler.
2. Obtain the current `timing_input.npz` from Bob. Its SHA-256 must match `paper/specification/inputs.json`; the older private Zenodo draft has a different input. Place it in `data/`. The supplementary aggregate JSON is included in GitHub.
3. Run `python -m unittest discover -s tests -v`.
4. Run `python reproduce.py all --comparisons`, followed by `python tests/check_paper_outputs.py --output outputs`.
5. For a full saved-bootstrap audit, repeat `all` with `--audit-bootstrap`. Independent optimization commands are in [refitting.md](refitting.md).
6. Review `paper/manuscript/manuscript.md` and `supplement.md`. The supplement contents follow the paper's topics and preserve Tables 1–5, Notes 1–7 and Figure 1. Word export remains a separate step.

## What changed since the earlier PR snapshot

- Adopted integer calendar-day learning/forgetting with observed daily gameplay counts; games remain assigned to the correct side of each test.
- Recomputed primary and comparison results, using the same 500 participant bootstrap samples for all four parameterized model specifications.
- Replaced supplemental participant records with aggregate statistics. One private model input plus the included aggregate JSON reproduces the current paper.
- Updated the timing contrast to 400 gameplays over 90 versus 730 days, added six maintenance schedules, and synchronized the revised manuscript, supplement and five figures.
- Consolidated reference results and figure inputs, clarified quick replay versus independent refitting, and documented validation.

The model cohort is 172,731 participants with 409,486 tests and 96,461,780 gameplays. Scoring thresholds and eligibility definitions are unchanged by repository cleanup. See [model.md](model.md), [data_preparation.md](data_preparation.md), and [validation.md](validation.md).

## Next release steps

Review the current code and paper before merging the PR. Prepare a fresh, minimal Zenodo package and repeat its privacy/reproduction checks separately. The existing deposit remains a private draft; nothing here changes its access or publishes data. Refresh Word documents only when the authors request a build.
