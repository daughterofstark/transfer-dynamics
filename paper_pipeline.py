"""
paper_pipeline.py - merges the two extracts and defines the weighting bands.
Used by v17 (via data_build.py): build_merged, MAIN_DAY_EDGES/LBLS, NOEXCL, _truncate.
fit() and main() are the legacy v16 pipeline and are not part of the v17 workflow.
"""
from __future__ import annotations
import argparse, copy, os, tempfile
import numpy as np
import pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

import transfer_model as ff
import composite_extract as mnr
import figures as figs
try:
    import paper_additions as add;      HAVE_ADD = True
except Exception: HAVE_ADD = False
try:
    import reanalysis_v3 as rean;       HAVE_REAN = True
except Exception:
    HAVE_REAN = False
    print("  NOTE: reanalysis_v3 not importable — the exclusion sweep will be SKIPPED.\n"
          "        Equivalent analysis: python verify_numbers.py --only sweep")

PO = ff.PARAM_ORDER
HUGE = 10 ** 9
NOEXCL = dict(winsorize_outliers=False, max_plays_interval=HUGE,
              max_days_interval=HUGE, max_plays_per_day=HUGE)

# LOCKED weighting bins
MAIN_DAY_EDGES = [-1.0, 90.0, 150.0, 9999.0]   # 0-90 band includes same-day retests
MAIN_DAY_LBLS = ["D0-90", "D90-150", "D150+"]
ROBUST_DAY_EDGES = [0.0, 90.0, 150.0, 9999.0]          # original: no same-day
ROBUST_DAY_LBLS  = ["D0-90", "D90-150", "D150+"]

MANIFEST = []
def _try(name, fn):
    try:
        fn(); MANIFEST.append((name, "OK")); print(f"    OK   {name}")
    except Exception as e:
        MANIFEST.append((name, f"FAIL: {type(e).__name__}: {e}")); print(f"    FAIL {name}: {e}")


def _truncate(frame, max_test):
    d = frame[pd.to_numeric(frame["nth_test"], errors="coerce") <= max_test].copy()
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".csv").name
    d.to_csv(tmp, index=False); return tmp


# ───────────────────────── build merged data (internal) ─────────────────────────
def build_merged(data, composite, min_valid_subtests, uid_prefix, out_csv):
    print(f"\n{'='*70}\n  BUILD MERGED DATA (Grand Index + composite)\n{'='*70}")
    run = mnr.build_composite(composite, min_valid_subtests)
    chains, _ = mnr.build_chains(run)
    newsub = mnr._clean_cols(pd.read_csv(data))
    newsub = mnr.enforce_same_battery(newsub, "original")
    # participants in both extracts: the same sittings scored two ways. Keep the Grand Index copy.
    gi_ids = set(newsub["user_id"].astype(str))
    in_both = chains["user_id"].astype(str).isin(gi_ids)
    n_both = chains.loc[in_both, "user_id"].nunique()
    print(f"  composite participants also in the Grand Index file, dropped: {n_both:,}")
    chains = chains[~in_both].copy()
    nic = mnr.to_newsubset_schema(chains, list(newsub.columns), uid_prefix)
    newsub_s = newsub.copy(); newsub_s["user_id"] = newsub_s["user_id"].astype(str)
    merged = pd.concat([newsub_s, nic], ignore_index=True)
    merged.to_csv(out_csv, index=False)
    print(f"  wrote {out_csv}  (N_rows={len(merged):,})")
    return newsub, merged


# ───────────────────────── one fit (returns df + matrices) ─────────────────────────
def fit(frame, label, min_tests, max_test, day_edges, day_lbls, save_dir):
    """Fit under no-exclusion + window + explicit bins. CONFIG is left SET for the
       caller's figures; caller restores it. Returns df, P, D, Y, w, params, wmse, dAIC."""
    print(f"\n{'#'*70}\n#  FIT: {label}  (min_tests={min_tests}, T1-T{max_test}, no exclusion, "
          f"bins {day_edges})\n{'#'*70}")
    ff.CONFIG.update(NOEXCL)
    ff.CONFIG["min_tests"] = min_tests
    ff.CONFIG["max_test"]  = max_test
    ff.CONFIG["save_dir"]  = save_dir
    src = _truncate(frame, max_test)
    try:
        df = ff.prepare_data(src)
    finally:
        try: os.remove(src)
        except OSError: pass
    uw, _ = ff.compute_user_weights(df, ff.CONFIG["play_bin_edges"],
                                    ff.CONFIG["play_bin_labels"], day_edges, day_lbls)
    uids, P, D, Y, w, t2 = ff.df_to_matrices(df, uw)
    params, _final = ff.run_optimization(P, D, Y, w)
    wmse = float(ff.wmse_matrix([params[k] for k in PO], P, D, Y, w))
    dAIC = np.nan
    if HAVE_ADD:
        try:
            s = add.fit_static_baseline(P, D, Y, w, params)
            dAIC = s["aic_static"] - s["aic_dyn"]
        except Exception as e:
            print(f"  (static baseline failed: {e})")
    return df, P, D, Y, w, params, wmse, dAIC


# ───────────────────────── manifest / numbers ─────────────────────────
def print_numbers(main, robust):
    (dm, Pm, Dm, Ym, wm, pm, wmm, aicm) = main
    (dr, Pr, Dr, Yr, wr, pr, wmr, aicr) = robust
    print(f"\n{'='*74}\n  CANONICAL NUMBERS — copy into the paper\n{'='*74}")
    print(f"  {'':16s}{'MAIN (merged 2-5)':>20s}{'ROBUST (orig T1-T3)':>22s}")
    print(f"  {'N':16s}{Pm.shape[0]:>20,}{Pr.shape[0]:>22,}")
    for k in PO:
        print(f"  {k:16s}{pm[k]:>20.5g}{pr[k]:>22.5g}")
    print(f"  {'direct share':16s}{pm['A_d']/(pm['A_t']+pm['A_d']):>20.3f}"
          f"{pr['A_d']/(pr['A_t']+pr['A_d']):>22.3f}")
    print(f"  {'WMSE':16s}{wmm:>20.4f}{wmr:>22.4f}")
    print(f"  {'dAIC(dyn-stat)':16s}{aicm:>20.0f}{aicr:>22.0f}")
    print("\n  (MAIN is the model of record. ROBUST is the original-only T1-T3 check;")
    print("   WMSE is NOT comparable across columns — different data.)")


# ───────────────────────── main ─────────────────────────
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="newsubset.csv")
    ap.add_argument("--nicole", required=True)
    ap.add_argument("--min-valid-subtests", type=int, default=3)
    ap.add_argument("--uid-prefix", default="NIC_")
    ap.add_argument("--nboot", type=int, default=200)
    ap.add_argument("--main-dir", default="fig_main")
    ap.add_argument("--supp-dir", default="fig_supp")
    ap.add_argument("--merged-csv", default="merged_for_fit.csv")
    ap.add_argument("--no-exclusion-sweep", action="store_true")
    ap.add_argument("--no-figures", action="store_true")
    args = ap.parse_args()

    os.makedirs(args.main_dir, exist_ok=True)
    os.makedirs(args.supp_dir, exist_ok=True)
    saved = copy.deepcopy(ff.CONFIG)
    try:
        # 1. merged data
        newsub, merged = build_merged(args.data, args.nicole, args.min_valid_subtests,
                                      args.uid_prefix, args.merged_csv)

        # 2. MAIN fit (merged 2-5) + figures use CONFIG set here
        main = fit(merged, "MAIN (merged 2-5)", 2, 5, MAIN_DAY_EDGES, MAIN_DAY_LBLS, args.main_dir)
        dm, Pm, Dm, Ym, wm, pm, wmm, aicm = main
        _try("direct identifiability report",
             lambda: ff.report_direct_identifiability(dm, pm, Pm, Dm, Ym, wm, raised_bound=100.0))

        # 4. MAIN + SUPPLEMENT figures (one bootstrap inside, reused)
        draws_merged = None
        if not args.no_figures:
            print(f"\n{'='*70}\n  MAIN + SUPPLEMENT FIGURES\n{'='*70}")
            man, draws_merged = figs.make_all(dm, pm, Pm, Dm, Ym, wm,
                                              args.main_dir, args.supp_dir,
                                              nboot=args.nboot, seed=7, max_test=5)
            MANIFEST.extend(man)

        # 3. ROBUSTNESS fit (original T1-T3) — new CONFIG phase
        robust = fit(newsub, "ROBUST (orig T1-T3)", 3, 3, ROBUST_DAY_EDGES, ROBUST_DAY_LBLS, args.main_dir)
        dr, Pr, Dr, Yr, wr, pr, wmr, aicr = robust

        # A_d identification supp figure: original (runs to bound) vs merged (identified)
        if not args.no_figures and draws_merged is not None:
            _try("Supp A_d identification (orig vs merged)",
                 lambda: figs.fig_Ad_identification(
                     figs.bootstrap_for_orig(Pr, Dr, Yr, wr, pr, nboot=args.nboot, seed=7),
                     draws_merged, f"{args.supp_dir}/figS_Ad_identification.png"))

        # numbers side by side
        print_numbers(main, robust)

        # 5. EXCLUSION SENSITIVITY as a text robustness line (no figure)
        if not args.no_exclusion_sweep and HAVE_REAN:
            print(f"\n{'='*70}\n  EXCLUSION-SENSITIVITY (text robustness line; no figure)\n{'='*70}")
            _try("exclusion sweep (text)",
                 lambda: rean.exclusion_sweep(args.merged_csv, max_test=5))

        # manifest
        print(f"\n{'='*74}\n  FIGURE / STEP MANIFEST\n{'='*74}")
        for name, status in MANIFEST:
            print(f"  {status[:40]:40s}  {name}")
        print(f"\n  main figures -> {args.main_dir}/   supplement -> {args.supp_dir}/")
        print("  Canonical numbers are in the 'CANONICAL NUMBERS' block above.")
    finally:
        ff.CONFIG.clear(); ff.CONFIG.update(saved)


if __name__ == "__main__":
    main()
