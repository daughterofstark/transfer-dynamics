"""
paper_additions.py
==================================================================
Drop-in additions for the Four-Forces paper. Imports the UNCHANGED engine from
transfer_model.py (as `ff`) and adds the analyses flagged in review:

  1. plot_booster_schedules(params)        -> booster_schedules.png   (NEW FIGURE)
  2. fit_static_baseline(P,D,Y,w,params)   -> static-vs-dynamic AIC    (BENCHMARK)
  3. plot_timing_decomposition(params)     -> timing_decomposition.png (DEFENDS Fig 4)
  4. check_rtm_by_dose(df)                  -> RTM balance table        (RTM hole)
  5. plot_saturation_crossover(df,params)  -> saturation_crossover.png (CROSS-FIND #2)
  6. winsorize_sensitivity(args_data)       -> A_t / split under capping (ROBUSTNESS)

Call them from transfer_model.main() right after the standard figures, e.g.:

    import paper_additions as add
    add.plot_booster_schedules(params)
    add.fit_static_baseline(P, D, Y, w, params)
    add.plot_timing_decomposition(params)
    add.check_rtm_by_dose(df)
    add.plot_saturation_crossover(df, params)
    # add.winsorize_sensitivity(CONFIG["data_file"])   # optional, re-fits

Usage standalone (figures that need only params, not the CSV):
    python paper_additions.py            # renders booster + timing-decomp figures
"""
from __future__ import annotations
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from scipy.optimize import minimize

import transfer_model as ff   # the engine; NOT modified

SAVE = ff.CONFIG["save_dir"]
DPI  = ff.CONFIG["dpi"]
PO   = ff.PARAM_ORDER         # ["k_Lt","k_Ft","k_Ld","k_Fd","A_t","A_d"]


# ════════════════════════════════════════════════════════════════════════════
# 1. BOOSTER / GAP / RE-ENGAGEMENT FIGURE   (the abstract promised this)
# ════════════════════════════════════════════════════════════════════════════
def plot_booster_schedules(params, horizon_days=540,
                           kFt_draw=None, kFt_slow=None):
    """Five realistic home-play schedules through the daily engine (ST only;
    home play confers no test familiarity, so SD=0 — consistent with viz3).

    Forgetting is drawn at a CONSERVATIVE 1-yr half-life by default so gaps and
    boosters are visible; a faint slower-rate overlay makes the assumption-
    dependence explicit (k_Ft is unidentified; see viz9)."""
    N = horizon_days
    kFt_draw = np.log(2) / 365.0 if kFt_draw is None else kFt_draw   # 1-yr HL
    kFt_slow = ff.CONFIG["k_Ft_lower_bound_tc"] if kFt_slow is None else kFt_slow

    p      = dict(params); p["k_Ft"]      = kFt_draw
    p_slow = dict(params); p_slow["k_Ft"] = kFt_slow

    def consistent(rate):     return np.full(N, rate)
    def intermittent(rate):                                  # 3 days/week
        v = np.zeros(N)
        for t in range(N):
            if (t % 7) in (0, 2, 4): v[t] = rate
        return v
    def front_stop(load=60, rate=10.0):
        v = np.zeros(N); v[:load] = rate; return v
    def front_boost(load=60, rate=10.0, blen=14, starts=(180, 360)):
        v = front_stop(load, rate)
        for s in starts: v[s:s + blen] = rate
        return v
    def resume_gap(load=60, rate=10.0, resume=365, rrate=2.0):
        v = np.zeros(N); v[:load] = rate; v[resume:] = rrate; return v

    scheds = [
        ("Consistent (1.3 g/day)",            consistent(1.3),  "#2a9d8f"),
        ("Intermittent (3 d/wk, 3 g/day)",    intermittent(3.0), "#8ab17d"),
        ("Front-load 60d, then stop",         front_stop(),     "#e9c46a"),
        ("Front-load + boosters (mo 6 & 12)", front_boost(),    "#e76f51"),
        ("Resume 2 g/day after 10-mo gap",    resume_gap(),     "#9b5de5"),
    ]

    days = np.arange(N)
    fig = plt.figure(figsize=(13.5, 8.2))
    ax  = fig.add_axes([0.07, 0.34, 0.84, 0.58])
    axg = fig.add_axes([0.07, 0.07, 0.84, 0.21])

    print(f"\n  BOOSTER SCHEDULES (k_Ft draw = {kFt_draw:.5f}, "
          f"HL={ff.half_life(kFt_draw):.0f} d)")
    print(f"  {'Schedule':36s} {'Games':>6} {'PeakST':>7} {'EndST':>7} {'AUC':>8}")
    for label, vec, color in scheds:
        _, hST = ff.simulate_vector(vec, p, assessment_days=None)
        auc = float(np.sum(hST))
        ax.plot(days, hST, color=color, lw=2.4, label=label)
        ax.annotate(f"{hST[-1]:.2f}", (N - 1, hST[-1]), (N + 4, hST[-1]),
                    fontsize=8, color=color, va="center")
        print(f"  {label:36s} {vec.sum():>6.0f} {hST.max():>7.2f} "
              f"{hST[-1]:>7.2f} {auc:>8.0f}")

    _, hslow = ff.simulate_vector(front_stop(), p_slow, assessment_days=None)
    ax.plot(days, hslow, color="#e9c46a", lw=1.3, ls=":", alpha=0.9,
            label=f"(front-load+stop at slower {ff.half_life(kFt_slow)/365:.1f}-yr HL)")

    ax.axhline(params["A_t"], color="gray", ls="--", lw=1, alpha=0.7)
    ax.annotate(f"A_t = {params['A_t']:.2f}", (8, params["A_t"]),
                (8, params["A_t"] + 0.06), fontsize=8, color="gray")
    ax.set_title("Booster / Gap / Re-engagement Schedules — Transfer Skill (ST)\n"
                 "Home play confers no test familiarity (SD\u22610); forgetting at the "
                 "conservative 1-yr half-life (assumed, not measured \u2014 see viz9)",
                 fontsize=11, fontweight="bold")
    ax.set_ylabel("Predicted transfer \u0394 from baseline (ST)")
    ax.set_xlim(0, N + 28); ax.set_ylim(0, params["A_t"] * 1.08)
    ax.xaxis.set_major_locator(mticker.MultipleLocator(30)); ax.tick_params(labelbottom=False)
    ax.legend(fontsize=8, loc="lower right"); ax.grid(alpha=0.3)
    axm = ax.twiny(); axm.set_xlim(ax.get_xlim())
    axm.set_xticks([30 * m for m in range(0, 19, 2)])
    axm.set_xticklabels([f"M{m}" for m in range(0, 19, 2)], fontsize=8)
    axm.set_xlabel("Month", fontsize=9)
    for label, vec, color in scheds:
        axg.plot(days, np.convolve(vec, np.ones(7) / 7, mode="same"),
                 color=color, lw=1.4, alpha=0.85)
    axg.set_xlim(0, N + 28); axg.set_ylim(bottom=0)
    axg.set_xlabel("Day of trial"); axg.set_ylabel("Games/day\n(7-day avg)", fontsize=9)
    axg.xaxis.set_major_locator(mticker.MultipleLocator(30)); axg.grid(alpha=0.3)
    axg.text(0.5, 0.93, "Model-implied (dose self-selected, not experimental). "
             "Gap-decay & booster-recovery magnitudes scale with assumed k_Ft.",
             transform=axg.transAxes, fontsize=7.5, ha="center", va="top",
             bbox=dict(boxstyle="round", facecolor="#fff3cd", alpha=0.85))
    path = f"{SAVE}/booster_schedules.png"
    plt.savefig(path, dpi=DPI, bbox_inches="tight"); plt.close()
    print(f"  Saved: {path}")


# ════════════════════════════════════════════════════════════════════════════
# 2. STATIC CUMULATIVE-DOSE BASELINE  (does calendar-time structure earn its keep?)
# ════════════════════════════════════════════════════════════════════════════
def _static_predict(P, D, x):
    """Osman-style STATIC model: ignores days entirely.
       ST = A_t*(1-(1-k_Lt)^cumulative_plays);  no transfer decay, no density.
       SD = A_d*(1-(1-k_Ld)^test_count);        no familiarity decay.
       x = [k_Lt, A_t, k_Ld, A_d]  (4 params vs the dynamic model's 5 free)."""
    k_Lt, A_t, k_Ld, A_d = x
    valid = ~np.isnan(P)
    Pf  = np.where(valid, P, 0.0)
    cum = np.cumsum(Pf, axis=1)                       # cumulative games by interval
    ST  = A_t * (1.0 - (1.0 - k_Lt) ** cum)
    k   = np.arange(1, P.shape[1] + 1)[None, :]       # NCPT sittings by interval end
    SD  = A_d * (1.0 - (1.0 - k_Ld) ** k)
    return np.where(valid, SD + ST, np.nan)


def _static_wmse(x, P, D, Y, w):
    pred = _static_predict(P, D, x)
    valid = ~np.isnan(Y)
    se = np.where(valid, (Y - pred) ** 2, 0.0)
    per_user = se.sum(1) / np.maximum(valid.sum(1), 1)
    return float((w * per_user).sum() / max(w.sum(), 1e-12))


def fit_static_baseline(P, D, Y, w, dyn_params):
    """Fit the static model, compare WMSE and an approximate AIC to the dynamic
    fit. The dynamic model has 5 free params (k_Ft fixed); static has 4."""
    print(f"\n{'═'*62}\n  STATIC CUMULATIVE-DOSE BASELINE  (does timing earn its keep?)\n{'═'*62}")
    b = [(1e-6, 0.99), (0.0, 30.0), (1e-6, 0.99), (0.0, 100.0)]
    best = None
    for s in ([0.005, 3.5, 0.2, 8.0], [0.02, 4.0, 0.5, 5.0], [0.001, 6.0, 0.1, 12.0]):
        r = minimize(_static_wmse, s, args=(P, D, Y, w), method="L-BFGS-B",
                     bounds=b, options={"maxiter": 5000, "ftol": 1e-12})
        if best is None or r.fun < best.fun:
            best = r
    wmse_static = float(best.fun)
    # dynamic WMSE on the same matrices
    x_dyn = [dyn_params[k] for k in PO]
    wmse_dyn = ff.wmse_matrix(x_dyn, P, D, Y, w)

    # approximate AIC from unweighted SSE (Gaussian): AIC = Nobs*ln(SSE/Nobs)+2k
    def sse(pred):
        v = ~np.isnan(Y); return float(np.nansum((Y - pred) ** 2)), int(v.sum())
    sse_s, nobs = sse(_static_predict(P, D, best.x))
    sse_d, _    = sse(ff.simulate_matrix(P, D, x_dyn))
    aic_s = nobs * np.log(sse_s / nobs) + 2 * 4
    aic_d = nobs * np.log(sse_d / nobs) + 2 * 5
    print(f"  static  : k_Lt={best.x[0]:.5f} A_t={best.x[1]:.3f} "
          f"k_Ld={best.x[2]:.4f} A_d={best.x[3]:.2f}")
    print(f"  WMSE  static={wmse_static:.4f}   dynamic={wmse_dyn:.4f}   "
          f"Δ={wmse_static - wmse_dyn:+.4f}")
    print(f"  AIC   static={aic_s:.1f}   dynamic={aic_d:.1f}   "
          f"ΔAIC(static−dynamic)={aic_s - aic_d:+.1f}  "
          f"({'dynamic wins' if aic_d < aic_s else 'static wins'})")
    return dict(wmse_static=wmse_static, wmse_dyn=wmse_dyn, aic_static=aic_s, aic_dyn=aic_d)


# ════════════════════════════════════════════════════════════════════════════
# 3. TIMING DECOMPOSITION  (how much of the Fig-4 timing effect is IDENTIFIED?)
# ════════════════════════════════════════════════════════════════════════════
def plot_timing_decomposition(params, dose=500.0, day_grid=None):
    """At a FIXED total dose, vary the T1→T2 interval and decompose the observable
    timing effect BY CHANNEL.

    KEY ALGEBRAIC FACT: with k_Ft=0 the transfer closed form reduces to
    ST = A_t·(1-(1-k_Lt)^P) — a function of TOTAL GAMES ONLY; interval length D
    cancels. So the transfer pathway has NO within-interval density/timing effect.
    The transfer pathway's entire interval-dependence is decay, governed by the
    UNIDENTIFIED k_Ft. Only the familiarity channel's timing effect (k_Fd) is
    (partially) identified. This figure makes that split explicit, so Fig 4's
    'timing modifies dose-response' is reported honestly per channel."""
    if day_grid is None:
        day_grid = np.linspace(20, 540, 60)
    p = params

    def split(D, kFt, kFd):
        SD, ST = ff.advance_interval(0.0, 0.0, float(D), float(dose),
                                     p["k_Ld"], kFd, p["k_Lt"], kFt,
                                     p["A_d"], p["A_t"])
        return SD, ST

    # transfer channel under three forgetting assumptions
    st_zero = np.array([split(D, 0.0, p["k_Fd"])[1] for D in day_grid])           # flat
    st_tc   = np.array([split(D, ff.CONFIG["k_Ft_lower_bound_tc"], p["k_Fd"])[1]
                        for D in day_grid])
    st_aggr = np.array([split(D, np.log(2) / 182.0, p["k_Fd"])[1] for D in day_grid])
    # familiarity channel under its (more identified) decay rate
    sd_tc   = np.array([split(D, ff.CONFIG["k_Ft_lower_bound_tc"], p["k_Fd"])[0]
                        for D in day_grid])

    fig, (axT, axD) = plt.subplots(1, 2, figsize=(13.5, 5.4))

    axT.plot(day_grid, st_zero, color="#264653", lw=2.4,
             label="k_Ft = 0  → flat: NO density/timing effect on transfer")
    axT.plot(day_grid, st_tc, color="#2a9d8f", lw=2.2, ls="--",
             label="k_Ft conservative (1.9-yr HL)")
    axT.plot(day_grid, st_aggr, color="#e76f51", lw=2.2, ls=":",
             label="k_Ft aggressive (6-mo HL)")
    axT.fill_between(day_grid, st_aggr, st_zero, color="#e76f51", alpha=0.10)
    axT.set_xlabel(f"T1→T2 interval (days), dose fixed at {dose:.0f} games")
    axT.set_ylabel("Transfer (ST) at T2")
    axT.set_title("TRANSFER channel — timing effect is ENTIRELY k_Ft\n"
                  "(unidentified): the flat line proves density is irrelevant",
                  fontsize=10, fontweight="bold")
    axT.legend(fontsize=8); axT.grid(alpha=0.3)

    axD.plot(day_grid, sd_tc, color="#6a4c93", lw=2.4,
             label=f"familiarity decay k_Fd={p['k_Fd']:.4f} (partially identified)")
    axD.set_xlabel(f"T1→T2 interval (days), dose fixed at {dose:.0f} games")
    axD.set_ylabel("Familiarity (SD) at T2")
    axD.set_title("FAMILIARITY channel — timing effect is k_Fd\n"
                  "(the defensible part of 'timing modifies dose-response')",
                  fontsize=10, fontweight="bold")
    axD.legend(fontsize=8); axD.grid(alpha=0.3)

    fig.suptitle("Decomposing the timing-modifies-dose effect by channel — "
                 "transfer's interval-sensitivity is an assumption, familiarity's is estimated",
                 fontsize=11, fontweight="bold")
    path = f"{SAVE}/timing_decomposition.png"
    plt.tight_layout(); plt.savefig(path, dpi=DPI, bbox_inches="tight"); plt.close()
    print(f"\n  TIMING DECOMPOSITION (by channel):")
    print(f"    transfer spread at k_Ft=0           : {st_zero.max()-st_zero.min():.4f}  (≈0 by construction)")
    print(f"    transfer spread at conservative k_Ft: {st_tc.max()-st_tc.min():.4f}  (assumption-driven)")
    print(f"    familiarity spread at k_Fd          : {sd_tc.max()-sd_tc.min():.4f}  (identified-ish)")
    print(f"  Saved: {path}")


# ════════════════════════════════════════════════════════════════════════════
# 4. REGRESSION-TO-THE-MEAN BALANCE ACROSS DOSE  (the differencing-out hole)
# ════════════════════════════════════════════════════════════════════════════
def check_rtm_by_dose(df):
    """RTM 'differences out' of the transfer estimate ONLY if T1 baseline is
    balanced across dose cohorts. Report mean T1 and within-cohort corr(T1,ΔT2)
    per cohort so the assumption is checkable rather than asserted."""
    print(f"\n{'═'*62}\n  RTM BALANCE ACROSS DOSE COHORTS\n{'═'*62}")
    t2 = df[df["nth_test"] == 2].copy()
    edges  = ff.CONFIG["play_bin_edges"]
    labels = ff.CONFIG["play_bin_labels"]
    t2["dose_bin"] = pd.cut(t2["plays_interval"], bins=edges, labels=labels)
    print(f"  {'Dose bin':10s} {'n':>6} {'meanT1':>8} {'sdT1':>7} "
          f"{'meanΔT2':>8} {'corr(T1,ΔT2)':>13}")
    rows = []
    for lab in labels:
        g = t2[t2["dose_bin"] == lab]
        if len(g) < 5: continue
        c = np.corrcoef(g["t1_score"], g["score_delta"])[0, 1]
        print(f"  {lab:10s} {len(g):>6,} {g['t1_score'].mean():>8.1f} "
              f"{g['t1_score'].std():>7.1f} {g['score_delta'].mean():>8.2f} {c:>13.3f}")
        rows.append((lab, g["t1_score"].mean()))
    if len(rows) >= 2:
        spread = max(r[1] for r in rows) - min(r[1] for r in rows)
        print(f"  → T1 baseline spread across dose bins = {spread:.1f} points.")
        print(f"    Small spread ⇒ RTM affects dose groups similarly ⇒ it largely")
        print(f"    differences out of the transfer (between-group) estimate.")
        print(f"    Large spread ⇒ covariate-adjust T1 before quoting transfer.")


# ════════════════════════════════════════════════════════════════════════════
# 5. SATURATION / CROSSOVER FIGURE  (cross-finding #2 had no figure)
# ════════════════════════════════════════════════════════════════════════════
def plot_saturation_crossover(df, params):
    """Per cohort, walk the model test-by-test under the cohort's own median
    intervals and plot transfer as % of A_t (saturation) and the SD-vs-ST
    crossover (familiarity overtaking transfer is driven by RE-TESTING)."""
    print(f"\n{'═'*62}\n  SATURATION / CROSSOVER (transfer saturates early)\n{'═'*62}")
    p = params; mt = ff.CONFIG["max_test"]
    cohorts = ff.CONFIG["cohort_scheme"]
    fig, (axL, axR) = plt.subplots(1, 2, figsize=(13.5, 5.4))
    for (lab, lo, hi, desc, color) in cohorts:
        hi_v = hi if hi is not None else 10**9
        ids = df[(df["nth_test"] == 2) &
                 (df["plays_interval"] >= lo) & (df["plays_interval"] <= hi_v)]["user_id"]
        sub = df[df["user_id"].isin(ids) & (df["nth_test"] > 1)]
        if sub["user_id"].nunique() < 20: continue
        med_p = sub.groupby("nth_test")["plays_interval"].median()
        med_d = sub.groupby("nth_test")["days_interval"].median()
        SD = ST = 0.0; tests, satur, sd_hist, st_hist = [], [], [], []
        for nth in sorted(med_p.index):
            if nth > mt: break
            SD, ST = ff.advance_interval(SD, ST, max(float(med_d[nth]), 1.0),
                                         float(med_p[nth]), p["k_Ld"], p["k_Fd"],
                                         p["k_Lt"], p["k_Ft"], p["A_d"], p["A_t"])
            tests.append(nth); satur.append(100 * ST / p["A_t"])
            sd_hist.append(SD); st_hist.append(ST)
        axL.plot(tests, satur, "o-", color=color, lw=2, label=desc)
        axR.plot(tests, sd_hist, "s--", color=color, lw=1.6, alpha=0.8)
        axR.plot(tests, st_hist, "o-",  color=color, lw=2)
    axL.axhline(80, color="gray", ls=":", lw=1); axL.set_ylim(0, 105)
    axL.set_xlabel("Test number"); axL.set_ylabel("Transfer as % of A_t")
    axL.set_title("Transfer saturates early\n(heavy players ≈ ceiling by T2)",
                  fontsize=10.5, fontweight="bold")
    axL.legend(fontsize=8); axL.grid(alpha=0.3)
    axR.set_xlabel("Test number"); axR.set_ylabel("Score Δ (solid=ST transfer, dashed=SD direct)")
    axR.set_title("Direct vs transfer crossover\n(later climb = re-dosed familiarity)",
                  fontsize=10.5, fontweight="bold")
    axR.grid(alpha=0.3)
    path = f"{SAVE}/saturation_crossover.png"
    plt.tight_layout(); plt.savefig(path, dpi=DPI, bbox_inches="tight"); plt.close()
    print(f"  Saved: {path}")


# ════════════════════════════════════════════════════════════════════════════
# 6. WINSORIZE SENSITIVITY  (does dropping 33.7% of users move the headline?)
# ════════════════════════════════════════════════════════════════════════════
def winsorize_sensitivity(data_file):
    """Re-run prepare/fit with winsorize_outliers=True (cap offending intervals
    instead of dropping the user) and compare A_t + observable split."""
    print(f"\n{'═'*62}\n  WINSORIZE SENSITIVITY (cap vs drop outliers)\n{'═'*62}")
    out = {}
    for wins in (False, True):
        ff.CONFIG["winsorize_outliers"] = wins
        df = ff.prepare_data(data_file)
        pb, pl, db, dl = ff.plot_days_histogram_and_get_bins(df)
        uw, _ = ff.compute_user_weights(df, pb, pl, db, dl)
        _, P, D, Y, w, _ = ff.df_to_matrices(df, uw)
        params, _ = ff.run_optimization(P, D, Y, w)
        rep = ff.report_direct_identifiability(df, params, P, D, Y, w)
        out[wins] = (params["A_t"], rep["observable_direct_share"])
    ff.CONFIG["winsorize_outliers"] = False   # restore default
    print(f"\n  {'mode':8s} {'A_t':>7} {'obs. direct share':>18}")
    print(f"  {'drop':8s} {out[False][0]:>7.3f} {out[False][1]*100:>17.1f}%")
    print(f"  {'winsor':8s} {out[True][0]:>7.3f} {out[True][1]*100:>17.1f}%")


# pandas needed by check_rtm_by_dose
import pandas as pd


# ════════════════════════════════════════════════════════════════════════════
# SELF-CONTAINED INPUT BUILDER  (so this file runs standalone, no objects needed
# from a prior transfer_model run). Re-does the SAME data-prep + fit; with
# rng_seed=42 the params match the main run exactly.
# ════════════════════════════════════════════════════════════════════════════
def build_inputs(data_file):
    """Reproduce (df, params, P, D, Y, w) exactly as transfer_model.main() does."""
    import numpy as _np
    ff.CONFIG["data_file"] = data_file
    _np.random.seed(ff.CONFIG["rng_seed"])
    df = ff.prepare_data(data_file)
    pb, pl, db, dl = ff.plot_days_histogram_and_get_bins(df)
    user_weight, _ = ff.compute_user_weights(df, pb, pl, db, dl)
    uids, P, D, Y, w, t2_plays = ff.df_to_matrices(df, user_weight)
    params, _final = ff.run_optimization(P, D, Y, w)
    return df, params, P, D, Y, w


def main():
    import argparse
    ap = argparse.ArgumentParser(description="Paper additions (standalone).")
    ap.add_argument("--data", default=ff.CONFIG["data_file"],
                    help="CSV; if present, runs ALL additions. If omitted/missing, "
                         "renders only the two params-only figures off TC defaults.")
    ap.add_argument("--no-winsorize", action="store_true",
                    help="skip the winsorize sensitivity (it re-fits twice)")
    args = ap.parse_args()

    import os
    if args.data and os.path.exists(args.data):
        print(f"\n[paper_additions] full run on {args.data} "
              f"(re-fitting; params will match your main run)\n")
        df, params, P, D, Y, w = build_inputs(args.data)
        plot_booster_schedules(params)
        fit_static_baseline(P, D, Y, w, params)
        plot_timing_decomposition(params)
        check_rtm_by_dose(df)
        plot_saturation_crossover(df, params)
        if not args.no_winsorize:
            winsorize_sensitivity(args.data)
    else:
        print("\n[paper_additions] no CSV found — rendering params-only figures "
              "from TC defaults (booster + timing decomposition).\n")
        TC = dict(k_Lt=0.004777, k_Ft=0.001000, k_Ld=0.197363,
                  k_Fd=0.001407, A_t=3.4618, A_d=7.9809)
        plot_booster_schedules(TC)
        plot_timing_decomposition(TC)


if __name__ == "__main__":
    main()
