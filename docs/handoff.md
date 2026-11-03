# Handoff to Medha

1. Check out this PR and read the root README. The current workflow is under `paper/`; `legacy/v17/` preserves the earlier analysis.
2. Obtain the two private input NPZs from Bob, place them in `data/`, install requirements and run the synthetic tests.
3. Run `python reproduce.py all --comparisons --audit-bootstrap`. Compare `outputs/tables/` and Figures 1–4 with v23. This audits saved fits; it is not a new bootstrap run.
4. For independent optimization, use the `fit` commands in README, starting with the primary full-sample fit. Keep all fitting outputs and manifests together. Smaller smoke runs are not manuscript uncertainty estimates.
5. Review the PR, especially the frozen eligibility/scoring specification and the distinction between active coefficient slots and fitted parameters. Merge when satisfied.
6. Use the new v23 Word files supplied separately by Bob for collaborative manuscript review. Markdown here is their source; analysis commands do not overwrite it.

## Before submission / Zenodo release

- Confirm author affiliations, corresponding-author information, contributions, competing interests, ethics language and the remaining manuscript placeholders.
- Decide which minimally sufficient participant-level data can be publicly released and approve a data dictionary. Removing identifiers alone is not the release decision.
- Archive the final code commit/tag, exact dependency versions, approved inputs, hashes and full reproduction outputs; create the Zenodo DOI and replace its placeholder in the paper.
- Retain the private upstream extraction, norming-map and account/eligibility audits. The public model reproduction starts with frozen scored arrays and does not claim to rebuild the warehouse extraction.
- Perform a clean-environment run from the approved release tag, then confirm manuscript/source/figure/table versions agree.
- Confirm Communications Psychology's current submission requirements and prepare the journal package. No new journal-format or scientific-model decisions are introduced by this code PR.
