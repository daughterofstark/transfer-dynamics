"""
run_v17.py - v17 refit with Osman-anchored starting values (single start, one bound set, joint bootstrap).

  * one start, derived from Osman et al. 2023 (no restarts, no k_Ft probe, no fallback bound)
  * one bound set for every fit: rates [1e-6, 0.99], ceilings [0, 30]
  * bootstrap: 200 resamples, each started at the point estimate, same optimizer settings
    as the primary fit (maxiter 10,000), same draw sequence as figures._bootstrap (seed 7)
  * joint-bootstrap band only (no k_Ft-only sweep); no static comparator; no profile
  * Grand Index-only fit (Supplementary Table 3) and cross-validation with the same settings
  * data checks: Hedges' g, 1-69-day intervals, held-out decile agreement

transfer_model.py and figures.py are imported unchanged; CONFIG overrides are in memory.

Run:
  python run_v17.py --data data/newsubset.csv --composite data/short_intervals.csv --nboot 20 --skip-figures
  caffeinate -i python run_v17.py --data data/newsubset.csv --composite data/short_intervals.csv
Output: out/v17/report.md, draws.npy, bootstrap_info.csv, cv_deciles.csv, fig_main/, fig_supp/
"""
from __future__ import annotations
import argparse, os, subprocess, sys, time
import numpy as np
import pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

import transfer_model as ff
import paper_pipeline as pp
import figures as figs
import data_build as db

PO = ff.PARAM_ORDER                      # [k_Lt, k_Ft, k_Ld, k_Fd, A_t, A_d]
OUT = os.path.join("out", "v17")
REPORT: list[str] = []

# ---------------------------------------------------------------- starting values
# Osman et al. (2023) PLoS One 18:e0281095, Eq. 1:  dY = a + (b - a)(1 - exp(-c N))
OSMAN_A, OSMAN_B, OSMAN_C = 1.403, 4.513, 0.0058
HL_START_DAYS = 730.0        # practice-effect decline with retest interval (Calamia et al. 2012)
KLD_START = 0.5              # first repeat administration acquires half the retest ceiling
OSMAN_INTERVAL = 70.0        # Osman's T2 invitation interval; the interval his intercept refers to


def osman_start():
    kF = 1 - 0.5 ** (1 / HL_START_DAYS)
    return [1 - np.exp(-OSMAN_C),                                   # k_Lt
            kF,                                                     # k_Ft
            KLD_START,                                              # k_Ld
            kF,                                                     # k_Fd
            OSMAN_B - OSMAN_A,                                      # A_t
            OSMAN_A / (KLD_START * (1 - kF) ** OSMAN_INTERVAL)]  # A_d


BOUNDS = [(1e-6, 0.99)] * 4 + [(0.0, 30.0), (0.0, 30.0)]
SEPT13 = np.array([0.0041568, 0.0019811, 0.39994, 0.0013245, 3.1939, 5.5453])
FAST_KFT = 0.1
MINUTES = (3, 4, 6, 8, 15)
NAMES = {"even": "Even training", "load": "Front-load plus maintenance",
         "boost": "Front-load plus boosters"}


# ---------------------------------------------------------------- helpers
def say(s=""):
    print(s); REPORT.append(s)
    with open(os.path.join(OUT, "report.md"), "w") as fh:
        fh.write("\n".join(REPORT) + "\n")


def header(t):
    say("\n" + "=" * 74); say("  " + t); say("=" * 74)


def hl(k):
    return float(np.log(0.5) / np.log(1 - k)) if 0 < k < 1 else float("nan")


def fmt(x):
    return "  ".join(f"{k}={v:.5g}" for k, v in zip(PO, x))


def prepare(frame):
    ff.CONFIG.update(pp.NOEXCL)
    ff.CONFIG.update(min_tests=2, max_test=5, save_dir=OUT)
    src = pp._truncate(frame, 5)
    try:
        df = ff.prepare_data(src)
    finally:
        os.remove(src)
    uw, _ = ff.compute_user_weights(df, ff.CONFIG["play_bin_edges"], ff.CONFIG["play_bin_labels"],
                                    pp.MAIN_DAY_EDGES, pp.MAIN_DAY_LBLS)
    uids, P, D, Y, w, _ = ff.df_to_matrices(df, uw)
    return df, uids, P, D, Y, w


def fit_and_check(P, D, Y, w, x0, label):
    t0 = time.time()
    r = ff._fit(list(x0), P, D, Y, w, BOUNDS)
    x, g = np.asarray(r.x), np.asarray(r.jac)
    at_lo = np.array([x[i] - lo < 1e-8 for i, (lo, hi) in enumerate(BOUNDS)])
    at_hi = np.array([hi - x[i] < 1e-8 for i, (lo, hi) in enumerate(BOUNDS)])
    pg = np.where(at_lo, np.minimum(g, 0), np.where(at_hi, np.maximum(g, 0), g))
    header(f"FIT: {label}")
    say(f"  N = {P.shape[0]:,}   WMSE = {r.fun:.6f}   ({time.time() - t0:.0f} s)")
    say(f"  converged = {r.success}   message: {r.message}")
    say(f"  iterations = {r.nit}   function evaluations = {r.nfev}   "
        f"max |projected gradient| = {np.abs(pg).max():.2e}")
    at = [PO[i] for i in range(6) if at_lo[i] or at_hi[i]]
    say(f"  parameters at a bound: {', '.join(at) if at else 'none'}")
    say(f"  start   : {fmt(x0)}")
    say(f"  estimate: {fmt(x)}")
    say(f"  transfer half-life {hl(x[1]):.1f} d   retest half-life {hl(x[3]):.1f} d   "
        f"first-retest increment k_Ld*A_d = {x[2] * x[5]:.3f}")
    return r


def bootstrap(P, D, Y, w, x_hat, nboot, seed):
    path = os.path.join(OUT, "draws.npy")
    rng = np.random.default_rng(seed); n = P.shape[0]
    draws = np.full((nboot, 6), np.nan); info = []; t0 = time.time()
    for b in range(nboot):
        idx = rng.integers(0, n, n)              # same draw sequence as figures._bootstrap
        r = ff._fit(list(x_hat), P[idx], D[idx], Y[idx], w[idx], BOUNDS)
        info.append(dict(b=b, success=bool(r.success), nit=r.nit, wmse=r.fun,
                         message=str(r.message), **dict(zip(PO, r.x))))
        if r.success:
            draws[b] = r.x
        if (b + 1) % 20 == 0:
            print(f"    bootstrap {b + 1}/{nboot}  ({time.time() - t0:.0f} s)")
    np.save(path, draws)
    pd.DataFrame(info).to_csv(os.path.join(OUT, "bootstrap_info.csv"), index=False)
    return draws, pd.DataFrame(info)


def schedules():
    H, B, L, R = 547, 1094, 60, 7.0
    rem = B - L * R
    even = np.full(H, B / H)
    fl = np.zeros(H); fl[:L] = R; fl[L:] = rem / (H - L)
    bo = np.zeros(H); bo[:L] = R
    bd = int(round(rem / 2 / R))
    for s in (240, 420):
        bo[s:s + bd] = R
    bo[L:] *= rem / bo[L:].sum()
    return {"even": even, "load": fl, "boost": bo}


def steady(minutes, k_Lt, k_Ft):
    g = 1 - (1 - k_Lt) ** (np.asarray(minutes) / figs.MINUTES_PER_GAME)
    return 100 * g / (g + k_Ft)


def derived(x):
    p = dict(zip(PO, x)); out = {}
    for m in MINUTES:
        out[f"ss_{m}min"] = float(steady(m, p["k_Lt"], p["k_Ft"]))
    for lab, s in schedules().items():
        tr = 100 * figs._sim_transfer(s, p, 547) / p["A_t"]
        out[f"{lab}_end"], out[f"{lab}_avg"] = tr[-1], tr.mean()
    return out


# ---------------------------------------------------------------- report sections
def sec_table1(x, draws):
    header("TABLE 1 - estimates and 95% bootstrap intervals")
    ok = draws[~np.isnan(draws).any(axis=1)]
    say(f"  bootstrap samples used: {len(ok)} of {len(draws)}")
    say(f"  {'param':6s} {'estimate':>12s} {'2.5%':>12s} {'97.5%':>12s}   half-life (days)")
    for i, k in enumerate(PO):
        lo, hi = np.percentile(ok[:, i], [2.5, 97.5])
        h = f"{hl(x[i]):.0f} ({hl(hi):.0f}-{hl(lo):.0f})" if k.startswith("k_F") else ""
        say(f"  {k:6s} {x[i]:12.5g} {lo:12.5g} {hi:12.5g}   {h}")
    say(f"  draws at a bound (any parameter): "
        f"{int(sum(any(d[i] - lo < 1e-8 or hi - d[i] < 1e-8 for i, (lo, hi) in enumerate(BOUNDS)) for d in ok))}")
    say(f"  draws with k_Ft > {FAST_KFT}: {int((ok[:, 1] > FAST_KFT).sum())}")


def sec_results_numbers(x, df):
    header("RESULTS-TEXT NUMBERS at the estimate")
    p = dict(zip(PO, x))
    k_Lt, k_Ft, k_Ld, k_Fd, A_t, A_d = x
    for frac in (0.5, 0.75, 0.8):
        gms = figs._games_for_transfer_frac(p, frac, 90)
        say(f"  {int(frac * 100)}% of transfer ceiling over 90 days: {gms:.0f} gameplays = "
            f"{gms * figs.MINUTES_PER_GAME / 60:.1f} h")
    mean_d = float(df.loc[df["nth_test"] == 2, "days_interval"].mean())
    sd0, st0 = ff.advance_interval(0, 0, mean_d, 0, k_Ld, k_Fd, k_Lt, k_Ft, A_d, A_t)
    say(f"  Fig 4: predicted change at the mean first interval ({mean_d:.0f} d) with no training {sd0 + st0:.2f}; "
        f"asymptote with extensive training {sd0 + A_t:.2f}")
    for D in (1, 365):
        sd, st = ff.advance_interval(0, 0, D, 440, k_Ld, k_Fd, k_Lt, k_Ft, A_d, A_t)
        say(f"  Fig 5: 22 h (440 gameplays) over {D:3d} d -> total {sd + st:.2f} "
            f"(retest {sd:.2f}, transfer {st:.2f})")
    for lab, s in schedules().items():
        tr = 100 * figs._sim_transfer(s, p, 547) / A_t
        extra = ""
        if lab == "load":
            extra = f"   day 60 {tr[60]:.0f}%"
        if lab == "boost":
            extra = f"   day 240 {tr[240]:.0f}%   max in second booster {tr[421:469].max():.0f}%"
        say(f"  {NAMES[lab]:28s} endpoint {tr[-1]:.0f}%   average {tr.mean():.0f}%{extra}")


def sec_derived(x, draws):
    header("MAINTENANCE AND SCHEDULES - joint bootstrap (Supplementary Table 2)")
    ok = draws[~np.isnan(draws).any(axis=1)]
    pt = derived(x); tab = pd.DataFrame([derived(d) for d in ok])
    tab.to_csv(os.path.join(OUT, "derived_per_draw.csv"), index=False)
    for c in tab.columns:
        lo, hi = np.percentile(tab[c], [2.5, 97.5])
        say(f"  {c:12s} {pt[c]:6.0f}   95% {lo:.0f}-{hi:.0f}")
    la = (tab.load_avg > tab[["even_avg", "boost_avg"]].max(axis=1)).mean()
    ee = (tab.even_end > tab[["load_end", "boost_end"]].max(axis=1)).mean()
    say(f"  {NAMES['load']} highest average in {100 * la:.0f}% of samples")
    say(f"  {NAMES['even']} highest endpoint in {100 * ee:.0f}% of samples")
    return tab


def sec_data_checks(df, uids, x, uid_prefix):
    header("DATA CHECKS - Hedges' g, short intervals, retest group")
    t2 = df[df["nth_test"] == 2].copy()
    t2["days"] = t2["days_interval"].round()
    comp = t2["user_id"].astype(str).str.startswith(uid_prefix)
    short = (t2["days"] >= 1) & (t2["days"] <= 69)
    say(f"  first intervals of 1-69 days: {int(short.sum()):,} ({100 * short.mean():.2f}%)   "
        f"composite {int((short & comp).sum()):,}, Grand Index {int((short & ~comp).sum()):,}")
    say(f"  same-day first intervals: {int((t2['days'] == 0).sum()):,}   "
        f"(composite {int(((t2['days'] == 0) & comp).sum()):,})")

    def hedges(a, b):
        na, nb = len(a), len(b)
        sp = np.sqrt(((na - 1) * a.var() + (nb - 1) * b.var()) / (na + nb - 2))
        gv = (1 - 3 / (4 * (na + nb) - 9)) * (b.mean() - a.mean()) / sp
        se = np.sqrt((na + nb) / (na * nb) + gv ** 2 / (2 * (na + nb)))
        return gv, gv - 1.96 * se, gv + 1.96 * se
    for lab, sub in (("pooled", t2), ("Grand Index only", t2[~comp])):
        lo = sub.loc[sub["plays_interval"] <= 50, "score_delta"]
        hi = sub.loc[sub["plays_interval"] >= 501, "score_delta"]
        g, gl, gh = hedges(lo, hi)
        say(f"  {lab:17s} <=50: n={len(lo):,} mean {lo.mean():.3f}   >=501: n={len(hi):,} "
            f"mean {hi.mean():.3f}   diff {hi.mean() - lo.mean():.2f}   "
            f"Hedges' g {g:.3f} (95% CI {gl:.3f}-{gh:.3f})")

    k_Lt, k_Ft, k_Ld, k_Fd, A_t, A_d = x
    low = t2[t2["plays_interval"] <= 25]
    sd = [ff.advance_interval(0, 0, max(d, 1.0), p, k_Ld, k_Fd, k_Lt, k_Ft, A_d, A_t)
          for d, p in zip(low["days_interval"], low["plays_interval"])]
    sd = np.array(sd)
    say(f"  <=25 gameplays T1->T2: n={len(low):,}  observed mean {low['score_delta'].mean():.2f}  "
        f"interval median {low['days_interval'].median():.0f} d, mean {low['days_interval'].mean():.0f} d")
    say(f"    predicted, averaged over own intervals: retest {sd[:, 0].mean():.2f}, "
        f"total {sd.sum(axis=1).mean():.2f}")


def fig_calibration(tab, path):
    lo, hi = tab.obs - 1.96 * tab["sem"], tab.obs + 1.96 * tab["sem"]
    fig, ax = plt.subplots(figsize=(6.5, 6))
    lim = [min(tab.pred.min(), lo.min()) - .3, max(tab.pred.max(), hi.max()) + .3]
    ax.plot(lim, lim, "k--", lw=1.2, label="Predicted = observed")
    ax.errorbar(tab.pred, tab.obs, yerr=[tab.obs - lo, hi - tab.obs], fmt="o",
                color=figs.CORAL, capsize=4, ms=7, label="Held-out decile mean (95% CI)")
    ax.set_xlim(lim); ax.set_ylim(lim); ax.grid(alpha=.3); ax.legend(loc="upper left")
    ax.set_xlabel("Predicted change at second administration (points)")
    ax.set_ylabel("Observed change (points)")
    fig.tight_layout(); fig.savefig(path, dpi=ff.CONFIG["dpi"], bbox_inches="tight"); plt.close(fig)


def sec_cv(P, D, Y, w, x_hat, k=5, seed=0):
    header("5-FOLD CROSS-VALIDATION (held-out group means, second administration)")
    rng = np.random.default_rng(seed); fold = rng.integers(0, k, P.shape[0])
    pr = np.full(P.shape[0], np.nan); kft = []
    for fi in range(k):
        tr, te = fold != fi, fold == fi
        r = ff._fit(list(x_hat), P[tr], D[tr], Y[tr], w[tr], BOUNDS)
        kft.append(r.x[1]); pr[te] = ff.simulate_matrix(P[te], D[te], r.x)[:, 0]
    ac = Y[:, 0]; ok = np.isfinite(pr) & np.isfinite(ac)
    t = pd.DataFrame(dict(pred=pr[ok], obs=ac[ok]))
    t["decile"] = pd.qcut(t["pred"], 10, labels=False, duplicates="drop")
    tab = t.groupby("decile").agg(n=("obs", "size"), pred=("pred", "mean"), obs=("obs", "mean"),
                                  sem=("obs", "sem"))
    tab.to_csv(os.path.join(OUT, "cv_deciles.csv"))
    say("  decile      n    predicted   observed (95% CI)")
    for d, r in tab.iterrows():
        n, p, o, s = r["n"], r["pred"], r["obs"], r["sem"]
        say(f"  {int(d):6d} {n:7,.0f}   {p:8.2f}   {o:6.2f} ({o - 1.96 * s:.2f}-{o + 1.96 * s:.2f})")
    say(f"  max |observed - predicted| across deciles: {np.abs(tab.obs - tab.pred).max():.2f} points")
    say("  fold k_Ft: " + ", ".join(f"{v:.3g}" for v in kft))
    os.makedirs(os.path.join(OUT, "fig_supp"), exist_ok=True)
    fig_calibration(tab, os.path.join(OUT, "fig_supp", "figS_calibration.png"))
    say("  calibration figure: fig_supp/figS_calibration.png (from these deciles)")
    return tab


def fig_maintenance_joint(draws, x, path):
    ok = draws[~np.isnan(draws).any(axis=1)]
    mins = np.linspace(0.05, 18, 300)
    J = np.array([steady(mins, d[0], d[1]) for d in ok])
    lo, hi = np.percentile(J, [2.5, 97.5], axis=0)
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.fill_between(mins, lo, hi, color=figs.TEAL, alpha=.30, label="95% interval (bootstrap)")
    ax.plot(mins, steady(mins, x[0], x[1]), color=figs.INK, lw=2.4, label="Estimate")
    ax.set_xlabel("Daily cognitive training (minutes)")
    ax.set_ylabel("Steady-state transfer (% of ceiling)")
    ax.set_xlim(0, 18); ax.set_ylim(0, 102); ax.grid(alpha=.3); ax.legend(loc="lower right")
    fig.tight_layout(); fig.savefig(path, dpi=ff.CONFIG["dpi"], bbox_inches="tight"); plt.close(fig)


def fig_supp_uncertainty(draws, x, tab, path):
    ok = draws[~np.isnan(draws).any(axis=1)]
    mins = np.linspace(0.05, 18, 300)
    J = np.array([steady(mins, d[0], d[1]) for d in ok])
    lo, hi = np.percentile(J, [2.5, 97.5], axis=0)
    pt = derived(x)
    fig, (a0, a1) = plt.subplots(1, 2, figsize=(13, 5.2))
    a0.fill_between(mins, lo, hi, color=figs.TEAL, alpha=.30, label="95% interval (bootstrap)")
    a0.plot(mins, steady(mins, x[0], x[1]), color=figs.INK, lw=2.4, label="Estimate")
    a0.set_xlabel("Daily cognitive training (minutes)")
    a0.set_ylabel("Steady-state transfer (% of ceiling)")
    a0.set_xlim(0, 18); a0.set_ylim(0, 102); a0.grid(alpha=.3); a0.legend(loc="lower right")
    xs = np.arange(3); keys = ("even", "load", "boost")
    for crit, off, col, lab in (("end", -.16, figs.PURPLE, "18-month endpoint"),
                                ("avg", .16, figs.CORAL, "18-month average")):
        pts = np.array([pt[f"{k}_{crit}"] for k in keys])
        l = np.array([np.percentile(tab[f"{k}_{crit}"], 2.5) for k in keys])
        h = np.array([np.percentile(tab[f"{k}_{crit}"], 97.5) for k in keys])
        a1.errorbar(xs + off, pts, yerr=[pts - l, h - pts], fmt="o", ms=7, capsize=5, lw=2,
                    color=col, label=lab)
    a1.set_xticks(xs); a1.set_xticklabels([NAMES[k] for k in keys], fontsize=9)
    a1.set_ylabel("Transfer (% of ceiling)"); a1.set_ylim(0, 102); a1.grid(alpha=.3); a1.legend()
    fig.tight_layout(); fig.savefig(path, dpi=ff.CONFIG["dpi"], bbox_inches="tight"); plt.close(fig)


def make_figures(df, x, P, D, Y, w, draws, tab, nboot):
    main_dir, supp_dir = os.path.join(OUT, "fig_main"), os.path.join(OUT, "fig_supp")
    os.makedirs(main_dir, exist_ok=True); os.makedirs(supp_dir, exist_ok=True)
    params = dict(zip(PO, x))
    orig = figs._bootstrap
    figs._bootstrap = lambda *a, **k: draws        # make_all reuses the v17 draws
    try:
        man, _ = figs.make_all(df, params, P, D, Y, w, main_dir, supp_dir,
                               nboot=nboot, seed=7, max_test=5)
    finally:
        figs._bootstrap = orig
    fig_maintenance_joint(draws, x, os.path.join(main_dir, "fig_maintenance.png"))
    fig_supp_uncertainty(draws, x, tab, os.path.join(supp_dir, "figS4_uncertainty.png"))
    header("FIGURE MANIFEST")
    for name, status in man:
        say(f"  {status[:40]:40s} {name}")
    say("  fig_main/fig_maintenance.png overwritten with the joint-bootstrap band (Fig. 7)")
    say("  fig_supp/figS4_uncertainty.png written (Supplementary Fig. 4)")
    say("  removed in v17: loss landscape, k_Ft profile, engine calibration (replaced by figS_calibration)")


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data/newsubset.csv")
    ap.add_argument("--composite", "--nicole", dest="composite", default="data/short_intervals.csv")
    ap.add_argument("--min-valid-subtests", type=int, default=3)
    ap.add_argument("--uid-prefix", default="NIC_")
    ap.add_argument("--nboot", type=int, default=200)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--rebuild", action="store_true")
    ap.add_argument("--skip-figures", action="store_true")
    ap.add_argument("--force", action="store_true", help="continue even if k_Ft > 0.1")
    args = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    t_start = time.time()

    # in-memory overrides: one start, one bound set, everywhere
    x0 = osman_start()
    ff.CONFIG["x0_smart"] = x0
    ff.CONFIG["bounds_unconstrained"] = BOUNDS
    ff.CONFIG["A_d_ceiling"] = 30.0
    ff.CONFIG["k_Ft_lower_bound_tc"] = 1e-6
    ff.CONFIG["maxiter"] = 10_000

    say(f"# run_v17.py - {time.strftime('%Y-%m-%d %H:%M')}")
    import scipy
    try:
        c = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], text=True).strip()
        dirty = subprocess.check_output(["git", "status", "--porcelain", "--untracked-files=no"], text=True).strip()
    except Exception:
        c, dirty = "unavailable", ""
    say(f"  Python {sys.version.split()[0]}  NumPy {np.__version__}  SciPy {scipy.__version__}  "
        f"pandas {pd.__version__}  matplotlib {matplotlib.__version__}")
    say(f"  git {c}{' (uncommitted changes present)' if dirty else ''}")
    say(f"  bounds: rates [1e-6, 0.99], ceilings [0, 30]   maxiter {ff.CONFIG['maxiter']}  "
        f"ftol {ff.CONFIG['ftol']}  gtol {ff.CONFIG['gtol']}")
    say(f"  Osman-anchored start: {fmt(x0)}")

    newsub, merged = db.build_merged_once(args)
    df, uids, P, D, Y, w = prepare(merged)
    r = fit_and_check(P, D, Y, w, x0, "MAIN (pooled, T1-T5)")
    x = np.asarray(r.x)
    say(f"  relative change vs 13 Sept estimate: " +
        "  ".join(f"{k} {100 * (a / b - 1):+.1f}%" for k, a, b in zip(PO, x, SEPT13)))

    if x[1] > FAST_KFT and not args.force:
        say(f"\n  !! k_Ft = {x[1]:.3g} > {FAST_KFT}: the Osman-anchored start reached the fast basin.")
        say("     Stopping before the bootstrap; rerun with --force to continue.")
        sys.exit(2)

    sec_results_numbers(x, df)
    sec_data_checks(df, uids, x, args.uid_prefix)

    header(f"BOOTSTRAP ({args.nboot} resamples, start = point estimate)")
    draws, info = bootstrap(P, D, Y, w, x, args.nboot, args.seed)
    say(f"  converged: {int(info.success.sum())} of {len(info)}")
    for _, row in info[~info.success].iterrows():
        say(f"    sample {row.b}: nit {row.nit}, message: {row.message}")
    sec_table1(x, draws)
    tab = sec_derived(x, draws)

    sec_cv(P, D, Y, w, x)

    df_gi, _, Pg, Dg, Yg, wg = prepare(newsub)
    fit_and_check(Pg, Dg, Yg, wg, x0, "GRAND INDEX ONLY (Supplementary Table 3)")

    if not args.skip_figures:
        make_figures(df, x, P, D, Y, w, draws, tab, args.nboot)

    say(f"\n  done in {(time.time() - t_start) / 60:.0f} min.  report: {OUT}/report.md")


if __name__ == "__main__":
    main()
