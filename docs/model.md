# Model specification

At T2–T5, predicted change in GI is training-related gain G, retest-related gain R, and a baseline correction:

`prediction = G + R + gamma * [GI(T1) - mu(age at T1)] / 15`.

`mu(age) = c0 + c1*t + c2*t^2`, where `t=(age-50)/20`. The reference curve uses one T1 score per participant and the fitting sample's weights. It is re-estimated inside each training fold and bootstrap draw. Gamma is profiled by weighted least squares while the six nonlinear coefficients are jointly optimized.

For p observed gameplays on a date followed by D calendar-date boundaries before the next event:

```
G_after_games = A - (A - G_before_games) * (1-kL)**p
G_next = G_after_games * (1-kG)**D
```

Events on the same date have D=0. Gameplay counts on testing dates are split before/after each test using timestamps during extraction. Only games before a test contribute to its score. Inactive dates can be compressed into a single forgetting interval. The model uses integer date differences; the inclusive-day gameplay eligibility limit uses D+1 separately.

A test adds retest input `q50*exp(beta*(age-50)/20)` after its score. Retest gain decays by `(1-kR)**D` between tests. Primary retest input does not depend on accumulated retest gain.

Loss averages squared follow-up errors within each participant and then across participants. Bootstrap counts replace participant weights. Training and retest half-lives are `log(0.5)/log(1-k)`.

Complete simulated training days apply learning then one day of forgetting. End-of-day steady-state gain is `A*(1-kG)*L/[kG+(1-kG)*L]`, with `L=1-(1-kL)**p`. The learning fraction needed for a target fraction f of A is `kG*f/[(1-kG)*(1-f)]`. Dividing `log(1-L)` by `log(1-kL)` gives the required daily dose. Simulations distribute integer game counts across active dates; the schedule diagrams show mean rates for readability.

## Numerical implementation

`model.py` and `objective.c` implement the primary model and retest-saturation comparator. The comparator adds alpha via `R_after_test=(1-alpha)*R_before_test+q(age)`; alpha is fixed at zero in the primary model. Six nonlinear coefficients and gamma are fitted in the primary model. The baseline-age curve has three nuisance coefficients.

L-BFGS-B uses scaled parameters, analytic derivatives, multiple starts for point and validation fits, and projected-gradient convergence checks. Bounds and tolerances are in `model.py`; starts and reference fitting are in `fitting.py`. Bootstrap seeds are in `paper/specification/bootstrap_seeds.json`. No failed resamples are dropped.

Predictions add the saved fitting-sample gamma and baseline-age reference. Held-out outcomes do not determine predictions. Tests compare compiled predictions with an independent Python recurrence, check derivatives and weighting, same-date events, maintenance equilibria, and outcome/reference isolation.

## Supplementary analyses

- Benchmarks: mean change, retest learning only, no forgetting, and a saturating cumulative-gameplay curve with age-dependent T2–T5 intercepts. Each fits its own baseline correction within the same folds.
- Retest saturation: alpha as above; 500 matched participant resamples.
- Longitudinal age-related change: adds `d50*T + dage*((age-50)*T/20 + T*T/40)`, with T in years since T1; 500 matched resamples. Retest half-life is reported as bound-limited when its forgetting coefficient reaches the lower bound.
- Slowing decay: fixed-exponent hyperbolic isolated-input retention, represented by exponential traces. Each trace receives game-count learning then forgetting over calendar days. Point and bootstrap fits use 48 quadrature nodes, validation fits 24, and held-out predictions 128. Adaptive integration supplies independent numerical checks. The same 500 participant resamples are fitted; half-retention is evaluated after the 400-gameplay, 90-day course using 128-node quadrature.
- Within-person regression: a descriptive association between interval gain and training rate, with participant effects, equal participant weights and clustered uncertainty.
