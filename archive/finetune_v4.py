"""
finetune_v4.py — two core-model fine-tunes, built on transfer_model.py (UNCHANGED).

  TASK 1  short-interval upweighting
    - report how many T1->T2 intervals are < 60 days and their day distribution
    - overwrite ONLY those users' weights with a large value (default 25), above the
      engine's 5x cap, leaving every standard-interval record untouched

  TASK 2  exclusion sweep judged on ALL SIX parameters
    - regimes ordered from "exclude least" upward: none -> winsorize plays@3000
      (asymptote-justified) -> winsorize plays@5000 (conservative)
    - the plays cap touches only the dose/ceiling side; the day limit is left loose
      because forgetting is driven by elapsed time
    - reports all six parameters, flags any that sit at a bound, and ranks the
      LEAST-STABLE parameters across regimes (the ones to actually watch)
    - runs each regime with short-interval boost OFF and ON

Run:
  python finetune_v4.py --data newsubset.csv                 # everything, T1-T3
  python finetune_v4.py --data newsubset.csv --short-days 60 --short-weight 25
  python finetune_v4.py --data newsubset.csv --report-only   # just Task-1 diagnostic
"""
from __future__ import annotations
import argparse, copy, os, tempfile
import numpy as np, pandas as pd

import transfer_model as ff
try:
    import paper_additions as add
    HAVE_ADD = True
except Exception:
    HAVE_ADD = False

PO = ff.PARAM_ORDER
DAY_EDGES, DAY_LBLS = [0., 90., 180., 9999.], ["D0-90", "D90-180", "D180+"]
HUGE = 10**9
A_D_CEIL = ff.CONFIG.get("A_d_ceiling", 100.0)
AT_BOUND = 30.0
KFT_FLOOR = ff.CONFIG.get("k_Ft_lower_bound_tc", 0.001)


def _truncated_csv(data, max_test):
    raw = pd.read_csv(data); raw.columns = [c.replace("\ufeff", "") for c in raw.columns]
    raw = raw[raw["nth_test"] <= max_test].copy()
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".csv").name
    raw.to_csv(tmp, index=False); return tmp


# ───────────────────────── TASK 1: report ─────────────────────────
def short_interval_report(df, short_days=60):
    t2 = df[df["nth_test"] == 2]
    d = t2["days_interval"].dropna()
    short = d[d < short_days]
    n, ns = len(d), len(short)
    print(f"\n{'='*68}\n  SHORT-INTERVAL DIAGNOSTIC  (T1->T2 < {short_days} days)\n{'='*68}")
    print(f"  T1->T2 records total          : {n:,}")
    print(f"  with interval < {short_days} days       : {ns:,}  ({100*ns/max(n,1):.2f}%)")
    if ns:
        q = short.quantile([0, .25, .5, .75, 1.0]).values
        print(f"  days in that group  min/Q1/med/Q3/max = "
              f"{q[0]:.0f} / {q[1]:.0f} / {q[2]:.0f} / {q[3]:.0f} / {q[4]:.0f}")
        edges = [0, 15, 30, 45, 60]
        h, _ = np.histogram(short, bins=edges)
        print("  histogram:")
        for i in range(len(h)):
            print(f"     {edges[i]:>2}-{edges[i+1]:<2} d : {h[i]:>4}")
    return ns


# ───────────────────────── TASK 1: weighting ─────────────────────────
def weights_with_shortboost(df, short_days, short_weight, boost):
    base, _ = ff.compute_user_weights(
        df, ff.CONFIG["play_bin_edges"], ff.CONFIG["play_bin_labels"], DAY_EDGES, DAY_LBLS)
    uw = dict(base)
    if not boost:
        return uw, 0, 0.0
    t2 = df[df["nth_test"] == 2]
    short = set(t2[t2["days_interval"] < short_days]["user_id"])
    for u in short:
        if u in uw:
            uw[u] = float(short_weight)
    total = sum(uw.values())
    short_mass = short_weight * sum(1 for u in short if u in base)
    return uw, len(short & set(base)), (short_mass / total if total else 0.0)


def flag_at_bounds(p):
    f = []
    if p["A_d"] >= 0.95 * A_D_CEIL:            f.append("A_d@ceiling")
    if p["A_t"] >= 0.95 * AT_BOUND:            f.append("A_t@bound")
    if p["k_Ft"] <= 2e-6:                      f.append("k_Ft@floor(unident)")
    if min(p["k_Lt"], p["k_Ld"]) <= 1.1e-6:   f.append("learn@0")
    return ",".join(f) if f else "-"


# ───────────────────────── one fit under overrides ─────────────────────────
def run_fit(data, overrides, max_test, short_days, short_weight, boost):
    saved = copy.deepcopy(ff.CONFIG)
    src = _truncated_csv(data, max_test)
    try:
        ff.CONFIG.update(overrides); ff.CONFIG["max_test"] = max_test
        df = ff.prepare_data(src)
        uw, n_short, mass = weights_with_shortboost(df, short_days, short_weight, boost)
        uids, P, D, Y, w, _ = ff.df_to_matrices(df, uw)
        params, _ = ff.run_optimization(P, D, Y, w)
        wmse = float(ff.wmse_matrix([params[k] for k in PO], P, D, Y, w))
        dAIC = np.nan
        if HAVE_ADD:
            try:
                s = add.fit_static_baseline(P, D, Y, w, params); dAIC = s["aic_static"] - s["aic_dyn"]
            except Exception:
                pass
        row = dict(N=P.shape[0], n_short=n_short, short_mass=mass, wmse=wmse, dAIC=dAIC,
                   flags=flag_at_bounds(params), **{k: params[k] for k in PO})
        return row
    finally:
        ff.CONFIG.clear(); ff.CONFIG.update(saved)
        try: os.remove(src)
        except OSError: pass


# ───────────────────────── TASK 2: the sweep ─────────────────────────
def sweep(data, max_test, short_days, short_weight):
    regimes = [
        ("no exclusion",
         dict(winsorize_outliers=False, max_plays_interval=HUGE, max_days_interval=HUGE, max_plays_per_day=HUGE)),
        ("winsorize plays@3000 (asymptote-justified)",
         dict(winsorize_outliers=True,  max_plays_interval=3000, max_days_interval=HUGE, max_plays_per_day=HUGE)),
        ("winsorize plays@5000 (conservative)",
         dict(winsorize_outliers=True,  max_plays_interval=5000, max_days_interval=HUGE, max_plays_per_day=HUGE)),
    ]
    rows = []
    for label, ov in regimes:
        for boost in (False, True):
            print(f"\n── {label}  |  short-boost={'ON' if boost else 'off'} ──")
            try:
                r = run_fit(data, ov, max_test, short_days, short_weight, boost)
                r["regime"] = label; r["boost"] = boost; rows.append(r)
            except Exception as e:
                print(f"   FAILED: {e}")

    # ---- table (all six parameters) ----
    print(f"\n{'='*118}\n  ALL-SIX-PARAMETER SWEEP  (max_test={max_test})\n{'='*118}")
    hdr = (f"  {'regime':42s} {'bst':3s} {'N':>6} {'A_t':>6} {'k_Lt':>7} "
           f"{'k_Ft':>8} {'A_d':>6} {'k_Ld':>6} {'k_Fd':>7} {'dAIC':>5}  flags")
    print(hdr); print("  " + "-"*114)
    for r in rows:
        print(f"  {r['regime'][:42]:42s} {'ON' if r['boost'] else 'off':3s} {r['N']:>6,} "
              f"{r['A_t']:>6.2f} {r['k_Lt']:>7.4f} {r['k_Ft']:>8.5f} {r['A_d']:>6.2f} "
              f"{r['k_Ld']:>6.3f} {r['k_Fd']:>7.4f} {r['dAIC']:>5.0f}  {r['flags']}")

    # ---- which parameters are least stable (the ones to watch) ----
    print(f"\n  STABILITY across the sweep (coefficient of variation; high = at risk):")
    df = pd.DataFrame(rows)
    cvs = []
    for k in PO:
        m, s = df[k].mean(), df[k].std()
        cvs.append((k, (s / abs(m)) if m else np.nan))
    for k, cv in sorted(cvs, key=lambda t: -(t[1] if t[1] == t[1] else -1)):
        tag = "  <-- WATCH" if cv > 0.15 else ""
        print(f"     {k:5s}  CV = {cv:5.2f}{tag}")
    print("\n  Reading: A_t/k_Lt should be low-CV (dose/ceiling side, well identified).")
    print("  The high-CV parameters are the 'most at risk' — judge each regime on those")
    print("  and on the flags, NOT on the transfer ceiling. 'no exclusion' is preferred")
    print("  if its at-risk params look sensible and nothing sits at a bound; otherwise")
    print("  step up to winsorize plays@3000, then @5000.")
    if rows:
        pd.DataFrame(rows).to_csv("finetune_sweep_summary.csv", index=False)
        print("\n  wrote finetune_sweep_summary.csv")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="newsubset.csv")
    ap.add_argument("--maxtest", type=int, default=3)
    ap.add_argument("--short-days", type=int, default=60)
    ap.add_argument("--short-weight", type=float, default=25.0)
    ap.add_argument("--report-only", action="store_true")
    args = ap.parse_args()

    # Task-1 diagnostic on the no-exclusion sample
    src = _truncated_csv(args.data, args.maxtest)
    try:
        saved = copy.deepcopy(ff.CONFIG)
        ff.CONFIG.update(dict(winsorize_outliers=False, max_plays_interval=HUGE,
                              max_days_interval=HUGE, max_plays_per_day=HUGE))
        df = ff.prepare_data(src)
        ff.CONFIG.clear(); ff.CONFIG.update(saved)
    finally:
        try: os.remove(src)
        except OSError: pass
    short_interval_report(df, args.short_days)

    if args.report_only:
        return
    sweep(args.data, args.maxtest, args.short_days, args.short_weight)


if __name__ == "__main__":
    main()
