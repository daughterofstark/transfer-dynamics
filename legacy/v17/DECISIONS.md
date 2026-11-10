# Analysis decisions

Append-only. Where entries conflict, v17 entries supersede earlier ones.

## v17 (October 2026)

**Starting values.** A single start derived from the exponential dose-response function of Osman et al. (2023), which has intercept 1.403, asymptote 4.513 and rate 0.0058 per game.
- The transfer ceiling starts at 4.513 - 1.403 = 3.11, and the transfer learning rate at 1 - exp(-0.0058).
- A single retest identifies only the product of the retest learning rate and ceiling. k_Ld starts at 0.5, and A_d is set so that the predicted retest effect after 70 days equals 1.403.
- Both forgetting rates start at a 730-day half-life, consistent with the decline of practice effects with retest interval reported by Calamia et al. (2012).

**One set of bounds** (rates [1e-6, 0.99], ceilings [0, 30]) for the main fit, bootstrap and cross-validation. Earlier versions used different bounds for different fits.

**Single-start fit, no restarts or fallback bounds.** The bootstrap refits each sample from the point estimate with the primary fit's settings (maxiter 10,000). Failed fits are excluded and reported.

**Removed from the reported analysis:** the static cumulative-dose comparison, the objective-function profile, and the sensitivity refits (weighting, exclusions, winsorizing, rescaling, chain length, gameplay timing). A Grand Index-only fit is retained as a supplementary check.

**One joint uncertainty band.** Maintenance and schedule outcomes are computed for every bootstrap draw from all six parameters.

**Effect size.** Hedges' g for <=50 vs >=501 first-interval gameplays replaces individual-level R-squared as the summary of the training association.

**Short-interval extract: reading between-sitting values.** The extract records days and gameplays since the previous sitting on only one row per sitting; its other rows hold 0. v16 took the first row in file order and so recorded most intervals as same-day with zero gameplays. v17 uses the per-sitting gameplay value.

**Short-interval extract: interval dates.** Intervals are calendar days between the dates of each sitting's first subtest result. This matches how Grand Index intervals are measured; the extract's own days column is based on sitting creation times.

**Short-interval extract: exclusions.**
- One result per subtest per sitting (first attempt kept).
- Chains must start at the participant's first sitting.
- Participants present in both extracts keep only their Grand Index records.

**Weighting bands.** Three interval bands (0-90 including same-day, 91-150, >=151 days). With intervals read correctly, a separate same-day band held 12 participants.

**Fig. 4 and Fig. 5 inputs.** Fig. 4 numbers use the data's mean first interval (110 days). Fig. 5 uses 440 gameplays (22 hours).

## Earlier decisions still in force

**Composite = mean of per-subtest census-normed index scores, with at least three valid subtests.** This keeps the census referencing; a within-sample rank transform would discard it.

**Same-battery chains** where a battery identifier exists, because the averaged composite is not calibrated across batteries.

**Age-group analyses** were removed and not revisited.

**Maintenance and dose language.** The cumulative and steady-state functions are monotone and concave, so the model implies diminishing returns. It does not identify an optimal dose.

## Superseded

v16 decisions on the four-band weighting with a same-day cell, multi-start optimization with a fallback lower bound, the single-start versus two-start bootstrap comparison, and AIC reporting against the static model.

## Corrected re-evaluation (24 October 2026)

**Preserve sitting gameplay metadata before subtest filtering.** The raw per-sitting gameplay maximum is now computed alongside the first-result date, before zero-index and duplicate subtest rows are removed. This recovers counts carried by excluded rows while retaining the same composite scores, sitting selection and calendar intervals. In the original v17 cohort, 492 retained follow-up sittings lost 120,387 gameplays through this ordering error.

**Make the GI battery policy explicit.** The newly supplied original GI extract has battery IDs. IDs 39 and 50 are the older and newer subscriber batteries; three subtests differ in version. The primary re-evaluation keeps each participant's initial same-battery sequence in both extracts. This holds the test battery constant for the model's retest process and applies the rule intended in the earlier analysis decisions. In the GI extract, 133 participants change batteries; trimming 174 records leaves 19 participants without a follow-up. These 19 no longer enter the fit. A missing battery ID raises an error rather than silently changing the policy. `--gi-battery-policy retain` is an explicit alternative for retaining all supplied GI records.

**Use the same group quantity for a figure line and its band.** For each parameter draw in the 3x3 and three-panel dose figures, predict each participant's actual interval inputs, then average within the cell. Percentiles across those means give the band. The former band predicted at cell-average inputs; nonlinear dynamics make that a different quantity.

**Keep the v17 model specification.** The model equations, single Osman-anchored start, chosen 730-day initial half-lives, bounds, optimizer tolerances, weighting scheme, bootstrap seed, five-fold validation and illustrative schedules are unchanged. The 730-day values are numerical starting choices; a quantitative derivation of those values from Calamia et al. has not been established. Calamia et al. support interval and alternate-form effects on retest gains, rather than the exact initial values used here (https://pubmed.ncbi.nlm.nih.gov/22540222/).

**Verify saved artifacts and convergence.** Caches are keyed to raw input checksums, the explicit cohort policy and builder-code hashes, and checked against cached output hashes. Main and validation fits must converge to finite estimates, and figure failures stop the workflow. Bootstrap failures are logged and omitted from intervals. Full-precision fits, validation diagnostics and run provenance are saved. Independent bootstrap fits may run in parallel with the same seed-7 resampling indices and output order; checkpoints are written after every draw.

`CANONICAL_NUMBERS.md` preserves the original v17 snapshot. `REEVALUATION.md` reports the corrected results and validation.
