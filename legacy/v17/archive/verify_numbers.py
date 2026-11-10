"""
verify_numbers.py — fills every [VERIFY] and [PENDING] slot in manuscript_v6_JMIR.md.

Reuses paper_pipeline / transfer_model unchanged. Writes verify_report.md plus CSVs.

Sections (run independently with --only):
  exposure    §3.1 modal / median / p90 / p95 first interval, median gameplays   (~1 min)
  halflife    Table 2 half-life CIs from bootstrap draws + second-mode check     (~nboot fits)
  sweep       exclusion-regime range for A_t (4 regimes)                         (4 fits)
  rescale     Limitation: refit with composite deltas rescaled 15/12.2           (1 fit)
  unweighted  Limitation: refit with all weights = 1                             (1 fit)

Run:
  python verify_numbers.py --data newsubset.csv --nicole data/short_intervals.csv
  python verify_numbers.py --data newsubset.csv --nicole "...csv" --only exposure
  python verify_numbers.py --data newsubset.csv --nicole "...csv" --only halflife --nboot 200
"""
from __future__ import annotations
import argparse, copy, os, sys, time, tempfile
import numpy as np
import pandas as pd
from scipy.optimize import minimize

import transfer_model as ff
import paper_pipeline as pp
import composite_extract as mnr
try:
    import paper_additions as add; HAVE_ADD = True
except Exception:
    HAVE_ADD = False

PO = ff.PARAM_ORDER                      # ["k_Lt","k_Ft","k_Ld","k_Fd","A_t","A_d"]
HUGE = 10 ** 9
SCRATCH = "_verify_scratch"

# Bounds used for the bootstrap. k_Ft free from 1e-6 (the reported CI lower bound of
# 6.1e-4 sits below the 1e-3 theoretical floor, so the reported CI came from a free fit).
BOOT_BOUNDS = [(1e-6, 0.99)] * 4 + [(0.0, 30.0), (0.0, 100.0)]

REPORT: list[str] = []


def say(s=""):
    print(s)
    REPORT.append(s)


def half_life(k):
    """Days to lose half the state at per-day rate k."""
    try:
        return float(ff.half_life(k))
    except Exception:
        k = float(k)
        if k <= 0 or k >= 1:
            return float("nan")
        return float(np.log(0.5) / np.log(1.0 - k))


def restore(saved):
    ff.CONFIG.clear(); ff.CONFIG.update(saved)


def build_merged_once(args):
    """Build the merged frame exactly as paper_pipeline does. Cached on disk."""
    cache = os.path.join(SCRATCH, "merged_cache.csv")
    orig = os.path.join(SCRATCH, "orig_cache.csv")
    if os.path.exists(cache) and os.path.exists(orig) and not args.rebuild:
        say("  (using cached merged data; pass --rebuild to force)")
        return pd.read_csv(orig, low_memory=False), pd.read_csv(cache, low_memory=False)
    newsub, merged = pp.build_merged(args.data, args.nicole, args.min_valid_subtests,
                                     args.uid_prefix, cache)
    newsub.to_csv(orig, index=False)
    return newsub, merged


def main_fit(frame, label="MAIN"):
    """The locked main spec: merged, min_tests=2, T1-T5, no exclusion, 90/150 + D0."""
    return pp.fit(frame, label, 2, 5, pp.MAIN_DAY_EDGES, pp.MAIN_DAY_LBLS, SCRATCH)


def fit_under(frame, overrides, day_edges=None, day_lbls=None, weights="freq"):
    """One fit with CONFIG overrides. weights: 'freq' | 'unit'. Returns (params, wmse, dAIC, N)."""
    day_edges = day_edges or pp.MAIN_DAY_EDGES
    day_lbls = day_lbls or pp.MAIN_DAY_LBLS
    ff.CONFIG.update(overrides)
    ff.CONFIG["min_tests"] = 2
    ff.CONFIG["max_test"] = 5
    ff.CONFIG["save_dir"] = SCRATCH
    src = pp._truncate(frame, 5)
    try:
        df = ff.prepare_data(src)
    finally:
        try: os.remove(src)
        except OSError: pass
    if weights == "unit":
        uw = {u: 1.0 for u in df["user_id"].unique()}
    else:
        uw, _ = ff.compute_user_weights(df, ff.CONFIG["play_bin_edges"],
                                        ff.CONFIG["play_bin_labels"], day_edges, day_lbls)
    _, P, D, Y, w, _ = ff.df_to_matrices(df, uw)
    params, _ = ff.run_optimization(P, D, Y, w)
    wmse = float(ff.wmse_matrix([params[k] for k in PO], P, D, Y, w))
    dAIC = np.nan
    if HAVE_ADD:
        try:
            s = add.fit_static_baseline(P, D, Y, w, params)
            dAIC = s["aic_static"] - s["aic_dyn"]
        except Exception:
            pass
    return params, wmse, dAIC, P.shape[0]


# ───────────────────────────── 1. EXPOSURE (§3.1) ─────────────────────────────
def sec_exposure(merged):
    say("\n" + "=" * 72)
    say("  §3.1 EXPOSURE — first-interval days and gameplays")
    say("=" * 72)
    saved = copy.deepcopy(ff.CONFIG)
    try:
        df, P, D, Y, w, params, wmse, dAIC = main_fit(merged, "exposure")
    finally:
        restore(saved)

    # locate the interval columns without assuming a name
    dcol = next((c for c in ("days_interval", "days_btw", "interval_days") if c in df.columns), None)
    pcol = next((c for c in ("plays_interval", "plays_btw", "num_plays_interval") if c in df.columns), None)
    if dcol is None or pcol is None:
        say(f"  !! could not find interval columns. available: {list(df.columns)}")
        return

    t2 = df[df["nth_test"] == 2]
    days = pd.to_numeric(t2[dcol], errors="coerce").dropna()
    plays = pd.to_numeric(t2[pcol], errors="coerce").dropna()

    say(f"\n  n with a first interval : {len(days):,}")

    # --- mode: report the shape, not just one number. The same-day retakes put a
    #     large spike at 0, so give the mode with and without it.
    vc = days.round().astype(int).value_counts().sort_values(ascending=False)
    say("\n  ten most common first-interval lengths (days, rounded):")
    for v, n in vc.head(10).items():
        say(f"     {v:>5} d : {n:>7,}  ({100*n/len(days):5.2f}%)")
    nz = days[days >= 1]
    vc_nz = nz.round().astype(int).value_counts()
    say(f"\n  MODE (all intervals)         : {vc.index[0]} days   (n={vc.iloc[0]:,})")
    say(f"  MODE (intervals >= 1 day)    : {vc_nz.idxmax()} days   (n={vc_nz.max():,})")
    say("     -> use the >=1 day mode in §3.1 if the overall mode is 0 (same-day retakes),")
    say("        and state the same-day count separately as the manuscript already does.")

    q = days.quantile([.25, .50, .75, .90, .95, .99])
    say(f"\n  DAYS   median = {q[.50]:.0f}   p25 = {q[.25]:.0f}   p75 = {q[.75]:.0f}")
    say(f"         p90    = {q[.90]:.0f}   p95 = {q[.95]:.0f}   p99 = {q[.99]:.0f}   max = {days.max():.0f}")

    qp = plays.quantile([.25, .50, .75, .90, .95])
    say(f"\n  PLAYS  median = {qp[.50]:.0f}   p25 = {qp[.25]:.0f}   p75 = {qp[.75]:.0f}")
    say(f"         p90    = {qp[.90]:.0f}   p95 = {qp[.95]:.0f}   max = {plays.max():.0f}")

    say(f"\n  same-day first interval (== 0 d) : {int((days == 0).sum()):,} "
        f"({100*(days == 0).mean():.2f}%)   [manuscript states 3,171 / 3.87%]")
    say(f"  longest first interval           : {days.max():.0f} d")
    say(f"  longest interval, any position   : "
        f"{pd.to_numeric(df[dcol], errors='coerce').max():.0f} d   "
        f"[Methods cites ~2,095 d]")

    # total gameplays across the whole analytic sample (headline figure for §3.1)
    all_plays = pd.to_numeric(df[pcol], errors="coerce").fillna(0)
    total_plays = float(all_plays.sum())
    say(f"\n  TOTAL gameplays across all analysed intervals : {total_plays:,.0f}")
    say(f"    (sum of {pcol} over every interval in the fitted sample)")
    for col in ("num_plays_before", "plays_cum", "cum_plays"):
        if col in df.columns:
            last = (df.sort_values(["user_id", "nth_test"])
                      .groupby("user_id")[col].last())
            say(f"  alt: sum of final {col} per participant   : "
                f"{pd.to_numeric(last, errors='coerce').fillna(0).sum():,.0f}")
            break
    say("    -> use the larger, better-defined of these in §3.1; state which one.")

    say("\n  >>> PASTE INTO §3.1:")
    say(f'      "The modal first interval was {vc_nz.idxmax()} days, the median {q[.50]:.0f} days, '
        f'the 90th percentile {q[.90]:.0f} days and the 95th percentile {q[.95]:.0f} days."')
    say(f'      "...with a median of {qp[.50]:.0f}." (gameplays)')

    pd.DataFrame({"days": days.values}).to_csv(f"{SCRATCH}/first_interval_days.csv", index=False)


# ─────────────────────── 2. HALF-LIFE CIs + SECOND MODE ───────────────────────
def _fit_from(x0, P, D, Y, w):
    r = minimize(lambda x: ff.wmse_matrix(x, P, D, Y, w), np.asarray(x0, float),
                 method="L-BFGS-B", bounds=BOOT_BOUNDS,
                 options={"maxiter": 500, "ftol": 1e-12})
    return r.x, float(r.fun)


def sec_halflife(merged, nboot, seed):
    say("\n" + "=" * 72)
    say("  TABLE 2 — half-life CIs from bootstrap draws, and second-mode check")
    say("=" * 72)
    saved = copy.deepcopy(ff.CONFIG)
    try:
        df, P, D, Y, w, params, wmse, dAIC = main_fit(merged, "halflife")
        x_hat = np.array([params[k] for k in PO], float)

        # two starts per resample: the point estimate, and a fast-forgetting start.
        # The Phase-3 probe in the pipeline log lands at k_Ft ~ 0.371, so a single
        # start from x_hat cannot see that basin.
        x_fast = x_hat.copy(); x_fast[PO.index("k_Ft")] = 0.30

        rng = np.random.default_rng(seed)
        n = P.shape[0]
        draws, fast_wins, t0 = [], 0, time.time()
        say(f"\n  bootstrapping {nboot} resamples x 2 starts (n={n:,}) …")
        for b in range(nboot):
            idx = rng.integers(0, n, n)
            Pb, Db, Yb, wb = P[idx], D[idx], Y[idx], w[idx]
            xa, fa = _fit_from(x_hat, Pb, Db, Yb, wb)
            xb, fb = _fit_from(x_fast, Pb, Db, Yb, wb)
            if fb < fa - 1e-9:
                fast_wins += 1
                draws.append(xb)
            else:
                draws.append(xa)
            if (b + 1) % 25 == 0:
                say(f"    {b+1}/{nboot}   ({time.time()-t0:.0f}s)")
        Dr = np.array(draws)
        np.savetxt(f"{SCRATCH}/bootstrap_draws.csv", Dr, delimiter=",",
                   header=",".join(PO), comments="")

        say(f"\n  resamples where the fast-k_Ft start won : {fast_wins}/{nboot} "
            f"({100*fast_wins/nboot:.1f}%)")
        kft = Dr[:, PO.index("k_Ft")]
        say(f"  draws with k_Ft > 0.01 (HL < 69 d)      : {int((kft > 0.01).sum())}/{nboot}")
        say(f"  draws with k_Ft > 0.10                  : {int((kft > 0.10).sum())}/{nboot}")
        say("     -> if these are ~0, the fast basin is not supported by resampled data")
        say("        and the single-start CI in the manuscript is safe to report.")
        say("        if non-trivial, report the bimodality in the Discussion.")

        say("\n  PARAMETER  point        2.5%         97.5%")
        for i, k in enumerate(PO):
            lo, hi = np.percentile(Dr[:, i], [2.5, 97.5])
            say(f"   {k:5s}   {x_hat[i]:.6g}   {lo:.6g}   {hi:.6g}")

        say("\n  HALF-LIVES (days) — computed per draw, then percentiled:")
        for k in ("k_Ft", "k_Fd"):
            i = PO.index(k)
            hl = np.array([half_life(v) for v in Dr[:, i]])
            hl = hl[np.isfinite(hl)]
            lo, hi = np.percentile(hl, [2.5, 97.5])
            say(f"   {k}: point {half_life(x_hat[i]):.0f} d   95% CI [{lo:.0f}, {hi:.0f}] d"
                f"   = [{lo/365:.2f}, {hi/365:.2f}] yr")
            say(f"        (manuscript Table 2 currently: "
                f"{'350 (85-1136)' if k=='k_Ft' else '523 (373-924)'})")

        # profile-likelihood 95% bound, so the flat-vs-estimated question is settled
        # on a likelihood scale rather than on raw WMSE units.
        nobs = int(np.isfinite(Y).sum())          # Y is NaN-padded to (n_users, n_int)
        say(f"\n  PROFILE-LIKELIHOOD REFERENCE")
        say(f"    valid observations (approx)     : {nobs:,}")
        say(f"    WMSE at optimum                 : {wmse:.6f}")
        thr = wmse * 3.84 / max(nobs, 1)
        say(f"    95% one-parameter threshold     : ΔWMSE = {thr:.6f}")
        say(f"    -> draw a horizontal line at WMSE = {wmse + thr:.6f} on Figure S5;")
        say(f"       the k_Ft values below it are the profile-likelihood interval.")
        say(f"       (inflate the threshold by the design effect if clustering matters:")
        say(f"        ~2.4 administrations per participant -> use ~1.4x, ΔWMSE = {1.4*thr:.6f})")
    finally:
        restore(saved)


# ─────────────────────────── 3. EXCLUSION SWEEP ───────────────────────────
def sec_sweep(merged):
    say("\n" + "=" * 72)
    say("  §3.2 EXCLUSION SWEEP — A_t across four regimes")
    say("=" * 72)
    # engine defaults are the DROP regime: winsorize=False + caps 1000/730/20
    regimes = [
        ("drop extreme intervals",
         dict(winsorize_outliers=False, max_plays_interval=1000,
              max_days_interval=730, max_plays_per_day=20)),
        ("winsorize extreme intervals",
         dict(winsorize_outliers=True, max_plays_interval=1000,
              max_days_interval=730, max_plays_per_day=20)),
        ("raised plays limit (3000)",
         dict(winsorize_outliers=True, max_plays_interval=3000,
              max_days_interval=730, max_plays_per_day=20)),
        ("no exclusion",
         dict(winsorize_outliers=False, max_plays_interval=HUGE,
              max_days_interval=HUGE, max_plays_per_day=HUGE)),
    ]
    rows = []
    saved = copy.deepcopy(ff.CONFIG)
    try:
        for label, ov in regimes:
            say(f"\n  ── {label} ──")
            try:
                restore(saved)
                params, wmse, dAIC, N = fit_under(merged, ov)
                rows.append(dict(regime=label, N=N, wmse=wmse, dAIC=dAIC,
                                 **{k: params[k] for k in PO}))
            except Exception as e:
                say(f"    FAILED: {type(e).__name__}: {e}")
    finally:
        restore(saved)

    if not rows:
        return
    t = pd.DataFrame(rows)
    say(f"\n  {'regime':30s} {'N':>8} {'A_t':>7} {'A_d':>7} {'k_Ft':>9} {'dAIC':>7}")
    say("  " + "-" * 72)
    for r in rows:
        say(f"  {r['regime']:30s} {r['N']:>8,} {r['A_t']:>7.3f} {r['A_d']:>7.3f} "
            f"{r['k_Ft']:>9.5f} {r['dAIC']:>7.0f}")
    say(f"\n  A_t range across regimes : {t['A_t'].min():.2f} – {t['A_t'].max():.2f}")
    say(f"  dAIC range               : {t['dAIC'].min():.0f} – {t['dAIC'].max():.0f}")
    say(f"  dynamic model preferred in {int((t['dAIC'] > 0).sum())}/{len(t)} regimes")
    say("\n  >>> PASTE INTO §3.2:")
    say(f'      "the transfer ceiling ranged over {t["A_t"].min():.2f}-{t["A_t"].max():.2f} points '
        f'and the dynamic model was preferred in every regime."')
    t.to_csv(f"{SCRATCH}/exclusion_sweep.csv", index=False)


# ──────────────── 4. RESCALED REFIT (scale caveat, Discussion) ────────────────
def sec_rescale(merged, uid_prefix, sd_target=15.0, sd_source=12.2):
    say("\n" + "=" * 72)
    say(f"  LIMITATION — refit with composite deltas rescaled by {sd_target}/{sd_source}")
    say("=" * 72)
    f = sd_target / sd_source
    m = merged.copy()
    m["user_id"] = m["user_id"].astype(str)
    m["nth_test"] = pd.to_numeric(m["nth_test"], errors="coerce")
    m["normed_score"] = pd.to_numeric(m["normed_score"], errors="coerce")

    # scale each composite participant's deviations about their own first score, so
    # score deltas scale exactly by f and the baseline is untouched.
    is_comp = m["user_id"].str.startswith(uid_prefix)
    base = (m[is_comp].sort_values(["user_id", "nth_test"])
              .groupby("user_id")["normed_score"].first())
    b = m.loc[is_comp, "user_id"].map(base)
    m.loc[is_comp, "normed_score"] = b + (m.loc[is_comp, "normed_score"] - b) * f
    say(f"  rescaled {is_comp.sum():,} rows from {base.shape[0]:,} composite participants "
        f"(factor {f:.4f})")

    saved = copy.deepcopy(ff.CONFIG)
    try:
        params, wmse, dAIC, N = fit_under(m, pp.NOEXCL)
    finally:
        restore(saved)
    say(f"\n  N = {N:,}   WMSE = {wmse:.4f}   dAIC = {dAIC:.0f}")
    say("  PARAM        rescaled     manuscript    Δ%")
    ref = dict(k_Lt=0.0041567, k_Ft=0.0019811, k_Ld=0.39994,
               k_Fd=0.0013245, A_t=3.1939, A_d=5.5453)
    for k in PO:
        d = 100 * (params[k] - ref[k]) / ref[k]
        say(f"   {k:5s}   {params[k]:>11.6g}  {ref[k]:>11.6g}  {d:>+7.1f}%")
    say(f"\n  k_Ft half-life: {half_life(params['k_Ft']):.0f} d "
        f"(manuscript 350 d)")
    say("  >>> If k_Ft falls back toward the floor here, the forgetting signal is")
    say("      partly a scale artifact and the Discussion must say so.")


# ────────────────── 5. UNWEIGHTED REFIT (weighting caveat) ──────────────────
def sec_unweighted(merged):
    say("\n" + "=" * 72)
    say("  LIMITATION — refit with all participant weights = 1")
    say("=" * 72)
    saved = copy.deepcopy(ff.CONFIG)
    try:
        params, wmse, dAIC, N = fit_under(merged, pp.NOEXCL, weights="unit")
    finally:
        restore(saved)
    say(f"\n  N = {N:,}   WMSE = {wmse:.4f}   dAIC = {dAIC:.0f}")
    say("  PARAM      unweighted     manuscript    Δ%")
    ref = dict(k_Lt=0.0041567, k_Ft=0.0019811, k_Ld=0.39994,
               k_Fd=0.0013245, A_t=3.1939, A_d=5.5453)
    for k in PO:
        d = 100 * (params[k] - ref[k]) / ref[k]
        say(f"   {k:5s}   {params[k]:>11.6g}  {ref[k]:>11.6g}  {d:>+7.1f}%")
    say(f"\n  k_Ft half-life: {half_life(params['k_Ft']):.0f} d (manuscript 350 d)")
    say("  >>> Quote the largest |Δ%| among A_t and k_Ft in Limitation on weighting.")


# ───────────────────────────────── main ─────────────────────────────────
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="newsubset.csv")
    ap.add_argument("--nicole", required=True)
    ap.add_argument("--min-valid-subtests", type=int, default=3)
    ap.add_argument("--uid-prefix", default="NIC_")
    ap.add_argument("--nboot", type=int, default=200)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--rebuild", action="store_true", help="ignore cached merged data")
    ap.add_argument("--only", nargs="*", default=None,
                    choices=["exposure", "halflife", "sweep", "rescale", "unweighted"])
    args = ap.parse_args()

    os.makedirs(SCRATCH, exist_ok=True)
    want = set(args.only) if args.only else {"exposure", "halflife", "sweep",
                                             "rescale", "unweighted"}

    say(f"# verify_numbers.py — {time.strftime('%Y-%m-%d %H:%M')}")
    say(f"  data={args.data}")
    say(f"  nicole={args.nicole}")
    say(f"  bootstrap bounds: k_* in [1e-6, 0.99], A_t in [0, 30], A_d in [0, 100]")

    newsub, merged = build_merged_once(args)

    if "exposure" in want:   sec_exposure(merged)
    if "halflife" in want:   sec_halflife(merged, args.nboot, args.seed)
    if "sweep" in want:      sec_sweep(merged)
    if "rescale" in want:    sec_rescale(merged, args.uid_prefix)
    if "unweighted" in want: sec_unweighted(merged)

    out = "verify_report.md"
    with open(out, "w") as fh:
        fh.write("\n".join(REPORT) + "\n")
    print(f"\n\n  wrote {out}   (scratch files in {SCRATCH}/)")


if __name__ == "__main__":
    main()
