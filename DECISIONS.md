# Analysis decisions

Append-only. Each entry: what was decided, why, and what it rules out.

---

**Main model = merged records, min 2 administrations, T1–T5, no exclusion,
day bins (-1, 0.5, 90, 150, 9999).**
The practice-effect ceiling is only estimable with rapid retakes in the sample; a
same-day retake observes the practice dose with no intervening gameplay and no
elapsed time. Restricted to intervals >1 day, A_d and k_Ld trade off along a flat
ridge and resampled estimates run to the optimization bound.

**Composite = mean of per-subtest census-normed index scores, ≥3 valid subtests.**
Not a within-sample rank transform, which would re-reference scores to this cohort
and discard the deviations from the norm population that carry the signal. INT gave
A_t 3.04 and a low-dose mean of 2.70; the mean composite gives 3.19 and ~2.10.

**Same-battery chains where a battery identifier exists.**
The mean composite is not calibrated across batteries, so a within-participant
change spanning two batteries confounds test content with ability. Chain starts at
the participant's first run and stops at the first battery change.

**Day bins 90/150 with a same-day cell.**
60/150 starves the short-interval cell and drives capped weights with fatter tails.
90/180 is materially identical. Without a same-day cell, rapid retakes fall outside
the day grid entirely and take the weight cap by default.

**Age analysis cut.** Removed from pipeline, figures, and manuscript. Not revisited.

**Report both the asymptotic direct share (63.5%) and the observable share at
T5 (56.4%), labelled distinctly.**
They answer different questions. Neither substitutes for the other.

**Report the single-start bootstrap CI for k_Ft.**
A two-start bootstrap reaches a second basin in 9.5% of resamples, but that basin
implies 80% of the transfer ceiling after ~6 gameplays, which contradicts the
observed dose-response and Osman's independent curve. Excluded on external grounds
and reported in Methods. Both bootstraps agree to three decimals on the lower bound
and on the entire A_t interval.

**ΔAIC reported as a direction of preference.**
Computed from unweighted SSE treating within-participant administrations as
independent, and it scales with sample size. The defensible claim is that the
dynamic model is preferred in every regime, not the magnitude.

**"Optimal dose" claims in the literature are addressed as an inference problem.**
Both the cumulative dose-response and the steady-state maintenance function are
monotone and concave with no interior maximum. That follows from acquisition with
diminishing returns operating against forgetting. A maximum read off a binned
empirical curve does not establish a maximum in the underlying process.

---

## Open

- 7 always-zero subtest ids beyond the expected 12 — confirm un-normed.
- Whether the composite rescaling (15/12.2) is correct: a mean of correlated
  subtests has lower SD partly through reduced measurement error, in which case the
  true signal is not compressed and rescaling would inflate it. Not resolvable from
  these data; carried as a sensitivity.
- `reanalysis_v3.py` missing; exclusion sweep covered by `verify_numbers.py --only sweep`.
