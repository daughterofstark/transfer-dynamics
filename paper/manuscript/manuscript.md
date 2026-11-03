# Modeling the durability and maintenance of cognitive training gains in 172,731 adults

Medha Sharma<sup>1</sup> and Robert John Schafer<sup>2,*</sup>

<sup>1</sup> Birla Institute of Technology and Science, Pilani, K K Birla Goa Campus, Zuarinagar, Goa, India.

<sup>2</sup> Lumos Labs, Inc., San Francisco, California, United States.

<sup>*</sup> Correspondence: Robert John Schafer, PhD, Lumos Labs, Inc., 16 Maiden Lane, Suite 600, San Francisco, CA 94108, United States. Email: bschafer@lumoslabs.com.

## Abstract

Sustaining gains from digital cognitive training requires understanding their durability and the training needed to maintain them. We analyzed 96.5 million cognitive training gameplays and 409,486 completions of a separate cognitive test battery from 172,731 adults using a widely available program. A learning-and-forgetting model separately represented training-related gains and retest improvements in the battery's overall composite score. In held-out participants, the model predicted improvement more accurately than a model based on cumulative training amount without accounting for elapsed time. The estimated training-related half-life was 143 days (95% confidence interval 119–170). A maintenance dose of about three gameplays per day (approximately 10 minutes) was predicted to sustain 80% of the estimated maximum training-related gain. In model-driven simulations, both continuous training and periodic boosters sustained gains, with greater fluctuation under the booster regimen. Findings from this large real-world dataset connect cognitive training schedules to durability and provide quantitative targets for prospective comparisons of maintenance and booster regimens.

## Introduction

Cognitive training uses structured, repeated cognitive activities to improve cognitive performance. Digital delivery makes these activities widely accessible and allows the amount and timing of cognitive training to be measured during everyday use, creating opportunities for digital health and digital medicine interventions. Systematic reviews and meta-analyses of randomized trials in cognitively healthy older adults have found modest improvements on untrained cognitive tests [1,2]. A broader meta-analysis encompassing healthy aging and mild cognitive impairment found that benefits varied with the training approach and cognitive outcome [3]. Clinical applications include a digital attention intervention that improved performance on an objective attention test in children with attention-deficit/hyperactivity disorder (ADHD) in a randomized trial [4]. For programs intended for ongoing use, the amount and timing of training needed to sustain improvement are central to intervention design.

Gains on untrained tests are commonly explained through transfer of learning, in which learning acquired through training carries over to performance on tasks that were not trained [1]. Evidence for transfer depends on the relationship between the training and outcome tasks: improvements are more consistently observed on trained or closely related tasks than on more distant cognitive abilities or everyday activities [5]. Reviews of working-memory training and broader cognitive-training programs have found little evidence for far transfer to general cognitive abilities, particularly in studies with stronger controls [6,7]. This variation makes the choice of outcome and comparison condition central to evaluating transfer. The present study examines how performance on such tests changes with cognitive training and elapsed time.

Transfer has been demonstrated across many cognitive training studies [1,2,3], but its dynamics remain less clear: how quickly gains develop, how they decay, and how these processes depend on the training schedule. Trials differ in session duration, weekly frequency, total training period, and subsequent training. ACTIVE provided ten 60–75-minute sessions over five to six weeks, with subsets of participants receiving four 75-minute booster sessions at 11 months and again at 35 months [8,9,10]. Corbett et al. recommended 10 minutes of daily online training over six months [11]. Experiments varying the spacing of a fixed amount of training have produced different results across populations and tasks [12,13,14]. In memory research, the spacing that best supports later recall depends on how long information must be retained [15]. Designing maintenance regimens requires connecting these schedules to the accumulation and loss of gains over time. A model of learning and forgetting could estimate a maintenance dose—the ongoing training needed to sustain a specified level of improvement—and compare continuous use with periodic boosters. For boosters, duration, frequency, and daily intensity together determine the amount of training and the time available for gains to decline between courses.

In this study, we used Lumosity, a widely available digital cognitive training program, because of its prior research characterization and large real-world dataset. The program includes training tasks across multiple cognitive domains [16]. A large randomized, active-controlled trial found greater improvement in an overall composite score from a battery of cognitive tests separate from the training tasks after 10 weeks of cognitive training than after crossword practice [17]. A subsequent observational study by Osman et al. examined the relationship between the amount of cognitive training and test outcomes in 107,005 participants [18].

Osman et al. measured outcomes with the NeuroCognitive Performance Test (NCPT) and found that greater amounts of cognitive training were associated with greater improvement in the battery’s overall composite score [18]. Their fitted curve gradually leveled off, with progressively smaller additional gains at higher amounts of training. The curve separated two sources of improvement. The retest effect, the score gain from repeated exposure to the NCPT itself, was estimated as the gain at zero intervening training. Transfer was the additional improvement associated with cognitive training. The analysis described how gains accumulated with training but did not model how quickly either type of learning developed or was forgotten over calendar time. More recently, Liu et al. linked daily training duration and weekly frequency to improvement in a composite derived from training-task performance in 8,709 adults with subjective cognitive decline, mild cognitive impairment, or mild dementia [19]. These dose–response studies motivate examining how training amount and timing jointly relate to gains on separate cognitive tests and their maintenance.

We analyzed 96.5 million cognitive training gameplays and 409,486 NCPT battery completions from 172,731 adults to estimate durability and maintenance during real-world use. The model described change in the overall NCPT composite score through separate training-related gains and retest improvements, with a correction for baseline performance relative to age. Daily gameplay histories and up to five NCPT testing timepoints per participant provided information about learning and forgetting across different amounts and timing of training. We tested whether the model predicted improvement in held-out participants more accurately than a model based on cumulative training without elapsed time. We then estimated durability after training stops and maintenance doses for specified gains, and compared continuous training with periodic boosters at the same total training amount.

## Methods

### Data and participants

The data linked NCPT testing records to gameplay records from Lumosity (Lumos Labs). A gameplay was one recorded play of a cognitive training game. The NCPT is a web-based battery of cognitive tests with published reliability and validity data [20]. We used records from five NCPT batteries, with five to nine subtests per battery. These batteries have been described in the published NCPT dataset [21]. Battery composition and sample sizes are given in Supplementary Table 2.

During the study period, all subscribers were eligible to take the NCPT. Testing was optional and carried no incentive. Invitations were delivered through in-product messages and emails; prompts for repeat testing did not vary according to prior NCPT performance or cognitive training use. After a test, the NCPT was generally unavailable for 70 days to limit repeated practice. For a small subset of users, this restriction was temporarily shortened or removed to examine test–retest reliability and stability. Availability of these shorter retest intervals was not based on participant characteristics or performance. After testing, users could view raw scores on individual tests, without standardization. The Grand Index (GI), the battery’s overall composite score, was also shown until November 2015, when it was removed. No cognitive training recommendations were presented as part of NCPT testing.

Participants were eligible if their recorded date of birth placed them between 18 and 89 years, inclusive, at their first NCPT testing occasion (T1), their preferred language was English, and their signup country was the United States, Canada, Australia, or New Zealand. We excluded accounts identified as staff, research users, or deleted accounts. We also excluded batteries developed for school or research cohorts and batteries containing verbal list learning. Eligible participants had completed no more than 25 gameplays before T1. Inclusion in the model also required at least two consecutive valid testing occasions using the same NCPT battery and subtests.

We included each participant’s first two to five NCPT testing occasions, labeled T1–T5. Each testing session required valid results for every subtest, with no gap exceeding 24 hours between successive subtest results. Sessions whose subtest records overlapped another session were excluded. A missing or invalid session, or a change in battery or subtests, ended follow-up. Earlier eligible sessions were retained when at least T1 and T2 remained.

For each NCPT testing session, we counted all gameplays recorded before its earliest subtest-result timestamp. Subtracting these counts between successive sessions gave the intervening number of gameplays. Elapsed time in the model was the exact difference between these timestamps, expressed in days. The training-rate eligibility rule used the difference between calendar dates. To limit unusually high training rates, the maximum allowed number of gameplays was 20 × (calendar-day difference + 1); for example, a 30-day interval could contain up to 620 gameplays. The first interval exceeding this limit ended follow-up. There was no upper limit on the number of days between tests. A long interval between NCPT tests could contain both active training and pauses; daily gameplay records distinguished these periods.

We excluded testing sessions with a GI outside 40–160, corresponding to four normative standard deviations from 100. We also excluded changes between successive sessions outside −26.59 to 32.37 points. These change bounds were the mean plus or minus four standard deviations across eligible T1–T2 and T2–T3 intervals before completion and score exclusions. The bounds were then held fixed and applied to all retained intervals through T5. Follow-up ended at the first testing session failing either score criterion. The final cohort contained 172,731 participants and 409,486 NCPT testing sessions between March 2013 and June 2020. Supplementary Tables 1–3 describe participant characteristics, battery composition, and participant selection.

### Outcome measure

The modeled outcome was change from T1 in the overall composite measure from the NCPT battery, expressed as GI points. We constructed a GI for each eligible testing session using census-weighted inverse-normal transformations following Jaffe et al. [21], with additional scoring notes in Supplementary Note 1. Each battery had a reference sample of first NCPT tests from eligible adults with known education and no more than 25 prior gameplays. Reference samples contained at least 1,000 participants and represented all 18 joint age-by-education groups.

The reference groups combined six age ranges, 18–29, 30–39, 40–49, 50–59, 60–69, and 70–89 years, with three educational groups: high school or less; some college, associate’s degree, or college degree; and professional or graduate education. Census weights matched the joint age-by-education distribution of the 2019 US American Community Survey, restricted to ages 18–89. For each subtest, a weighted empirical percentile was transformed to a normal score with mean 100 and standard deviation 15. Equal raw scores received equal percentiles. The subtest scores were averaged, and this average underwent a second weighted inverse-normal transformation to produce the GI. The resulting maps were fixed and applied to every testing session. The five reference samples contained 344,969 participants in total.

### Model

The model described change in the overall NCPT composite score through three contributions (Fig. 1): improvement associated with cognitive training, G; learning retained from previous NCPT tests, R; and a baseline correction, B. Training-related and retest-related gains were zero at T1. At each follow-up, their sum and the baseline correction predicted change from T1:

$$
{\widehat{Y} }_{ij} = {G}_{ij} + {R}_{ij} + {B}_{i},  j \geq  2 \tag{1}
$$

Training-related improvement increased with each gameplay, with diminishing returns as it approached a maximum gain, A. The learning rate kL specified the fraction of the remaining possible improvement acquired per gameplay. For p gameplays in a full calendar day, the learning fraction was ℓ(p) = 1 − (1 − kL) raised to p. With training-related forgetting rate kG per day, the update was:

$$
{G}_{t+1} = {G}_{t} + \ell ({p}_{t})(A - {G}_{t}) - {k}_{G}{G}_{t} \tag{2}
$$

We applied the model to observed daily gameplay counts between successive NCPT tests. Intervals began and ended at the earliest subtest-result timestamps. Test-day gameplays were assigned to intervals according to their timestamps; gameplays after a follow-up timestamp did not contribute to the predicted score at that test. For partial calendar days, gameplay was distributed uniformly within the observed portion of the day, using the corresponding fractional-day update. Inactive periods contributed forgetting alone. The model used each participant's observed daily history rather than their average training rate across a test interval. Supplementary Methods give the fractional-day calculation and numerical checks.

Each NCPT test provided an opportunity for learning that could affect later test performance. The input q(a) depended on age a at T1, in completed years. Its value at age 50 was q50, with β describing its proportional change per 20 years of age. Learning from a test was added after that test and diminished before the next test according to a separate retest forgetting rate kR. For an interval of D elapsed days:

$$
q(a) = {q}_{50} \exp[\frac{\beta (a - 50)}{20}] \tag{3}
$$

$$
{R}_{out} = ({R}_{in} + q(a)){(1 - {k}_{R})}^{D} \tag{4}
$$

The baseline correction accounted for the association between initial performance and subsequent change. Within each fitting sample, we first estimated expected T1 GI as a quadratic function of age, using one baseline score per participant. This age-reference curve was then held fixed while fitting follow-up changes. The difference between a participant's T1 score and this age-specific expectation, expressed in units of 15 GI points, was multiplied by the baseline correction coefficient γ and added to predicted follow-up change:

$$
{B}_{i} = \gamma  \frac{{GI}_{i1} - \mu ({a}_{i})}{15} \tag{5}
$$

$$
\mu (a) = {c}_{0} + {c}_{1}t + {c}_{2}{t}^{2},  t = \frac{a - 50}{20} \tag{6}
$$

The baseline correction coefficient was estimated alongside the learning and forgetting parameters; the correction did not change the GI scores. Predicted change at T1 remained zero by definition.

We jointly fitted seven outcome coefficients: A, kL, kG, q50, β, kR, and γ. Three additional coefficients described the baseline age-reference curve. Durability was expressed as a separate half-life for training-related and retest-related learning, the time for half of the corresponding gain to be lost without another learning input:

$$
{h}_{G} = \frac{\log(0.5)}{\log(1 - {k}_{G})},   {h}_{R} = \frac{\log(0.5)}{\log(1 - {k}_{R})} \tag{7}
$$

### Statistical analyses

We minimized squared differences between predicted and observed GI changes. Squared errors were averaged across each participant's follow-up tests and then across participants, giving each person equal total weight regardless of the number of tests. We used L-BFGS-B optimization with analytic derivatives and multiple starting values. Learning and forgetting rates were bounded between 10⁻⁶ and 0.99, A between 0 and 30 GI points, q50 at zero or above, and β between −3 and 3. The linear baseline coefficient was unconstrained and estimated by least squares within each nonlinear optimizer evaluation. Implementation details are given in the Supplementary Methods.

Uncertainty was estimated from 500 bootstrap samples of participants, with replacement. Each sample retained a selected participant's complete testing and training history. The baseline age-reference curve and all seven outcome coefficients were re-estimated in every sample. Eligibility and score transformations were held fixed. We report the 2.5th and 97.5th percentiles as 95% confidence intervals (CIs), including for half-lives, maintenance doses, and illustrated training contrasts. All primary fits passed convergence checks, and none reached a parameter bound. Predictions, derivatives, and fitting losses were independently checked.

Prediction was evaluated using five-fold cross-validation. Each participant's complete history stayed within one fold, and both the baseline reference and outcome coefficients were estimated using only the other four folds. Root mean squared error (RMSE) used the same participant weighting as fitting. We compared observed and predicted means across training amounts, elapsed time, and testing timepoints. Error bars for observed means were ±1.96 standard errors. Matched benchmarks predicted mean change, retest learning alone, learning without forgetting, or a saturating cumulative-training dose response without calendar time. All benchmarks used the same folds and an age-referenced baseline correction (Supplementary Table 4).

To examine the association within individuals, we also analyzed consecutive-interval GI changes among participants with at least three NCPT tests. This descriptive regression included participant fixed effects, test-occasion indicators, interval duration, prior training, and age and baseline-score interactions with occasion. Each person had equal total weight, with participant-clustered uncertainty. Supplementary Methods provide the specification.

Three selected comparisons examined retest saturation, longitudinal age-related change, and slowing training-related decay. The retest comparison added α in the update (1 − α)R + q(a), allowing the input from a new test to diminish as retest learning accumulated. The aging comparison added a linear change over elapsed years that could vary with baseline age. The slowing-decay comparison replaced exponential training retention with a fixed-shape hyperbolic retention function. Other model components, participants, weighting, and validation folds were matched. Supplementary Table 5 summarizes their predictive performance and durability and maintenance estimates.

The analysis was exploratory, with no prospective sample-size calculation. All records meeting the criteria were included. Missing birth date excluded a participant; missing required test scores ended follow-up. Missing gender or education did not exclude participants from model estimation, although known education was required for the score-reference sample. Analyses used Python, NumPy, SciPy, pandas, and Matplotlib, with a compiled C objective. Versioned dependencies and seeds are recorded in the analysis package. Generative AI tools assisted code development and manuscript preparation; numerical outputs were checked against independent calculations.

### Durability and maintenance illustrations

We illustrated the additional GI improvement predicted for 400 gameplays over 90 days relative to no cognitive training. Age, baseline GI, and NCPT testing history were the same in both predictions, so their retest and baseline contributions canceled. The course distributed integer gameplays evenly as four or five games per day. The resulting contrast was reported primarily in GI points and secondarily in units of the observed T1–T2 change-score SD, 7.219 points, calculated once across all participants. This fixed reference was used for every illustrated contrast.

After the initial 90 days, the illustration compared stopping training, steady maintenance, and periodic boosters through day 360. The two maintenance schedules each provided 840 gameplays over 270 days. Steady maintenance distributed these as three or four games per day, averaging 3.11. Boosters provided 20 games per day for the final 14 days of each 90-day cycle: days 167–180, 257–270, and 347–360. Each booster therefore followed 76 days without training. We summarized predicted gains throughout follow-up and their mean across days 91–360, calculated from end-of-day values. These schedules were evaluated in each bootstrap fit; shaded bands show pointwise 95% confidence intervals for the mean predicted contrasts.

We defined a maintenance dose as the constant daily cognitive training associated with sustaining a specified training-related gain. With d gameplays per day, sustained improvement G* occurs when learning balances forgetting. The corresponding dose for a fraction f of the model's maximum training-related gain A is:

$$
{G}^{*} = \frac{A\ell (d)}{\ell (d) + {k}_{G}},   \ell (d) = 1 - {(1 - {k}_{L})}^{d} \tag{8}
$$

$$
d(f) = \frac{\log[1 - \frac{{k}_{G}f}{1 - f}]}{\log(1 - {k}_{L})} \tag{9}
$$

We report both fractions of the estimated maximum and fixed GI targets. Retest learning and the baseline correction are excluded from these training-related maintenance calculations. For accessibility, approximate time equivalents assume about three minutes per gameplay; actual training duration was not modeled. Minute equivalents are rounded ballpark translations.

### Ethics

This study analyzed existing NCPT and gameplay records collected during routine use of Lumosity. The analysis did not alter participants’ cognitive training or testing. Ethical review was provided by [reviewing institution or ethics committee], which [approval, exemption, or waiver determination; reference number]. Research use of these records was based on [applicable participant consent or authorization, including any waiver of consent]. Internal user identifiers linked cognitive-testing and gameplay records; dates of birth were used to establish eligibility and age at T1.

## Results

### Cognitive training and NCPT testing

The analysis included 172,731 participants who completed the NCPT on 409,486 occasions and played 96.5 million cognitive training games between their first and last included tests. Participants completed the battery an average of 2.37 times; 125,863 (72.9%) completed it twice. Mean age at T1 was 52.9 years (SD 15.7); 54.8% reported female gender, 36.1% male gender, and 9.1% did not report gender. Educational attainment was high school or less for 9.9%, some college or an undergraduate degree for 52.9%, and professional or graduate education for 26.1%; 1.6% reported other education and 9.5% did not report education. Baseline-eligible users who took only T1 were younger on average than users who returned for another test (46.0 versus 53.0 years; Supplementary Table 1).

The most common calendar-day gap between T1 and T2 was 70 days (25.3% of participants). The median was 74 days, and the 90th and 95th percentiles were 206 and 347 days. A total of 3,906 participants (2.3%) repeated the NCPT in fewer than 70 calendar days. Across all 236,755 intervals between successive tests, the mean and median calendar-day gaps were 175 and 90 days, and the longest was 2,558 days. The corresponding mean and median amounts of cognitive training were 407 and 228 gameplays. Figure 2 shows the variation in training amount and test timing.

Between T1 and T2, participants completed a median of 199 gameplays. Mean GI improvement increased from 1.75 points among those completing at most 50 games to 4.75 points among those completing at least 501 games, a difference of 3.00 points. Baseline GI was weakly associated with gameplay count (r = −0.015), while its association with T2 change was stronger (r = −0.180). Among the 46,868 participants with at least three tests, a within-person increase from approximately one to three games per day was associated with 0.74 points more interval improvement after adjustment for interval length, previous training, and the other specified covariates (95% CI 0.62–0.85).

### Agreement between predicted and observed improvement

The model captured the increase in mean GI gain with cognitive training and the smaller gains observed over longer elapsed intervals (Fig. 3). For participants completing 300–500 games between T1 and T2, observed mean improvement was 4.31 points when the interval was at most 100 days and 2.30 points for intervals longer than one year and at most two years. Corresponding held-out predictions were 4.43 and 2.61 points; the no-forgetting model predicted 4.19 and 4.36 points.

Across participants at each testing timepoint, observed mean gains were 3.48 points at T2, 4.40 at T3, 5.48 at T4, and 5.98 at T5. Predicted means were 3.50, 4.31, 5.39, and 6.21 points, respectively. Held-out RMSE was 6.89 GI points, compared with 7.03 for mean change, 6.97 for retest learning alone, 6.92 for learning without forgetting, and 6.92 for the static dose-response model. The dynamic model had lower error than each benchmark in all five folds (Supplementary Table 4).

### Parameter estimates and durability

Table 1 gives the parameter estimates. The estimated maximum training-related gain was 3.97 GI points (95% CI 3.85–4.11). For 400 gameplays over 90 days, the predicted GI advantage over no training was 3.20 points (95% CI 3.10–3.30), equivalent to 0.44 observed change-score SDs (95% CI 0.43–0.46).

The training-related half-life was 143 days (95% CI 119–170). In the illustration, stopping after the initial 90 days reduced the additional GI gain from 3.20 points to 0.87 points by day 360 (Fig. 4a).

Retest learning persisted longer, with an estimated half-life of 1,333 days (95% CI 1,130–1,604). At age 50, the learning input from each NCPT test was 1.46 GI points before subsequent forgetting (95% CI 1.37–1.55). This input was 39.2% smaller for each additional 20 years of age (95% CI 37.6–40.9%). The corresponding point estimates were 2.40 at age 30 and 0.89 at age 70.

A baseline GI 15 points below the expected score for age was associated with 2.68 points more follow-up improvement, conditional on training and testing history (95% CI 2.63–2.72). The bootstrap correlation between the logarithms of the training and retest half-lives was −0.36 (Supplementary Table 6).

### Table 1

| Parameter or equivalent measure | Estimate | 95% CI |
| --- | ---: | ---: |
| **General** | | |
| Baseline correction, γ (GI points per 15-point deviation) | −2.68 | −2.72 to −2.63 |
| **Training-related** | | |
| Maximum gain, A (GI points) | 3.97 | 3.85–4.11 |
| Learning rate, $k_L$ (per gameplay) | 0.00625 | 0.00567–0.00688 |
| Forgetting rate, $k_G$ (per day) | 0.00482 | 0.00407–0.00579 |
| &nbsp;&nbsp;*Equivalent half-life (days)* | 143 | 119–170 |
| **Retest-related** | | |
| Learning input at age 50, $q_{50}$ (GI points) | 1.46 | 1.37–1.55 |
| Age coefficient, β (per 20 years) | −0.498 | −0.526 to −0.471 |
| Forgetting rate, $k_R$ (per day) | 0.000520 | 0.000432–0.000613 |
| &nbsp;&nbsp;*Equivalent half-life (days)* | 1,333 | 1,130–1,604 |

**Table 1.** Model parameter estimates. The model estimates seven outcome coefficients. Each half-life expresses the corresponding forgetting rate in days. Confidence intervals are percentiles from 500 participant bootstrap fits. The three coefficients of the baseline age-reference curve were also re-estimated in every fit; their estimates are given with Supplementary Table 6. Retest input is expressed before subsequent forgetting.

### Steady maintenance and periodic boosters

Continuing at approximately 3.1 gameplays per day after the initial 90-day course sustained an additional gain of about 3.18 GI points through day 360 (Fig. 4a). The relationship between ongoing daily training and sustained improvement showed diminishing returns (Fig. 4b). One gameplay per day sustained 2.24 points (95% CI 2.08–2.39), and two per day sustained 2.86 points (95% CI 2.72–2.99).

Maintaining 80% of the estimated maximum training-related gain, 3.17 GI points, required 3.1 gameplays per day (95% CI 2.7–3.7), roughly ten minutes under the illustrative time conversion. Maintaining 90% required 7.1 gameplays per day (95% CI 6.1–8.4). For a fixed three-point GI advantage, the estimated maintenance dose was 2.4 gameplays per day (95% CI 2.0–2.9).

Periodic boosters produced larger fluctuations in predicted improvement at the same total training amount (Fig. 4a). Before the first booster, the gain fell to 2.22 GI points; the 14-day booster raised it to 3.56. By the third cycle, gains ranged from 2.49 immediately before the booster to 3.60 immediately afterward. Across days 91–360, the mean predicted gain was 2.93 points with boosters and 3.18 with steady maintenance, a difference of 0.25 points (95% CI 0.22–0.28).

Selected comparisons of retest saturation, longitudinal age-related change, and slowing decay are reported in Supplementary Table 5.

## Discussion

This large real-world dataset connects the amount and daily timing of cognitive training to the durability and maintenance of gains on a separate cognitive test battery. Training-related gains had an estimated half-life of about five months, while learning associated with repeated NCPT testing persisted longer. A maintenance dose of about three gameplays per day, approximately ten minutes, was predicted to sustain 80% of the estimated maximum training-related gain. Simulations showed that both continuous training and periodic boosters sustained gains, with greater fluctuation under boosters. Together, these estimates provide a quantitative basis for selecting maintenance doses and schedules to evaluate prospectively.

The leveling off of improvement with greater cognitive training was consistent with Osman et al.'s dose-response analysis of the same program and outcome [18]. Liu et al. also found that improvement depended on training duration and frequency, with age-related differences in dose-response relationships, using performance on the training tasks themselves [19]. The scale and daily detail of the present dataset made it possible to examine how training amount and elapsed time jointly relate to improvement. The learning-and-forgetting model predicted improvement more accurately than the cumulative-training model in each of the five held-out folds. Daily gameplay records distinguished periods of activity and inactivity, and accounting for timing helped predict smaller improvements when similar amounts of training occurred over longer intervals. The within-person association between training rate and interval improvement also indicates that the pattern extends beyond differences between consistently high-use and low-use participants.

Transfer of learning provides one account of improvement on cognitive tests distinct from the training tasks. The program's randomized, active-controlled trial supplies evidence for an advantage over crossword practice [17], while the current analysis describes how training-associated differences vary over time in ordinary use. Broader claims about transfer require attention to task similarity and study design: reviews have found limited far transfer to general abilities [5,6,7], and an experiment manipulating recruitment expectations demonstrated the potential for placebo effects in cognitive-training studies [22]. Our training-related component may combine transfer with changes in engagement, expectations, and familiarity with digital tasks. Randomized comparisons remain important for separating those contributions.

Durability differs across programs and outcomes. In the IMPACT trial, several benefits persisted after three months without contact, although effects were generally smaller and the advantage on the primary outcome was no longer statistically significant [23]. ACTIVE reported cognitive and everyday-function outcomes over five and ten years, with reasoning and processing-speed benefits still detectable at ten years [9,10]. An ACTIVE analysis linked processing-speed training and boosters to gains maintained over five years [24]. The broader skill-retention literature likewise relates loss during nonuse to the skill, training, and retention interval [25]. Such follow-up findings motivate characterizing the time course of gains alongside whether a group difference remains detectable at a particular visit.

Physical exercise provides a related framework for acquiring gains, losing them during detraining, and maintaining them with continued activity [26]. Small studies illustrate variation across outcomes, with some endurance adaptations declining over weeks and strength gains persisting over longer interruptions [27,28]. Fitness–fatigue models also describe the accumulation and decay of training effects [29]. These parallels concern the framework; differences in outcomes, study designs, and reference levels limit direct comparison of numerical half-lives.

Intermittent use has also been studied clinically: an open-label study of a digital therapeutic for pediatric ADHD found that improvements in clinical ratings were maintained during a four-week pause, with further improvement during a second treatment period [30]. In our illustration, continuing at approximately 3.1 games per day—about 70% of the initial daily rate—sustained most of the acquired gain. The maintenance curve makes the relationship between ongoing training and the desired level of improvement explicit.

A maintenance dose expresses the ongoing training associated with sustaining a chosen level of improvement. The estimated dose was about 2.4 games per day for a three-point GI advantage and about 3.1 for 80% of the estimated maximum. The maintenance curve allows these targets to be weighed against the amount of training they require, with progressively more training needed for gains near the estimated maximum. Adherence also matters: in the cognitive-training component of FINGER, 63% of participants began the computerized exercises and 20% completed at least half of the planned sessions, with prior computer use associated with participation [31]. A prospective maintenance study could therefore compare feasible daily and booster schedules after a common initial course, measuring sustained cognitive performance and continued engagement together.

Periodic boosters offer a maintenance option when continuous training is impractical or undesirable. ACTIVE used four-session booster courses at widely separated follow-ups [9,10,24]. In our simulations, two-week boosters every 90 days sustained gains through alternating periods of recovery and decline. With the same total number of gameplays, gains rose above those under steady training after each booster and fell below them between courses, yielding a lower average over the maintenance period. The model can be used to select booster duration, spacing, and daily intensity for a desired average gain or a minimum gain between courses. The illustrated booster schedule concentrated training into roughly an hour per active day, compared with roughly ten minutes daily under steady maintenance. Prospective comparisons could evaluate sustained performance alongside the feasibility and burden of these different schedules.

Scheduling research shows that the best distribution of practice depends on the later outcome of interest. Cepeda et al. related effective spacing to the intended retention interval [15], and Pavlik and Anderson experimentally evaluated schedules selected by a learning model [32]. The present model describes accumulation and loss under observed training schedules; it does not make forgetting depend on spacing. Studies varying training frequency, pauses, and total volume could test the predicted fluctuations between booster courses and whether spacing changes durability itself.

Retest learning was larger in younger adults, consistent with Osman et al. [18] and evidence that repeated-test gains vary with age and test interval [33,34]. Ng et al. found no detectable age-group difference in the training advantage over crossword practice in a reanalysis of the program's randomized trial [35]. Our model allowed age to affect retest learning and assumed a common training response across ages as a simplifying choice. Its simpler retest rule described the first five testing timepoints as well as the saturating comparison. The longer persistence of retest learning highlights its importance for digital intervention studies with repeated cognitive outcomes. Measuring the effects of test exposure alongside training can improve the interpretation of change over follow-up.

The age-referenced baseline correction captured another substantial source of variation in change. A low initial GI relative to the expectation for age was associated with greater subsequent improvement. This pattern can reflect regression to the mean and genuine baseline-related differences in subsequent change, both relevant to the associations discussed by Ng et al. [35]. The correction improves prediction without assigning the baseline-related difference to training or retest learning. Short-interval, low-training repeats in these data were too limited to distinguish measurement variability from real retest-related change precisely.

Training and repeat testing were voluntary. Although test invitations did not depend on previous performance or training amount, motivation, effort, health, and willingness to return could influence both training and outcomes. Participants who returned were older than those with only one recorded test. Ending follow-up at a battery change or failed quality criterion could introduce further selection. The within-person check accounts for stable individual differences but does not remove changing circumstances or effort.

The estimated half-lives and maintenance doses depend on the model. Exponential forgetting gives a constant half-life, whereas other retention functions allow loss to slow [36]. The selected alternatives retained training durability on the scale of several months but differed in longer-term retention and maintenance estimates (Supplementary Table 5). Slowing decay increased retention after a year; its dose for a fixed three-point gain was close to the primary estimate, while its dose for 80% of its own estimated maximum was higher. Adding longitudinal age-related change lengthened the training half-life and moved retest forgetting close to zero, making the retest half-life particularly sensitive to that specification. Bootstrap intervals describe sampling uncertainty within each model.

Some observed patterns remained imperfectly captured. The model underpredicted gains following extended pauses in training and among short-interval repeats. Five testing timepoints provide limited information about eventual saturation of retest learning. The current coefficients describe average relationships and do not estimate individual maintenance requirements. Game selection, difficulty, and domain-specific responses were not modeled separately.

The sample comprised self-selected, English-speaking adults from four countries, many with higher education, using one program during 2013–2020. The findings concern the overall NCPT composite and may differ for individual cognitive domains, clinical populations, or other programs. Daily-function and patient-reported outcomes were unavailable, so the practical significance of a given GI difference requires further study. Changes in the program or testing context, including the final months of the study period, may also affect generalizability.

The scale and temporal detail of these real-world records provide a basis for estimating the durability of cognitive training gains and planning their maintenance. A prospective study could assign continuous training or periodic boosters after a common training course, include planned pauses and resumed training, and vary outcome-test exposure independently where feasible. Measuring sustained cognitive performance, everyday function, and engagement would test both the predicted loss and recovery of gains and the feasibility of the schedules. The resulting evidence could guide maintenance regimens that accommodate different patterns of ongoing use in digital health and digital medicine.

## Data availability

Deidentified participant-level data underlying the results reported in this Article and its Supplementary Information, together with an accompanying data dictionary, will be openly available on Zenodo ([Zenodo DOI]) upon publication.

## Code availability

Custom analysis code used to generate the results reported in this Article and its Supplementary Information, together with software dependencies and instructions for reproducing the analyses, will be openly available on Zenodo ([Zenodo DOI]) upon publication.

## Author contributions

M.S. and R.J.S. conceived and designed the study, developed the methodology, curated the data, developed the analysis software, performed the statistical analyses, validated and interpreted the results, prepared the figures and tables, and drafted and revised the manuscript. R.J.S. provided research resources, supervised the work, and administered the project.

## Acknowledgements

We thank the Lumos Labs research team for their support and scientific discussions.

Lumos Labs, Inc. supported this work through provision of the study data and research resources. R.J.S., an employee of Lumos Labs, contributed to study design, data preparation, analysis, interpretation, and manuscript preparation.

## Competing interests

R.J.S. is employed by Lumos Labs and holds equity in the company. M.S. declares no competing interests.

## References

[1] Lampit, A., Hallock, H. & Valenzuela, M. Computerized cognitive training in cognitively healthy older adults: a systematic review and meta-analysis of effect modifiers. PLoS Med. 11, e1001756 (2014). https://doi.org/10.1371/journal.pmed.1001756

[2] Bonnechère, B., Langley, C. & Sahakian, B. J. The use of commercial computerised cognitive games in older adults: a meta-analysis. Sci. Rep. 10, 15276 (2020). https://doi.org/10.1038/s41598-020-72281-3

[3] Basak, C., Qin, S. & O’Connell, M. A. Differential effects of cognitive training modules in healthy aging and mild cognitive impairment: a comprehensive meta-analysis of randomized controlled trials. Psychol. Aging 35, 220–249 (2020). https://doi.org/10.1037/pag0000442

[4] Kollins, S. H. et al. A novel digital intervention for actively reducing severity of paediatric ADHD (STARS-ADHD): a randomised controlled trial. Lancet Digit. Health 2, e168–e178 (2020). https://doi.org/10.1016/S2589-7500(20)30017-0

[5] Simons, D. J. et al. Do “brain-training” programs work? Psychol. Sci. Public Interest 17, 103–186 (2016). https://doi.org/10.1177/1529100616661983

[6] Melby-Lervåg, M., Redick, T. S. & Hulme, C. Working memory training does not improve performance on measures of intelligence or other measures of “far transfer”: evidence from a meta-analytic review. Perspect. Psychol. Sci. 11, 512–534 (2016). https://doi.org/10.1177/1745691616635612

[7] Sala, G. & Gobet, F. Cognitive training does not enhance general cognition. Trends Cogn. Sci. 23, 9–20 (2019). https://doi.org/10.1016/j.tics.2018.10.004

[8] Ball, K. et al. Effects of cognitive training interventions with older adults: a randomized controlled trial. JAMA 288, 2271–2281 (2002). https://doi.org/10.1001/jama.288.18.2271

[9] Willis, S. L. et al. Long-term effects of cognitive training on everyday functional outcomes in older adults. JAMA 296, 2805–2814 (2006). https://doi.org/10.1001/jama.296.23.2805

[10] Rebok, G. W. et al. Ten-year effects of the ACTIVE cognitive training trial on cognition and everyday functioning in older adults. J. Am. Geriatr. Soc. 62, 16–24 (2014). https://doi.org/10.1111/jgs.12607

[11] Corbett, A. et al. The effect of an online cognitive training package in healthy older adults: an online randomized controlled trial. J. Am. Med. Dir. Assoc. 16, 990–997 (2015). https://doi.org/10.1016/j.jamda.2015.06.014

[12] Wang, Z. et al. Spaced cognitive training promotes training transfer. Front. Hum. Neurosci. 8, 217 (2014). https://doi.org/10.3389/fnhum.2014.00217

[13] Jaeggi, S. M. et al. Investigating the effects of spacing on working memory training outcome: a randomized, controlled, multisite trial in older adults. J. Gerontol. B Psychol. Sci. Soc. Sci. 75, 1181–1192 (2020). https://doi.org/10.1093/geronb/gbz090

[14] Booth, S. J. et al. Experimental investigation of training schedule on home-based working memory training in healthy older adults. Front. Psychol. 14, 1165275 (2023). https://doi.org/10.3389/fpsyg.2023.1165275

[15] Cepeda, N. J., Vul, E., Rohrer, D., Wixted, J. T. & Pashler, H. Spacing effects in learning: a temporal ridgeline of optimal retention. Psychol. Sci. 19, 1095–1102 (2008). https://doi.org/10.1111/j.1467-9280.2008.02209.x

[16] Steyvers, M. & Schafer, R. J. Inferring latent learning factors in large-scale cognitive training data. Nat. Hum. Behav. 4, 1145–1155 (2020). https://doi.org/10.1038/s41562-020-00935-3

[17] Hardy, J. L. et al. Enhancing cognitive abilities with comprehensive training: a large, online, randomized, active-controlled trial. PLoS One 10, e0134467 (2015). https://doi.org/10.1371/journal.pone.0134467

[18] Osman, A. M., Jaffe, P. I., Ng, N. F., Kerlan, K. R. & Schafer, R. J. Transfer of learning: analysis of dose-response functions from a large-scale, online, cognitive training dataset. PLoS One 18, e0281095 (2023). https://doi.org/10.1371/journal.pone.0281095

[19] Liu, L. et al. Dose–response relationship between computerized cognitive training and cognitive improvement. npj Digit. Med. 7, 214 (2024). https://doi.org/10.1038/s41746-024-01210-9

[20] Morrison, G. E., Simone, C. M., Ng, N. F. & Hardy, J. L. Reliability and validity of the NeuroCognitive Performance Test, a web-based neuropsychological assessment. Front. Psychol. 6, 1652 (2015). https://doi.org/10.3389/fpsyg.2015.01652

[21] Jaffe, P. I., Kaluszka, A., Ng, N. F. & Schafer, R. J. A massive dataset of the NeuroCognitive Performance Test, a web-based cognitive assessment. Sci. Data 9, 758 (2022). https://doi.org/10.1038/s41597-022-01872-8

[22] Foroughi, C. K., Monfort, S. S., Paczynski, M., McKnight, P. E. & Greenwood, P. M. Placebo effects in cognitive training. Proc. Natl Acad. Sci. USA 113, 7470–7474 (2016). https://doi.org/10.1073/pnas.1601243113

[23] Zelinski, E. M. et al. Improvement in memory with plasticity-based adaptive cognitive training: results of the 3-month follow-up. J. Am. Geriatr. Soc. 59, 258–265 (2011). https://doi.org/10.1111/j.1532-5415.2010.03277.x

[24] Ball, K. K., Ross, L. A., Roth, D. L. & Edwards, J. D. Speed of processing training in the ACTIVE study: how much is needed and who benefits? J. Aging Health 25, 65S–84S (2013). https://doi.org/10.1177/0898264312470167

[25] Arthur, W. Jr, Bennett, W. Jr, Stanush, P. L. & McNelly, T. L. Factors that influence skill decay and retention: a quantitative review and analysis. Hum. Perform. 11, 57–101 (1998). https://doi.org/10.1207/s15327043hup1101_3

[26] Hickson, R. C. & Rosenkoetter, M. A. Reduced training frequencies and maintenance of increased aerobic power. Med. Sci. Sports Exerc. 13, 13–16 (1981). https://pubmed.ncbi.nlm.nih.gov/7219129/

[27] Coyle, E. F., Martin, W. H. III, Sinacore, D. R., Joyner, M. J., Hagberg, J. M. & Holloszy, J. O. Time course of loss of adaptations after stopping prolonged intense endurance training. J. Appl. Physiol. 57, 1857–1864 (1984). https://doi.org/10.1152/jappl.1984.57.6.1857

[28] Bickel, C. S., Cross, J. M. & Bamman, M. M. Exercise dosing to retain resistance training adaptations in young and older adults. Med. Sci. Sports Exerc. 43, 1177–1187 (2011). https://doi.org/10.1249/MSS.0b013e318207c15d

[29] Morton, R. H., Fitz-Clarke, J. R. & Banister, E. W. Modeling human performance in running. J. Appl. Physiol. 69, 1171–1177 (1990). https://doi.org/10.1152/jappl.1990.69.3.1171

[30] Kollins, S. H., Childress, A., Heusser, A. C. & Lutz, J. Effectiveness of a digital therapeutic as adjunct to treatment with medication in pediatric ADHD. npj Digit. Med. 4, 58 (2021). https://doi.org/10.1038/s41746-021-00429-0

[31] Turunen, M. et al. Computer-based cognitive training for older adults: determinants of adherence. PLoS One 14, e0219541 (2019). https://doi.org/10.1371/journal.pone.0219541

[32] Pavlik, P. I. Jr & Anderson, J. R. Using a model to compute the optimal schedule of practice. J. Exp. Psychol. Appl. 14, 101–117 (2008). https://doi.org/10.1037/1076-898X.14.2.101

[33] Calamia, M., Markon, K. & Tranel, D. Scoring higher the second time around: meta-analyses of practice effects in neuropsychological assessment. Clin. Neuropsychol. 26, 543–570 (2012). https://doi.org/10.1080/13854046.2012.680913

[34] Salthouse, T. A. Influence of age on practice effects in longitudinal neurocognitive change. Neuropsychology 24, 563–572 (2010). https://doi.org/10.1037/a0019026

[35] Ng, N. F., Osman, A. M., Kerlan, K. R., Doraiswamy, P. M. & Schafer, R. J. Computerized cognitive training by healthy older and younger adults: age comparisons of overall efficacy and selective effects on cognition. Front. Neurol. 11, 564317 (2021). https://doi.org/10.3389/fneur.2020.564317

[36] Wixted, J. T. & Ebbesen, E. B. On the form of forgetting. Psychol. Sci. 2, 409–415 (1991). https://doi.org/10.1111/j.1467-9280.1991.tb00175.x

## Figure 1

![Figure 1](figures/Figure_1.svg)

**Figure 1.** Conceptual model of improvement on the NCPT. **a,** Daily cognitive training and periodic NCPT tests shown on a common calendar-time axis. Each small dot represents one day’s gameplay count; test intervals vary. **b,** Corresponding training-related and retest-related contributions to NCPT improvement. Training-related gains build during training and diminish during pauses. Each NCPT test contributes learning to subsequent test performance, with an age-dependent input and a separately estimated forgetting rate. The retest curve shows learning immediately after each test and its retention until the next test; a test’s own score precedes its new learning input. Dotted guides align the test timepoints across rows. **c,** Training-related gain, retest-related gain, and a correction for initial GI relative to age are added to predict change from T1 in the overall NCPT composite at each follow-up. Schedules and curves are qualitative illustrations, with arbitrary vertical scales.

## Figure 2

![Figure 2](figures/Figure_2.svg)

**Figure 2.** Cognitive training and NCPT test timing for 172,731 participants. **a,** Joint distribution of calendar days and gameplays between T1 and T2. Color shows participant counts on a logarithmic scale; displayed axes end at their respective 99th percentiles. **b,** Cumulative distribution of calendar days between T1 and T2. **c,** Cumulative distribution of gameplays between T1 and T2. Both cumulative distributions include all participants and are displayed to 1,000 on their respective horizontal axes.

## Figure 3

![Figure 3](figures/Figure_3.svg)

**Figure 3.** Observed and predicted improvement in the overall NCPT composite (GI). **a,** Mean T1–T2 gains in 20 approximately equal-sized gameplay groups, plotted at mean gameplay counts. All 172,731 participants are represented. **b,** Gains against mean elapsed months for 30,587 participants with 300–500 gameplays between T1 and T2. Bins are 0–100, >100–150, >150–240, >240–365, >365–730, >730–1,460, and >1,460 days; all eligible intervals are included. The longest-interval group contains 36 participants. **c,** Mean gains at T1–T5, with 172,731, 172,731, 46,868, 12,466, and 4,690 participants, respectively. T1 is zero change by definition; later timepoints contain different subsets. Circles and error bars show observed means and approximate 95% confidence intervals. Dashed lines in a and b and squares in c show model predictions, held out by participant and averaged over the same people as the observed means. The model uses participants’ actual daily gameplay histories, test timing, ages, and baseline scores.

## Figure 4

![Figure 4](figures/Figure_4.svg)

**Figure 4.** Model illustrations of durability and maintenance. a, Daily training schedules (upper plot) and additional GI gain relative to no training (lower plot). All schedules start with 400 gameplays over 90 days. Steady maintenance and boosters each add 840 games over the next 270 days: an average of 3.11 games/day, or 20 daily games for 14 days at the end of each 90-day cycle. The upper plot shows average daily rates within each training phase; gain curves use the corresponding integer-day schedules. The third schedule stops after day 90. Comparisons share age, baseline GI, and testing history, so retest and baseline terms cancel. The marker indicates half the acquired gain remaining 143 days after stopping. b, Sustained training-related gain under constant daily training. The marked dose sustains 80% of the estimated maximum gain, 3.17 GI points, at approximately 3.1 games/day (95% CI 2.7–3.7). This target refers to the model maximum. Shading shows pointwise 95% participant-bootstrap intervals. Assuming about three minutes per game, steady maintenance is roughly ten minutes/day and boosters about an hour per active day.
