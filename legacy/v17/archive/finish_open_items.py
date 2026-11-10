"""
finish_open_items.py - the remaining computable items from the v15 completion list.

Imports the engine and helpers unchanged. Uses the same merged-data cache as
verify_numbers.py (_verify_scratch/), so the data build is not repeated.

Sections (run all, or pick with --only):
  env        Python / package versions and git commit                        (instant)
  sample     sample flow, administrations, demographics and dates             (~1 min)
  strata     Supp Table 1 rank correlation (first-interval days vs gameplays)  (~1 min)
  fast       full parameters of the 53.659 solution; where the two solutions
             make different predictions                                       (1 fit)
  cv         5-fold cross-validation with the k_Ft lower bound at 1e-6        (5 fits)
  profile    k_Ft profile extended from 1e-6 to 0.9, swept from both solutions (~60 fits)
  bootstrap  two-start bootstrap, same resamples as Table 1; CIs and derived
             quantities with and without the fast basin                        (400 fits)
  timing     refits with gameplay concentrated early or late in each interval  (8 fits)
  gionly     Grand Index records only, same specification as the main fit      (1 fit)

Run:
  python finish_open_items.py --data data/newsubset.csv --nicole data/short_intervals.csv
  python finish_open_items.py ... --only cv profile
Output: out/open_items/report.md plus CSVs and figures in out/open_items/.
"""
from __future__ import annotations
import argparse, copy, os, subprocess, sys, time
import numpy as np
import pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.optimize import minimize
from scipy.stats import spearmanr

import transfer_model as ff
import paper_pipeline as pp
import figures as figs
import verify_numbers as vn

PO = ff.PARAM_ORDER                       # [k_Lt, k_Ft, k_Ld, k_Fd, A_t, A_d]
OUT = os.path.join("out", "open_items")
REPORT: list[str] = []
B6 = [(1e-6, .99), (1e-6, .99), (1e-6, .99), (1e-6, .99), (0.0, 30.0), (0.0, 100.0)]
MAIN_B = [(1e-6, .99)] * 4 + [(0.0, 30.0), (0.0, 30.0)]   # main-fit bounds


def say(s=""):
    print(s); REPORT.append(s)


def hl(k):
    return float(np.log(0.5) / np.log(1.0 - k)) if 0 < k < 1 else float("nan")


def fmt(x):
    return "  ".join(f"{k}={v:.5g}" for k, v in zip(PO, x))


def header(t):
    say("\n" + "=" * 74); say("  " + t); say("=" * 74)


def load_main(args):
    """Merged + GI-only frames, and the main fit (no figures)."""
    saved = copy.deepcopy(ff.CONFIG)
    newsub, merged = vn.build_merged_once(args)
    df, P, D, Y, w, params, wmse, _ = pp.fit(merged, "MAIN", 2, 5, pp.MAIN_DAY_EDGES,
                                             pp.MAIN_DAY_LBLS, OUT)
    ctx = dict(saved=saved, newsub=newsub, merged=merged, df=df, P=P, D=D, Y=Y, w=w,
               x_hat=np.array([params[k] for k in PO]), wmse=wmse)
    say(f"\n  main fit: WMSE {wmse:.6f}   {fmt(ctx['x_hat'])}")
    return ctx


def fast_solution(ctx):
    """Lowest-objective fit with k_Ft > 0.05, from the considered start (which reached the
    fast basin in the Sept 13 run) and from the point estimate with k_Ft set to 0.3."""
    if "x_fast" not in ctx:
        P, D, Y, w = ctx["P"], ctx["D"], ctx["Y"], ctx["w"]
        x03 = list(ctx["x_hat"]); x03[1] = 0.3
        fits = [ff._fit(x0, P, D, Y, w, MAIN_B) for x0 in (ff.CONFIG["x0_smart"], x03)]
        fast = [r for r in fits if r.x[1] > 0.05]
        if fast:
            r = min(fast, key=lambda r: r.fun)
            ctx["x_fast"], ctx["wmse_fast"], ctx["fast_found"] = np.array(r.x), float(r.fun), True
        else:
            ctx["x_fast"], ctx["wmse_fast"], ctx["fast_found"] = np.array(x03), float("nan"), False
            say("  !! no solution with k_Ft > 0.05 found; fast start set to the point estimate"
                " with k_Ft = 0.3")
    return ctx["x_fast"]


# ------------------------------------------------------------------ sections
def sec_env(ctx):
    header("ENVIRONMENT")
    import scipy
    say(f"  Python {sys.version.split()[0]}   NumPy {np.__version__}   SciPy {scipy.__version__}"
        f"   pandas {pd.__version__}")
    try:
        c = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], text=True).strip()
        dirty = subprocess.check_output(["git", "status", "--porcelain"], text=True).strip()
        say(f"  git commit {c}{' (uncommitted changes present)' if dirty else ''}")
    except Exception as e:
        say(f"  git commit unavailable: {e}")


def sec_sample(ctx, args):
    header("SAMPLE FLOW, ADMINISTRATIONS, DEMOGRAPHICS, DATES")
    m = ctx["merged"].copy()
    m["user_id"] = m["user_id"].astype(str)
    m["nth_test"] = pd.to_numeric(m["nth_test"], errors="coerce")
    comp = m["user_id"].str.startswith(args.uid_prefix)
    for lab, sub in (("Grand Index", m[~comp]), ("averaged composite", m[comp]), ("all", m)):
        say(f"  {lab:20s} participants {sub['user_id'].nunique():>7,}   administrations "
            f"{len(sub):>8,}   after truncation at T5 {int((sub['nth_test'] <= 5).sum()):>8,}")
    Y = ctx["Y"]
    say(f"  post-baseline administrations entering the fit : {int(np.isfinite(Y).sum()):,}")
    say(f"  participants entering the fit                  : {Y.shape[0]:,}")
    say(f"  columns available: {list(m.columns)}")
    t1 = m[m["nth_test"] == 1]
    for col in ("age", "gender", "education_level"):
        if col not in t1.columns:
            say(f"  {col}: not in data"); continue
        for lab, sub in (("GI", t1[~comp.loc[t1.index]]), ("composite", t1[comp.loc[t1.index]])):
            v = sub[col]
            if v.notna().sum() == 0:
                say(f"  {col} [{lab}]: all missing"); continue
            if pd.api.types.is_numeric_dtype(v):
                say(f"  {col} [{lab}]: n={v.notna().sum():,} mean {v.mean():.1f} SD {v.std():.1f}"
                    f" median {v.median():.0f} range {v.min():.0f}-{v.max():.0f}")
            else:
                vc = v.value_counts(normalize=True, dropna=False).head(8)
                say(f"  {col} [{lab}]: " + ", ".join(f"{k} {100*p:.1f}%" for k, p in vc.items()))
    if "signup_date" in m.columns:
        g = m[~comp].copy()
        d = pd.to_datetime(g["signup_date"], errors="coerce") + pd.to_timedelta(
            pd.to_numeric(g["days_since_signup"], errors="coerce"), unit="D")
        say(f"  GI administration dates: {d.min()} to {d.max()} "
            f"(signup_date + days_since_signup; {d.isna().sum():,} unparseable)")
        say("  composite records: days_since_signup is rebuilt from zero at the first run, so"
            " dates cannot be derived here; take them from the raw composite file.")
    else:
        say("  signup_date not in data: collection dates must come from the source extract.")
    try:
        cols = list(pd.read_csv(args.nicole, nrows=0).columns)
        say(f"  composite source columns: {cols}")
    except Exception as e:
        say(f"  composite source header unreadable: {e}")


def sec_strata(ctx):
    header("SUPP TABLE 1 - RANK CORRELATION, FIRST INTERVAL")
    t2 = ctx["df"][ctx["df"]["nth_test"] == 2]
    rho, p = spearmanr(t2["days_interval"], t2["plays_interval"])
    say(f"  Spearman rho(first-interval days, gameplays) = {rho:.3f}  (n = {len(t2):,}, p = {p:.2g})")
    t2b = t2[t2["days_interval"] > 0]
    rho2, _ = spearmanr(t2b["days_interval"], t2b["plays_interval"])
    say(f"  excluding same-day retests                   = {rho2:.3f}  (n = {len(t2b):,})")


def sec_fast(ctx):
    header("THE 53.659 SOLUTION")
    xf = fast_solution(ctx); xh = ctx["x_hat"]
    say(f"  fast    : WMSE {ctx['wmse_fast']:.6f}   {fmt(xf)}")
    say(f"  reported: WMSE {ctx['wmse']:.6f}   {fmt(xh)}")
    say(f"  objective difference {ctx['wmse_fast'] - ctx['wmse']:.6f}")
    say(f"  fast k_Lt / reported k_Lt = {xf[0] / xh[0]:.1f};  transfer half-life "
        f"{hl(xf[1]):.1f} d vs {hl(xh[1]):.0f} d")
    say("  gameplays for 80% of ceiling from zero with no forgetting: "
        f"fast {np.log(0.2) / np.log(1 - xf[0]):.1f}, reported {np.log(0.2) / np.log(1 - xh[0]):.0f}")
    say("\n  where they differ - predicted change at T2 (retest + transfer), 440 gameplays"
        " spread evenly over D days:")
    say("      D     reported      fast")
    for D in (1, 14, 30, 70, 108, 180, 365):
        a = sum(ff.advance_interval(0, 0, D, 440, xh[2], xh[3], xh[0], xh[1], xh[5], xh[4]))
        b = sum(ff.advance_interval(0, 0, D, 440, xf[2], xf[3], xf[0], xf[1], xf[5], xf[4]))
        say(f"    {D:4d}    {a:8.2f}  {b:8.2f}")
    say("\n  and at a fixed 70-day interval, varying gameplays:")
    say("  plays     reported      fast")
    for g in (0, 25, 100, 223, 400, 700, 1500):
        a = sum(ff.advance_interval(0, 0, 70, g, xh[2], xh[3], xh[0], xh[1], xh[5], xh[4]))
        b = sum(ff.advance_interval(0, 0, 70, g, xf[2], xf[3], xf[0], xf[1], xf[5], xf[4]))
        say(f"  {g:5d}    {a:8.2f}  {b:8.2f}")


def sec_cv(ctx):
    header("5-FOLD CROSS-VALIDATION, k_Ft LOWER BOUND 1e-6")
    P, D, Y, w, x0 = ctx["P"], ctx["D"], ctx["Y"], ctx["w"], list(ctx["x_hat"])
    rng = np.random.default_rng(0); n = P.shape[0]; fold = rng.integers(0, 5, n)
    pr, ac, kft = [], [], []
    for fi in range(5):
        tr, te = fold != fi, fold == fi
        r = ff._fit(x0, P[tr], D[tr], Y[tr], w[tr], B6, maxiter=400)
        kft.append(r.x[1])
        pr.append(ff.simulate_matrix(P[te], D[te], r.x)[:, 0]); ac.append(Y[te][:, 0])
    pr, ac = np.concatenate(pr), np.concatenate(ac)
    ok = np.isfinite(pr) & np.isfinite(ac); pr, ac = pr[ok], ac[ok]
    r2 = 1 - np.sum((ac - pr) ** 2) / np.sum((ac - ac.mean()) ** 2)
    say(f"  out-of-sample R2 = {r2:.4f}   MAE = {np.abs(ac - pr).mean():.3f}   N = {len(pr):,}")
    say("  fold k_Ft estimates: " + ", ".join(f"{k:.3g}" for k in kft)
        + f"   (any below 1e-3: {'yes' if min(kft) < 1e-3 else 'no'})")
    saved = ff.CONFIG["k_Ft_lower_bound_tc"], ff.CONFIG["save_dir"]
    ff.CONFIG["k_Ft_lower_bound_tc"], ff.CONFIG["save_dir"] = 1e-6, OUT
    try:
        ff.plot_kfold_calibration(P, D, Y, w, dict(zip(PO, ctx["x_hat"])), k=5)
        say(f"  figure: {OUT}/viz10_calibration.png  (Supplementary Fig. 7)")
    finally:
        ff.CONFIG["k_Ft_lower_bound_tc"], ff.CONFIG["save_dir"] = saved


def sec_profile(ctx, npts_hi=14):
    header("k_Ft PROFILE, 1e-6 TO 0.9, SWEPT FROM BOTH SOLUTIONS")
    P, D, Y, w = ctx["P"], ctx["D"], ctx["Y"], ctx["w"]
    xf = fast_solution(ctx); xh = ctx["x_hat"]
    grid = np.unique(np.r_[np.geomspace(1e-6, 2e-2, 16), np.geomspace(2e-2, 0.9, npts_hi),
                           xh[1], xf[1]])
    b5 = [B6[i] for i in (0, 2, 3, 4, 5)]
    def sweep(order, x0):
        res = {}
        for kft in order:
            f = lambda v: ff.wmse_matrix([v[0], kft, v[1], v[2], v[3], v[4]], P, D, Y, w)
            r = minimize(f, x0, method="L-BFGS-B", bounds=b5,
                         options={"maxiter": 1000, "ftol": 1e-13, "gtol": 1e-9})
            res[kft] = (float(r.fun), r.x); x0 = list(r.x)
        return res
    up = sweep(grid, [xh[i] for i in (0, 2, 3, 4, 5)])
    down = sweep(grid[::-1], [xf[i] for i in (0, 2, 3, 4, 5)])
    rows = []
    for k in grid:
        (fu, xu), (fd, xd) = up[k], down[k]
        best, x = (fu, xu) if fu <= fd else (fd, xd)
        rows.append(dict(k_Ft=k, half_life=hl(k), wmse=best, wmse_from_slow=fu, wmse_from_fast=fd,
                         k_Lt=x[0], k_Ld=x[1], k_Fd=x[2], A_t=x[3], A_d=x[4]))
    t = pd.DataFrame(rows); t.to_csv(f"{OUT}/kft_profile.csv", index=False)
    gmin = t["wmse"].min()
    say("   k_Ft        HL (d)     dWMSE    k_Lt      A_t")
    for r in rows:
        say(f"  {r['k_Ft']:9.3g}  {r['half_life']:9.1f}  {r['wmse'] - gmin:8.4f}  "
            f"{r['k_Lt']:.4g}  {r['A_t']:.3f}")
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.semilogx(t["k_Ft"], t["wmse"] - gmin, "o-", color="#264653", lw=2, ms=5)
    for k, lab, c in ((xh[1], "reported", "#2a9d8f"), (xf[1], "fast solution", "#e76f51")):
        ax.axvline(k, color=c, ls="--", lw=1.5, label=f"{lab} (k_Ft = {k:.3g})")
    ax.set_xlabel("Transfer-forgetting rate k_Ft (per day), fixed")
    ax.set_ylabel("Increase in fitting objective over minimum")
    ax.set_title("Profile of the fitting objective across transfer-forgetting rates")
    ax.grid(alpha=.3, which="both"); ax.legend()
    ax2 = ax.secondary_xaxis("top", functions=(lambda k: np.log(.5) / np.log(1 - np.clip(k, 1e-9, .999)),
                                               lambda h: 1 - .5 ** (1 / np.clip(h, 1e-9, None))))
    ax2.set_xlabel("Half-life (days)")
    fig.tight_layout(); fig.savefig(f"{OUT}/figS4_kft_profile.png", dpi=150); plt.close(fig)
    say(f"  figure: {OUT}/figS4_kft_profile.png  (Supplementary Fig. 4)   csv: kft_profile.csv")


def _schedules():
    H, B, L, R = 547, 1094, 60, 7.0
    rem = B - L * R
    even = np.full(H, B / H)
    fl = np.zeros(H); fl[:L] = R; fl[L:] = rem / (H - L)
    bo = np.zeros(H); bo[:L] = R
    bd = int(round(rem / 2 / R))
    for s in (240, 420): bo[s:s + bd] = R
    bo[L:] *= rem / bo[L:].sum()
    return {"even": even, "load": fl, "boost": bo}


def _derived(x):
    p = dict(zip(PO, x)); out = {}
    for d in (1.0, 2.0, 8 / 3, 5.0):
        g = 1 - (1 - p["k_Lt"]) ** d; out[f"m{d:.2f}"] = 100 * g / (g + p["k_Ft"])
    for lab, s in _schedules().items():
        tr = figs._sim_transfer(s, p, 547)
        out[f"{lab}_end"] = 100 * tr[-1] / p["A_t"]; out[f"{lab}_avg"] = 100 * tr.mean() / p["A_t"]
    return out


def sec_bootstrap(ctx, nboot, seed):
    header(f"TWO-START BOOTSTRAP ({nboot} resamples, same resamples as Table 1)")
    P, D, Y, w = ctx["P"], ctx["D"], ctx["Y"], ctx["w"]
    xh = list(ctx["x_hat"]); xf = list(fast_solution(ctx))
    rng = np.random.default_rng(seed); n = P.shape[0]; rows = []; t0 = time.time()
    for b in range(nboot):
        idx = rng.integers(0, n, n)                   # identical draw sequence to figures._bootstrap
        ra = ff._fit(xh, P[idx], D[idx], Y[idx], w[idx], B6, maxiter=300)
        rb = ff._fit(xf, P[idx], D[idx], Y[idx], w[idx], B6, maxiter=300)
        rows.append(dict(b=b, fa=ra.fun, sa=ra.success, fb=rb.fun, sb=rb.success,
                         **{f"a_{k}": v for k, v in zip(PO, ra.x)},
                         **{f"b_{k}": v for k, v in zip(PO, rb.x)}))
        if (b + 1) % 20 == 0:
            print(f"    {b + 1}/{nboot}  ({time.time() - t0:.0f}s)")
    t = pd.DataFrame(rows); t.to_csv(f"{OUT}/bootstrap_two_start.csv", index=False)
    single = t[t.sa]
    fast_win = t.sb & (t.fb < t.fa - 1e-9)
    say(f"  single start converged: {int(t.sa.sum())}/{nboot}   fast start converged: {int(t.sb.sum())}/{nboot}")
    say(f"  fast start reached a lower objective: {int(fast_win.sum())}/{nboot} "
        f"({100 * fast_win.mean():.1f}%)")
    best = np.array([[r[f"b_{k}"] if fw else r[f"a_{k}"] for k in PO]
                     for (_, r), fw in zip(t.iterrows(), fast_win)])
    keep = (t.sa | fast_win).values
    best = best[keep]
    say(f"  best-of-two draws with k_Ft > 0.1: {int((best[:, 1] > 0.1).sum())}/{len(best)}")
    say("\n  param      estimate   single-start 95%          best-of-two 95%")
    for i, k in enumerate(PO):
        a = np.percentile(single[f"a_{k}"], [2.5, 97.5]); c = np.percentile(best[:, i], [2.5, 97.5])
        say(f"  {k:5s}  {xh[i]:11.5g}   {a[0]:.5g} - {a[1]:.5g}      {c[0]:.5g} - {c[1]:.5g}")
    for k in ("k_Ft", "k_Fd"):
        i = PO.index(k)
        a = np.percentile(single[f"a_{k}"], [2.5, 97.5]); c = np.percentile(best[:, i], [2.5, 97.5])
        say(f"  {k} half-life  single {hl(a[1]):.0f}-{hl(a[0]):.0f} d   best-of-two "
            f"{hl(c[1]):.1f}-{hl(c[0]):.0f} d")
    ds = pd.DataFrame([_derived(single[[f'a_{k}' for k in PO]].values[j]) for j in range(len(single))])
    db = pd.DataFrame([_derived(x) for x in best]); dp = _derived(xh)
    say("\n  derived quantity        point   single-start 95%   best-of-two 95%")
    for c in ds.columns:
        a = np.percentile(ds[c], [2.5, 97.5]); z = np.percentile(db[c], [2.5, 97.5])
        say(f"  {c:18s}  {dp[c]:7.1f}   {a[0]:5.1f} - {a[1]:5.1f}      {z[0]:5.1f} - {z[1]:5.1f}")
    for lab, d in (("single-start", ds), ("best-of-two", db)):
        la = (d.load_avg > d[["even_avg", "boost_avg"]].max(axis=1)).mean()
        ee = (d.even_end > d[["load_end", "boost_end"]].max(axis=1)).mean()
        say(f"  {lab}: load-and-maintain highest average {100 * la:.0f}%; even highest endpoint {100 * ee:.0f}%")
    say("  (m1.00, m2.00, m2.67, m5.00 = steady state at 3, 6, 8, 15 min/day)")


def _sim_timed(P, D, x, frac, where):
    """Engine update with each interval's gameplay concentrated in `frac` of the interval,
    at its start ('front') or end ('back'); frac = 1 reproduces ff.simulate_matrix."""
    k_Lt, k_Ft, k_Ld, k_Fd, A_t, A_d = x
    valid = ~np.isnan(P); Pm = np.where(valid, P, 0.0)
    Dm = np.where(valid, np.maximum(D, 1.0), 1.0)
    SD = np.zeros(P.shape[0]); ST = np.zeros(P.shape[0]); out = np.full(P.shape, np.nan)
    for i in range(P.shape[1]):
        Pi, Di = Pm[:, i], Dm[:, i]
        SD = np.clip(np.maximum(0.0, SD + k_Ld * np.maximum(0.0, A_d - SD)) * (1 - k_Fd) ** Di, 0, A_d)
        Ls = np.minimum(np.maximum(1.0, frac * Di), Di); rest = Di - Ls
        def play(S):
            g = 1.0 - (1.0 - k_Lt) ** (Pi / Ls)
            r = np.clip(1.0 - g - k_Ft, 1e-9, 1.0 - 1e-12)
            omr = np.where(np.abs(1 - r) < 1e-9, 1e-9, 1 - r); rL = r ** Ls
            geo = S * rL + g * A_t * (1 - rL) / omr
            lin = S + Ls * (g * A_t - (g + k_Ft) * S)
            return np.where(np.abs(1 - r) < 1e-9, lin, geo)
        dec = lambda S, t: S * (1 - k_Ft) ** t
        if where == "front": S_play = dec(np.clip(play(ST), 0, A_t), rest)
        else:                S_play = np.clip(play(dec(ST, rest)), 0, A_t)
        ST = np.clip(np.where(Pi > 0, S_play, ST * (1 - k_Ft) ** Di), 0, A_t)
        out[:, i] = np.where(valid[:, i], SD + ST, np.nan)
    return out


def _wmse_timed(x, P, D, Y, w, frac, where):
    pr = _sim_timed(P, D, x, frac, where); v = ~np.isnan(Y)
    se = np.where(v, (Y - pr) ** 2, 0.0).sum(1) / np.maximum(v.sum(1), 1)
    return float((w * se).sum() / w.sum())


def sec_timing(ctx):
    header("TIMING OF GAMEPLAY WITHIN INTERVALS")
    P, D, Y, w = ctx["P"], ctx["D"], ctx["Y"], ctx["w"]
    xh = list(ctx["x_hat"]); xf = list(fast_solution(ctx))
    chk = np.nanmax(np.abs(_sim_timed(P, D, xh, 1.0, "front") - ff.simulate_matrix(P, D, xh)))
    say(f"  check: frac = 1 reproduces the engine (max abs difference {chk:.2e})")
    say("  scenario           WMSE       k_Ft      HL (d)   k_Lt      A_t    A_d    k_Fd    start")
    for frac in (0.5, 0.25):
        for where in ("front", "back"):
            fits = []
            for lab, x0 in (("reported", xh), ("fast", xf)):
                r = minimize(_wmse_timed, x0, args=(P, D, Y, w, frac, where), method="L-BFGS-B",
                             bounds=MAIN_B, options={"maxiter": 10000, "ftol": 1e-13, "gtol": 1e-9})
                fits.append((r.fun, r.x, lab))
            f, x, lab = min(fits, key=lambda z: z[0])
            other = max(fits, key=lambda z: z[0])
            say(f"  {where:5s} {int(frac * 100):3d}%        {f:.4f}  {x[1]:9.3g}  {hl(x[1]):8.1f}  "
                f"{x[0]:.4g}  {x[4]:.3f}  {x[5]:.3f}  {x[3]:.3g}  {lab}"
                f"   (other start: {other[0] - f:+.4f})")
    say(f"  even spread (primary)  {ctx['wmse']:.4f}  {xh[1]:9.3g}  {hl(xh[1]):8.1f}")


def sec_gionly(ctx):
    header("GRAND INDEX RECORDS ONLY (pooling check)")
    saved = copy.deepcopy(ff.CONFIG)
    try:
        _, P, D, Y, w, params, wmse, dAIC = pp.fit(ctx["newsub"], "GI only", 2, 5,
                                                   pp.MAIN_DAY_EDGES, pp.MAIN_DAY_LBLS, OUT)
    finally:
        ff.CONFIG.clear(); ff.CONFIG.update(saved)
    x = [params[k] for k in PO]
    say(f"  N = {P.shape[0]:,}   WMSE = {wmse:.4f}   {fmt(x)}")
    say(f"  transfer half-life {hl(x[1]):.0f} d   retest half-life {hl(x[3]):.0f} d   "
        f"first-retest increment k_Ld*A_d = {x[2] * x[5]:.2f}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data/newsubset.csv")
    ap.add_argument("--nicole", default="data/short_intervals.csv")
    ap.add_argument("--min-valid-subtests", type=int, default=3)
    ap.add_argument("--uid-prefix", default="NIC_")
    ap.add_argument("--nboot", type=int, default=200)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--rebuild", action="store_true")
    ALL = ["env", "sample", "strata", "fast", "cv", "profile", "bootstrap", "timing", "gionly"]
    ap.add_argument("--only", nargs="*", choices=ALL, default=None)
    args = ap.parse_args()
    want = args.only or ALL
    os.makedirs(OUT, exist_ok=True); os.makedirs(vn.SCRATCH, exist_ok=True)
    say(f"# finish_open_items.py - {time.strftime('%Y-%m-%d %H:%M')}   sections: {' '.join(want)}")
    t0 = time.time()
    ctx = load_main(args)
    try:
        for s in want:
            try:
                {"env": lambda: sec_env(ctx), "sample": lambda: sec_sample(ctx, args),
                 "strata": lambda: sec_strata(ctx), "fast": lambda: sec_fast(ctx),
                 "cv": lambda: sec_cv(ctx), "profile": lambda: sec_profile(ctx),
                 "bootstrap": lambda: sec_bootstrap(ctx, args.nboot, args.seed),
                 "timing": lambda: sec_timing(ctx), "gionly": lambda: sec_gionly(ctx)}[s]()
            except Exception as e:
                say(f"\n  !! {s} FAILED: {type(e).__name__}: {e}")
            with open(f"{OUT}/report.md", "w") as fh:
                fh.write("\n".join(REPORT) + "\n")
    finally:
        ff.CONFIG.clear(); ff.CONFIG.update(ctx["saved"])
    say(f"\n  done in {(time.time() - t0) / 60:.0f} min.  report: {OUT}/report.md")
    with open(f"{OUT}/report.md", "w") as fh:
        fh.write("\n".join(REPORT) + "\n")


if __name__ == "__main__":
    main()
