# Current model specification

For participant i at T2–T5, predicted GI improvement from T1 is the sum of training-related gain G, retest-related gain R, and a baseline correction:

`prediction = G + R + gamma * [GI(T1) - mu(age at T1)] / 15`.

`mu(age) = c0 + c1*t + c2*t^2`, where `t=(age-50)/20`. The reference curve uses T1 scores with the fitting sample's participant weights. It is re-estimated inside each training fold and bootstrap draw. Gamma is profiled by weighted least squares while the six nonlinear coefficients are jointly optimized.

The training coefficients are learning per gameplay kL, forgetting per day kG, and maximum training-related gain A. For a segment of duration delta with p gameplays:

```
learning = 1 - (1-kL) ** (p/delta)
r = clip(1-learning-kG, 1e-9, 1-1e-12)
G_out = G_in * r**delta + learning*A*(1-r**delta)/(1-r)
```

A zero-gameplay segment simply multiplies G by `(1-kG)**delta`. G is bounded to [0,A]. Observed daily counts determine segments; gameplays are treated as uniformly distributed within each exact partial/full calendar day. This is not exact intraday gameplay modeling. `objective.c` caches integer full-day updates for speed.

A test adds retest-learning input `q50*exp(beta*(age-50)/20)` **after** its recorded score. Retest gain then decays over the exact elapsed interval by `(1-kR)**D_exact`. T1 contributes learning to T2, but not to its own baseline score. There is no estimated retest ceiling in the primary specification.

The minimized loss averages squared prediction errors over each participant's valid follow-ups and then averages across participants. A bootstrap count replaces the weight for that participant; no inverse-density or nine-cell weighting is used.

Training and retest half-lives are `log(0.5)/log(1-kG)` and `log(0.5)/log(1-kR)`. They are derived from forgetting coefficients, not extra fitted coefficients. Maintenance dose for fraction f of A solves `learning/(learning+kG)=f`. Simulations use integer daily game counts; Figure 4 displays the continuous regimen's phase-average rate for readability.

## Numerical implementation

`model.py` and `objective.c` implement the primary model and nested retest-saturation comparator. The latter adds alpha via `R_after_test=(1-alpha)*R_before_test+q(age)`. Primary fits fix alpha=0. The array has seven nonlinear slots to share code, but primary fits have only six active nonlinear coefficients plus gamma.

Parameter scales, bounds, starting values and optimizer settings are explicit in `model.py` and `fitting.py`. L-BFGS-B uses analytic derivatives. Rare high-rate partial-day segments reach the numerical retention clamp; ordinary gradients can then be nonzero at a nonsmooth optimum. Tangential stationarity and nondecreasing perturbations on both sides audit these solutions without changing the cohort. Bootstrap seeds are fixed in `paper/specification/bootstrap_seeds.json`.

The compiled function's `mode=1` selects observed daily timing (`mode=0` is its retained interval-uniform code path, not used by the current workflow). Its prediction buffer contains raw G+R. Predictions add the **saved fitting-sample gamma**, ignoring the objective's newly profiled coefficient. Held-out Y does not determine predictions. Tests compare the C recurrence with independent Python predictions and finite-difference derivatives.

## Selected comparisons

- Predictive benchmarks: mean change, retest only, no forgetting, and a saturating cumulative-gameplay curve with separate age-dependent T2–T5 intercepts and no elapsed-time term. Each estimates its own age-reference and baseline correction within the same five training folds.
- Retest saturation: the single alpha term above; same 500 participant resamples.
- Longitudinal age-related change: adds `d50*T + dage*((age-50)*T/20 + T*T/40)`, where T is years since T1; 200 paired resamples. The near-zero-bound retest decay is not reported as a finite biological half-life.
- Slowing training decay: fixed-exponent hyperbolic isolated-input retention, implemented as a mixture of exponential traces. Full-sample optimization uses 48 nodes; folds use 24-node fits and 128-node predictions, with adaptive rate integration for partial-day clamp histories. No parameter bootstrap. The 400-game, 90-day cessation illustration is matched to Figure 4.

Within-person regression is a separate descriptive check. It uses interval GI changes, participant demeaning, equal total participant weights and participant-clustered uncertainty. It is not another component of the primary model.
