# Acquisition and forgetting dynamics of cognitive training transfer constrain effective training schedules

---

## Abstract

Digital programs for brain and cognitive health are used at scale, yet there is no agreed protocol for how much people should train, or over what period. Proposed optimal doses are read from binned empirical curves without a model that predicts why an optimum should exist. We modelled repeated performance on an untrained cognitive assessment in 81,939 participants of a commercial training program as two latent states: a benefit transferring from gameplay, and a practice effect from repeated testing, each accruing toward a ceiling with diminishing returns and decaying over calendar time. Transfer reached a ceiling of 3.19 assessment points, four fifths of it within roughly 460 gameplays, and decayed with a half-life near one year. The practice effect had a higher ceiling. At steady state, approximately one short game per day sustained two thirds of peak transfer, and at matched total volume schedules differed more in when benefit arrived than in where it ended. Diminishing returns follow from acquisition and forgetting alone, without an optimal dose.

---

Digital interventions for brain and cognitive health now reach very large populations, and cognitive training programs are among the most widely used of them. How much benefit such programs confer, and of what kind, remains actively debated. The strongest disagreements concern the outcomes furthest from the trained activity: whether training produces far transfer to everyday functioning, whether it alters brain structure or function, and whether it modifies the trajectory of cognitive ageing<sup>1,2</sup>. We do not address those questions here. Our focus is the outcome for which the evidence base is most secure: performance on cognitive assessments that are not themselves trained. Randomized, active-controlled trials have shown that training on a commercial program improves scores on an untrained assessment battery<sup>3</sup>, and observational analyses at scale have shown that improvement scales with the amount of training undertaken<sup>4</sup>.

That improvement is what is meant by transfer. The premise is that repeated practice on training tasks strengthens processes general enough to be detected when a different task is administered, and the quantity of interest is how much of that generalized benefit accrues, how quickly, and how long it lasts. Transfer in this sense is separable from a second source of improvement that repeated assessment introduces on its own: familiarity with the assessment itself, which accumulates whether or not any training occurs<sup>4</sup>. Both processes are properties of the measurement setting rather than of everyday cognition, and conclusions drawn about them do not extend to real-world functioning or to neural change.

Against that reasonably secure foundation, there is no comparable basis for deciding how a program should be used. Across trials, prescribed schedules span an order of magnitude in daily duration and differ in weekly frequency, calendar duration, and whether any practice is scheduled after the initial block<sup>5-8</sup>. These schedules have generally been selected for feasibility and scalability rather than derived from dose-finding, a gap stated plainly in the dose literature itself<sup>9,10</sup>. The few experiments that manipulate schedule while holding total dose fixed disagree with one another, with spacing benefits reported in some populations and negligible effects in others<sup>11-13</sup>, and no trial has compared front-loaded, evenly distributed, and periodically boosted regimens under matched total volume in a single sample. Reviews of non-pharmacological interventions have identified the absence of theory-based specification as a central methodological weakness of the field<sup>14</sup>.

A related and less remarked difficulty concerns how dose recommendations are derived. Where optimal doses have been proposed, they are typically identified as the maximum of a binned empirical curve<sup>9</sup>. No account is offered of why a maximum should exist. An acquisition process with diminishing returns, combined with forgetting during gaps, generates a curve that rises and flattens; producing a curve that rises and then falls requires an additional mechanism, and post hoc appeals to fatigue<sup>15</sup> are not derived from any model fitted to the data. Diminishing marginal returns and an optimum beyond which benefit declines are distinct claims, and the empirical support for the first is considerably stronger than for the second.

Analyses of large-scale program records have established the shape of the cumulative dose-response. Improvement on an untrained assessment rises monotonically with intervening gameplay and is well described by an exponential approach to an asymptote, with most of the predicted growth occurring early<sup>4</sup>. That work also separated the gain attributable to repeated assessment from the gain attributable to training, which is a prerequisite for interpreting any dose-response measured through repeated testing. What a cumulative count cannot express is time. The same total gameplay distributed over one month and over one year is a single value on a cumulative axis, so a static dose model cannot represent decay during gaps, cannot state how much ongoing practice preserves a benefit already acquired, and cannot rank schedules that differ only in arrangement.

We therefore modelled improvement on an untrained assessment as the sum of two latent states that accrue toward ceilings with diminishing returns and decay over calendar days: a transfer state driven by gameplay, and a practice-effect state dosed by each administration of the assessment. We estimated the six parameters of that model from the records of 81,939 participants, used them to derive the steady-state daily gameplay that sustains a given fraction of peak transfer, and compared simulated schedules at matched total volume.

---

## Results

### Program use and assessment timing

The sample comprised 81,939 participants contributing 197,843 administrations of the NeuroCognitive Performance Test (NCPT) and [VERIFY] gameplays. Participants contributed a mean of 2.41 administrations each; 58,126 (70.94%) contributed exactly two and 23,813 (29.06%) contributed three or more.

The assessment is offered within the program as an optional structured activity at a nominal cadence near 70 days, and the interval distribution reflects that cadence: the modal first interval was [VERIFY] days, the median [VERIFY] days, the 90th percentile [VERIFY] days and the 95th percentile [VERIFY] days. A total of 3,171 participants (3.87%) repeated the assessment on the same day as their first administration. The longest observed interval was [VERIFY] days.

Gameplays between the first two administrations ranged from 0 to several thousand, with a median of [VERIFY]. Across strata, 9,721 participants (11.86%) recorded 50 or fewer gameplays between their first two administrations, 27,232 (33.23%) recorded 51 to 200, 31,872 (38.90%) recorded 201 to 500, and 13,114 (16.00%) recorded 501 or more. Mean score change at the second administration was +2.10 points in the lowest stratum and +4.92 points in the highest.

Interval length and gameplay varied largely independently (Fig. 1). All cells of a grid crossing three gameplay bands with four interval bands were populated, including low gameplay over long intervals and high gameplay over short intervals (Supplementary Table 1).

### Parameter estimates

Estimates for the six parameters are given in Table 1. The transfer ceiling was 3.19 NCPT points (95% CI 3.02-3.57) and the transfer learning rate 4.16 × 10⁻³ per gameplay (95% CI 3.3-5.4 × 10⁻³). The practice-effect ceiling was 5.55 points (95% CI 4.26-7.40) with a learning rate of 0.400 per administration (95% CI 0.277-0.541), giving a first-administration increment of 2.22 points. The practice-effect state decayed with a half-life of 523 days (95% CI 373-924) and the transfer state with a half-life of 350 days (95% CI 85-1136). Resampling distributions for all six parameters are shown in Fig. 2.

The transfer-forgetting rate was the least precisely estimated parameter. Its profile likelihood was comparatively flat across slow rates and rose across fast rates (Supplementary Fig. 4), and its resampling interval spans half-lives from approximately 3 months to 3 years.

Separating the two ceilings depends on rapid reassessments. Restricted to participants whose first interval exceeded one day, the practice-effect ceiling and its learning rate traded off along a flat ridge and resampled estimates of the ceiling reached the optimization bound; including same-day reassessments, resampled estimates fell away from the bound (Supplementary Fig. 5).

The dynamic model fitted better than a static cumulative-dose model without time dependence (weighted mean squared error 53.64 against 53.92), with the difference concentrated in the practice-effect state. Across four exclusion regimes the transfer ceiling ranged over [VERIFY] points. Restricted to the 23,291 participants with at least three administrations and to their first three administrations, the transfer ceiling was 3.34 points and the transfer learning rate 3.50 × 10⁻³.

**Table 1 | Parameter estimates.** Point estimates with 95% CIs from 200 participant-level bootstrap resamples.

| Parameter | Description | Estimate | 95% CI | Half-life (days) |
|---|---|---|---|---|
| A_t | Transfer ceiling (NCPT points) | 3.19 | 3.02-3.57 | — |
| k_Lt | Transfer learning rate (per gameplay) | 4.16 × 10⁻³ | 3.3-5.4 × 10⁻³ | — |
| k_Ft | Transfer forgetting rate (per day) | 1.98 × 10⁻³ | 0.61-8.1 × 10⁻³ | 350 (85-1136) |
| A_d | Practice-effect ceiling (NCPT points) | 5.55 | 4.26-7.40 | — |
| k_Ld | Practice-effect learning rate (per administration) | 0.400 | 0.277-0.541 | — |
| k_Fd | Practice-effect forgetting rate (per day) | 1.33 × 10⁻³ | 0.75-1.86 × 10⁻³ | 523 (373-924) |

### Observed and modelled change across successive assessment intervals

Among the 23,813 participants with at least three administrations, gameplay in the first interval was crossed with gameplay in the second, and observed mean change at each administration was compared with the model run forward through each participant's own intervals (Fig. 3).

Change at the third administration increased with gameplay in either interval across all nine combinations. In the two largest cells, predicted and observed values at the second and third administrations were 3.91 and 4.83 against 3.77 and 4.72 (n = 7,226), and 3.60 and 4.43 against 3.77 and 4.38 (n = 6,656).

Two cells departed from the observed means. For participants with 50 or fewer gameplays in both intervals (n = 905), the model predicted 3.15 points at the third administration against an observed 2.63. For participants with 400 or more gameplays followed by 50 or fewer (n = 170), the model predicted a decrease from 4.55 to 4.24 points, while observed means increased from 3.37 to 4.90.

### Gameplay, elapsed time and retained change

Over a single interval of the sample mean length (108 days), predicted change rose from 1.92 points at zero gameplay toward an asymptote of 5.12 points, with 80% of the transfer state reached by approximately 472 gameplays (Fig. 4). Over a standardized 90-day window, 80% was reached by approximately 457 gameplays (Supplementary Fig. 2). The rise was monotonic across the full observed range, with no maximum. Among participants recording 25 or fewer gameplays between their first two administrations, observed mean change was 2.00 points (95% CI 1.81-2.19; n = 6,102), containing the modelled intercept of 1.92.

Holding gameplay fixed at 442 and varying the interval, predicted change at the second administration declined from 4.9 points at 1 day to 3.5 points at 365 days (Fig. 5). The practice-effect state contributed 2.2 points at 1 day and 1.4 points at 365 days; the transfer state contributed 2.7 and 2.1 points. The transfer decline is governed entirely by the transfer-forgetting rate and scales with it. Predicted change as a joint function of gameplay and elapsed days is given in Supplementary Fig. 3.

### Maintenance dose

Under a constant daily dose of *d* gameplays, the transfer state gains a fraction *g* = 1 − (1 − *k*<sub>Lt</sub>)<sup>*d*</sup> of its remaining distance to the ceiling each day and loses a fraction *k*<sub>Ft</sub> of the transfer held, giving a steady state

*S*<sub>T</sub>* / *A*<sub>t</sub> = *g* / (*g* + *k*<sub>Ft</sub>).

The steady state is approached from either direction (Fig. 6). Following a 90-day loading phase, a participant holding 95% of the transfer ceiling declines toward the steady state under a maintenance dose of one gameplay per day, and a participant holding 50% rises toward it. At five gameplays per day the steady state is 91%.

At the estimated forgetting rate, 0.5 gameplays per day sustained 51% of the transfer ceiling at steady state, 1 gameplay per day (approximately 3 minutes) sustained 68%, 1.3 sustained 73%, 2 sustained 81%, and 2.74 sustained 85% (Fig. 7). The function is monotonically increasing in dose across the full range. The band spans the resampling interval on the transfer-forgetting rate.

### Simulated training schedules

Three allocations of 1,094 gameplays over 547 days, averaging approximately two gameplays per day, were simulated (Fig. 8): even distribution at 2.00 gameplays per day; a loading phase of 7 gameplays per day for 60 days followed by maintenance at 1.38 per day; and the same loading phase followed by two blocks of approximately 48 days placed 6 months apart with no gameplay between.

The even schedule ended at 80% of the transfer ceiling with a mean of 66% across the horizon. The load-and-maintain schedule reached 79% within its first 60 days, ended at 74%, and had a mean of 73%. The boosted schedule declined to 55% before the first block, recovered above 85% during the second, ended at 75%, and had a mean of 71%. The amplitude of the oscillation in the boosted schedule is governed by the transfer-forgetting rate.

---

## Discussion

Transfer to an untrained assessment accrued quickly and saturated within the range of program use observed here, reaching a ceiling of 3.19 points with four fifths of that attained by roughly 460 gameplays over a 90-day window. The practice effect of repeated assessment had a higher ceiling, 5.55 points, and decayed with a half-life near 17 months. Transfer decayed with a half-life near one year, estimated imprecisely. Applied at steady state, these dynamics imply that approximately one short game per day sustains about two thirds of peak transfer, and that at fixed total volume schedules differ more in when benefit arrives than in where it ends.

The dose-response reproduced here matches the exponential approach to an asymptote reported previously for the same assessment<sup>4</sup>, and the saturation points are close. Adding calendar time changes what can be asked of the data. A static cumulative-dose model describes the transfer state almost as well as the dynamic model, and the algebra explains why: at slow forgetting the dynamic transfer state approximates a function of total gameplay alone. The gain from modelling time appears in the practice-effect state, which decays measurably between administrations, and in the quantities that presuppose a forgetting rate.

Those quantities bear directly on the question of how a program should be used. Where schedule has been manipulated experimentally, the contrasts concern acquisition under fixed total dose and the results have not converged<sup>11-13</sup>. The steady-state framing asks a different question, taking a benefit as already acquired and asking what ongoing rate holds it. The answer here is a low daily dose with sharply diminishing returns above about two gameplays per day. The schedule simulation supplies the three-way comparison at matched volume that trials have not run: front-loading followed by maintenance delivered a higher average benefit across 18 months than even distribution while ending slightly lower, and intermittent blocks separated by long gaps performed less well on both criteria. The advantage of front-loading arises from reaching the ceiling early and holding it, which is the mechanism by which delayed booster blocks were expected to act<sup>5-7</sup>.

The model also speaks to how optimal doses have been inferred. Both the cumulative dose-response (Fig. 4) and the steady-state maintenance function (Fig. 7) are monotonically increasing and concave, with no interior maximum. That shape follows from acquisition with diminishing returns operating against forgetting, and requires no further assumption. Reports of an optimal dose beyond which benefit declines<sup>9</sup> therefore describe something a two-state acquisition-forgetting account does not produce, and identifying such an optimum from the maximum of a binned curve does not by itself establish that a maximum exists in the underlying process. In observational data, apparent declines at the highest doses can also arise from differences between the people who train most and everyone else, and from the practice effect being distributed unevenly across dose groups. Distinguishing genuine non-monotonicity from these alternatives requires a model in which the shape of the dose-response is a consequence of stated mechanisms rather than a description of binned means, and the present results suggest that diminishing marginal returns can be accepted without the stronger claim.

Separating the two states matters for how repeated-assessment designs are interpreted more generally. The practice-effect ceiling exceeded the transfer ceiling, so across administrations a substantial share of observed change is attributable to familiarity with the assessment. Later gains among the heaviest-training participants have the same shape whether they arise from continued transfer or from re-dosed familiarity, and attributing them requires a model that carries both. Where a practice effect is assumed to affect all participants equally and therefore to be safely ignored<sup>9</sup>, that assumption is testable and, in these data, does not hold: the practice-effect state is re-dosed at every administration and decays between them, so its contribution depends on how often and how recently each participant was assessed.

Among the limitations of this analysis, the imprecision of the transfer-forgetting rate is the most consequential. Its resampling interval spans half-lives from roughly 3 months to 3 years, and every maintenance and schedule quantity scales with it: at the fast end of that interval the maintenance dose required to hold a given fraction of the ceiling rises several-fold, and the separation between schedules widens; at the slow end both effects shrink toward the static case. Supplementary Fig. 6 reports each derived quantity across that interval, and the derived quantities should be read with the corresponding range attached rather than at the point estimate alone. A restart from a fast forgetting rate also reaches a distinct and poorer optimum, indicating a second solution these data do not fully exclude.

Three further limitations bound the conclusions. Program use was self-selected, so the dose-response and the schedule comparisons describe what the fitted model implies under an allocation of practice rather than what randomization would establish; no causal or prescriptive claim is supported. Most participants (70.94%) contributed exactly two administrations, so trajectories at later administrations are conditional on continued participation, and the over-prediction of late change in the lowest gameplay stratum may reflect that selection. Individual-level prediction was negligible (out-of-sample *R*² = 0.017), confining all statements to the population level. Regression to the mean contributed to measured change (*r* = −0.157), and treats each gameplay as a uniform unit of practice, setting aside within-session difficulty and adaptivity.

How far these estimates travel beyond one program is an open question with a structured answer. The parameters that are specific to this setting are those expressed in the units of this platform and this assessment: the size of the ceilings in NCPT points, and the learning rate per gameplay, which depends on what a gameplay contains. The structural claims are less tied to the setting: that transfer accrues with diminishing returns toward a ceiling, that it decays over calendar time, that repeated assessment contributes a separable and substantial component with its own dynamics, and that these three together determine a maintenance dose and rank schedules at fixed volume. Programs differing in task content, session length, adaptivity, and outcome measure would be expected to yield different parameter values within the same structure, and the maintenance dose in particular should be expressed as a fraction of a program's own ceiling rather than transferred as a number of minutes. Testing that expectation requires fitting the same model to records from other programs, which is feasible wherever timestamped use is linked to repeated assessment on an untrained measure.

The estimates yield two predictions that randomization could test directly: that a maintenance dose near one short game per day holds most of the transfer benefit once it has been acquired, and that front-loading followed by maintenance delivers benefit earlier than even distribution at equal total volume. Both are stated in quantities a trial can manipulate, and both follow from a model whose parameters were estimated rather than assumed.

---

## Methods

### Data

Records comprised administrations of the NCPT, a web-based cognitive assessment battery with established reliability and validity<sup>16</sup>, linked to gameplay records from a commercial cognitive training program (Lumosity; Lumos Labs). The assessment is offered within the program as an optional structured activity. The analytic sample comprised 81,939 participants contributing 197,843 administrations, analysed across each participant's first five administrations.

For each participant we computed, between consecutive administrations, the number of gameplays and the elapsed days, and expressed each score as a change from that participant's own first administration, which is zero by construction. Three screens were available: a minimum of two administrations, no more than 25 gameplays before the first administration, and limits on implausible interval values. Each removed zero participants, so no participant was excluded.

### Outcome measure

The outcome was the Grand Index, a composite of NCPT subtest scores referenced to a census-normed population with a mean of 100 and an SD of 15. For most participants the Grand Index accompanying each administration was computed by the program's standard method. For the remaining participants, whose Grand Index had not been computed that way, the composite was formed as the mean of the per-subtest index scores for that administration, restricted to administrations with at least three valid subtests. Each per-subtest index is itself census-referenced, so averaging preserves the external referencing, and scores were not renormalized within sample. Composites formed this way had a mean of 109.3 (SD 12.2).

Where a subtest battery identifier was recorded, battery constancy was required within a participant, retaining the leading run of consecutive same-battery administrations and stopping at the first battery change; 64.1% of participants with at least two administrations retained the same battery across their first two. Where no battery identifier was recorded, battery constancy is enforced upstream by the standard Grand Index construction.

### Model

Score change from baseline at any administration was modelled as the sum of two latent states.

The practice-effect state *S*<sub>D</sub> is dosed upward at each administration with diminishing returns toward a ceiling *A*<sub>d</sub>, as *S*<sub>D</sub> → *S*<sub>D</sub> + *k*<sub>Ld</sub>(*A*<sub>d</sub> − *S*<sub>D</sub>), and decays across the elapsed days at rate *k*<sub>Fd</sub>. This state accrues from taking the assessment and is independent of gameplay.

The transfer state *S*<sub>T</sub> accrues from gameplays during an interval toward a ceiling *A*<sub>t</sub> with learning rate *k*<sub>Lt</sub> and decays at rate *k*<sub>Ft</sub>. Gameplays are assumed evenly distributed across an interval, giving a per-day increment *g* = 1 − (1 − *k*<sub>Lt</sub>)<sup>*P*/*D*</sup> for *P* gameplays over *D* days, applied as a closed-form geometric recurrence across the interval. When *k*<sub>Ft</sub> = 0 this reduces exactly to *A*<sub>t</sub>(1 − (1 − *k*<sub>Lt</sub>)<sup>*P*</sup>), a function of total gameplay with interval length cancelling, so all interval-dependence of the transfer state is carried by *k*<sub>Ft</sub>.

### Estimation

Parameters were estimated by minimizing a weighted mean squared error: squared error between predicted and observed score change at every administration, averaged within participant, then averaged across participants with frequency weights. Weights were formed by binning participants on their first interval by gameplays (≤50, 51-400, 400+) crossed with elapsed days (same day, 1-90, 91-150, 151+), then weighting by inverse cell frequency with a cap of five. The same-day cell prevents rapid reassessments from falling outside the day grid. Ten cells were populated and none reached the cap (Supplementary Table 1). This procedure balances representation across observed strata; it is not inverse-propensity weighting and does not remove confounding.

Optimization used L-BFGS-B from a considered starting point with perturbed restarts at ±20%. A restart initialized at a fast transfer-forgetting rate converged to a poorer local optimum (weighted mean squared error 53.659 against 53.641); the best solution across restarts is reported. Uncertainty was estimated by resampling participants with replacement and refitting all six parameters (200 resamples). The transfer-forgetting rate was additionally examined by profile likelihood, fixing it across a grid and re-optimizing the remaining five parameters.

The comparison model was a static cumulative-dose model with no time dependence, in which transfer is *A*<sub>t</sub>(1 − (1 − *k*<sub>Lt</sub>)<sup>cumulative gameplays</sup>) and the practice effect is *A*<sub>d</sub>(1 − (1 − *k*<sub>Ld</sub>)<sup>administrations</sup>), with no decay in either state.

Model calibration was assessed at the second administration and by five-fold cross-validation over participants. In-sample residuals had a mean of 0.07 and an SD of 7.02 (mean absolute error 5.48), with no systematic structure against predicted value, interval length, or gameplay (Supplementary Fig. 7). Held-out performance was comparable, with decile means of observed change on the identity line and *R*² = 0.017 (Supplementary Fig. 8). Mean change at the second administration declined across baseline deciles (*r* = −0.157; Supplementary Fig. 9).

Analyses used Python 3.11 with NumPy, SciPy and pandas.

### Ethics

[TO COMPLETE: ethics committee name and approval or waiver reference; statement that participants consented to research use of de-identified records under the program's terms of service; confirmation of de-identification before analysis.]

### Data availability

[TO COMPLETE.]

### Code availability

[TO COMPLETE: repository URL.]

---

## Figure legends

**Fig. 1 | Program use and assessment timing.** Joint distribution of first-interval elapsed days and gameplays (hexbin, log-scaled counts), with marginal cumulative distributions and the weighting grid overlaid. [fig_exposure.png]

**Fig. 2 | Parameter estimates.** Distributions of the six parameters over 200 participant-level resamples, with point estimates (solid) and 95% intervals (dashed). [fig_param_bootstrap.png]

**Fig. 3 | Observed and modelled change across successive assessment intervals.** Rows, gameplays in the first interval; columns, gameplays in the second. Observed mean change (± 95% CI) against the model run through each participant's own intervals. [fig_dose_9panel.png]

**Fig. 4 | Cumulative dose-response.** Predicted change at the second administration against gameplays at the sample mean interval, partitioned into the practice-effect intercept and the transfer term. [fig_dose_partition.png]

**Fig. 5 | Fixed gameplay across varying intervals.** Predicted change at the second administration for 442 gameplays across intervals from 1 to 365 days, partitioned into the two states. [fig_time_window.png]

**Fig. 6 | A maintenance dose defines a steady state.** Transfer as a percentage of its ceiling following a 90-day loading phase to 50%, 75% or 95%, then a constant maintenance dose. Left, one gameplay per day; right, five per day. [fig_maintenance_concept.png]

**Fig. 7 | Maintenance dose-response.** Steady-state transfer held as a percentage of the transfer ceiling against constant daily dose. Band spans the resampling interval on the transfer-forgetting rate. [fig_maintenance.png]

**Fig. 8 | Training schedules at matched total volume.** Transfer as a percentage of its ceiling under three allocations of 1,094 gameplays over 547 days. Lower panel, daily schedules. [fig_schedules.png]

---

## Supplementary information

**Supplementary Table 1.** Weighting strata by gameplays and elapsed days in the first interval, with participant counts and weights.

**Supplementary Fig. 1.** Cumulative distributions of the first interval in days and gameplays, and of administrations per participant. [fig_cdf.png]

**Supplementary Fig. 2.** Modelled transfer against cumulative gameplay over a standardized 90-day window. [viz5_dose_response.png]

**Supplementary Fig. 3.** Predicted change at the second administration as a joint function of gameplays and elapsed days. [fig_dose_time_heatmap.png]

**Supplementary Fig. 4.** Profile likelihood for the transfer-forgetting rate. [viz9_kFt_profile.png]

**Supplementary Fig. 5.** Resampled estimates of the practice-effect ceiling with and without same-day reassessments. [figS_Ad_identification.png]

**Supplementary Fig. 6.** Sensitivity of derived quantities to the transfer-forgetting rate across its resampling interval: maintenance dose-response, and schedule endpoints and means, evaluated at the lower bound, point estimate and upper bound. [TO GENERATE]

**Supplementary Fig. 7.** Residual diagnostics at the second administration. [viz7_residuals.png]

**Supplementary Fig. 8.** Five-fold out-of-sample calibration. [viz10_calibration.png]

**Supplementary Fig. 9.** Mean change at the second administration by baseline decile. [viz12_regression_to_mean.png]

**Supplementary Fig. 10.** Accrual of the two latent states across five administrations at median program use. [figS_two_channel.png]

---

## References

*Nature style. Entries confirmed against source where marked; remainder to complete.*

1. Simons, D. J. et al. Do "brain-training" programs work? *Psychol. Sci. Public Interest* **17**, 103-186 (2016).
2. Gates, N. J. et al. Computerised cognitive training for preventing dementia in people with mild cognitive impairment. *Cochrane Database Syst. Rev.* https://doi.org/10.1002/14651858.cd012279.pub2 (2019).
3. Hardy, J. L. et al. Enhancing cognitive abilities with comprehensive training: a large, online, randomized, active-controlled trial. *PLoS One* **10**, e0134467 (2015).
4. Osman, A. et al. Transfer of learning: analysis of dose-response functions from a large-scale, online, cognitive training dataset. *PLoS One* **18**, e0281095 (2023).
5. Ball, K. et al. Effects of cognitive training interventions with older adults: a randomized controlled trial. *JAMA* **288**, 2271-2281 (2002).
6. Willis, S. L. et al. Long-term effects of cognitive training on everyday functional outcomes in older adults. *JAMA* **296**, 2805-2814 (2006).
7. Rebok, G. W. et al. Ten-year effects of the ACTIVE cognitive training trial on cognition and everyday functioning in older adults. *J. Am. Geriatr. Soc.* **62**, 16-24 (2014).
8. Corbett, A. et al. The effect of an online cognitive training package in healthy older adults: an online randomized controlled trial. *J. Am. Med. Dir. Assoc.* **16**, 990-997 (2015).
9. Liu, L. et al. Dose-response relationship between computerized cognitive training and cognitive improvement. *npj Digit. Med.* **7**, 214 (2024).
10. Hampstead, B. M., Gillis, M. M. & Stringer, A. Y. Cognitive rehabilitation of memory for mild cognitive impairment: a methodological review and model for future research. *J. Int. Neuropsychol. Soc.* **20**, 135-151 (2014).
11. Wang, Z. et al. Spaced cognitive training promotes training transfer. *Front. Hum. Neurosci.* **8**, 217 (2014).
12. Jaeggi, S. M. et al. Investigating the effects of working memory training in a randomized, controlled, multisite trial in older adults. *J. Gerontol. B Psychol. Sci. Soc. Sci.* (2020).
13. Booth, S. J. et al. Experimental investigation of training schedule on home-based working memory training in healthy older adults. *Front. Psychol.* **14**, 1165275 (2023).
14. Sikkes, S. A. M. et al. Toward a theory-based specification of non-pharmacological treatments in aging and dementia: focused reviews and methodological recommendations. *Alzheimers Dement.* **17**, 255-270 (2021).
15. Holtzer, R., Shuman, M., Mahoney, J. R., Lipton, R. & Verghese, J. Cognitive fatigue defined in the context of attention networks. *Aging Neuropsychol. Cogn.* **18**, 108-128 (2010).
16. Morrison, G. E. et al. Reliability and validity of the NeuroCognitive Performance Test, a web-based neuropsychological assessment. [Journal and year to complete.]
17. Lampit, A., Hallock, H. & Valenzuela, M. Computerized cognitive training in cognitively healthy older adults: a systematic review and meta-analysis of effect modifiers. *PLoS Med.* **11**, e1001756 (2014).
18. Steyvers, M. & Schafer, R. J. Inferring latent learning factors in large-scale cognitive training data. *Nat. Hum. Behav.* **4**, 1145-1155 (2020).

*Refs 5-8, 9-15, 17-18 verified against the reference list of ref 9. Ref 12 volume and pages to complete. Ref 16 to complete.*
