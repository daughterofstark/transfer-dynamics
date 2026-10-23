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
