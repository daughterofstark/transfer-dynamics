"""
refix_figures.py — regenerate ONLY the three fixed figures. No bootstrap, so it's fast.

Rebuilds the merged data + the MAIN fit (same locked spec as paper_pipeline.py:
merged, min_tests=2, T1-T5, no exclusion, day bins [-1,0.5,90,150,9999]), then
redraws:
    fig_maintenance_concept.png   (retitled: steady state — higher decays, lower rises)
    fig_time_window.png           (direct on the bottom, matching the dose partition)
    fig_schedules.png             (all three arms now spend exactly the same budget)

Everything else in fig_main/ and fig_supp/ is left untouched.

Run (same directory as the rest):
  python refix_figures.py --data newsubset.csv --nicole data/short_intervals.csv
"""
from __future__ import annotations
import argparse, copy, os, tempfile
import pandas as pd

import transfer_model as ff
import composite_extract as mnr
import figures as figs

HUGE = 10 ** 9
NOEXCL = dict(winsorize_outliers=False, max_plays_interval=HUGE,
              max_days_interval=HUGE, max_plays_per_day=HUGE)
DAY_EDGES = [-1.0, 0.5, 90.0, 150.0, 9999.0]
DAY_LBLS = ["D0", "D0-90", "D90-150", "D150+"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="newsubset.csv")
    ap.add_argument("--nicole", required=True)
    ap.add_argument("--min-valid-subtests", type=int, default=3)
    ap.add_argument("--uid-prefix", default="NIC_")
    ap.add_argument("--main-dir", default="fig_main")
    args = ap.parse_args()

    os.makedirs(args.main_dir, exist_ok=True)
    saved = copy.deepcopy(ff.CONFIG)
    try:
        # ---- rebuild merged data (same as the pipeline) ----
        print("  building merged data …")
        run = mnr.build_nicole_composite(args.nicole, args.min_valid_subtests)
        chains, _ = mnr.build_chains(run)
        newsub = mnr._clean_cols(pd.read_csv(args.data))
        newsub = mnr.enforce_same_battery(newsub, "original")
        nic = mnr.to_newsubset_schema(chains, list(newsub.columns), args.uid_prefix)
        newsub["user_id"] = newsub["user_id"].astype(str)
        merged = pd.concat([newsub, nic], ignore_index=True)

        # ---- MAIN fit (no bootstrap) ----
        ff.CONFIG.update(NOEXCL)
        ff.CONFIG["min_tests"] = 2
        ff.CONFIG["max_test"] = 5
        ff.CONFIG["save_dir"] = args.main_dir
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".csv").name
        merged[pd.to_numeric(merged["nth_test"], errors="coerce") <= 5].to_csv(tmp, index=False)
        try:
            df = ff.prepare_data(tmp)
        finally:
            try: os.remove(tmp)
            except OSError: pass
        uw, _ = ff.compute_user_weights(df, ff.CONFIG["play_bin_edges"],
                                        ff.CONFIG["play_bin_labels"], DAY_EDGES, DAY_LBLS)
        _, P, D, Y, w, _ = ff.df_to_matrices(df, uw)
        params, _ = ff.run_optimization(P, D, Y, w)
        print(f"\n  fit: A_t={params['A_t']:.4f}  A_d={params['A_d']:.4f}  "
              f"k_Lt={params['k_Lt']:.5f}  k_Ft={params['k_Ft']:.5f}")

        # ---- redraw the changed deterministic figures (no bootstrap needed) ----
        md = args.main_dir
        print(f"\n  redrawing figures -> {md}/")
        for name, fn in [
            ("schematic (independent processes)", lambda: figs.fig_schematic(params, f"{md}/fig_schematic.png")),
            ("3x3 empirical match (own intervals)", lambda: figs.fig_dose_9panel(df, params, f"{md}/fig_dose_9panel.png")),
            ("3-panel dose row (T1-T2 fixed)", lambda: figs.fig_dose_row(df, params, f"{md}/fig_dose_row.png")),
            ("dose-response partition (mean days)", lambda: figs.fig_dose_partition(df, params, f"{md}/fig_dose_partition.png")),
            ("dose x time heatmap (journal fonts)", lambda: figs.fig_dose_time_heatmap(params, f"{md}/fig_dose_time_heatmap.png")),
            ("maintenance concept (2 panels, %)", lambda: figs.fig_maintenance_concept(df, params, f"{md}/fig_maintenance_concept.png")),
            ("maintenance dose (90%, 5 g/day)", lambda: figs.fig_maintenance(params, f"{md}/fig_maintenance.png", kft_ci=(6.1e-4, 8.1e-3))),
            ("fixed dose x time window", lambda: figs.fig_time_window(df, params, f"{md}/fig_time_window.png")),
            ("schedule comparison (boosters, %)", lambda: figs.fig_schedules(params, f"{md}/fig_schedules.png")),
        ]:
            try:
                fn(); print(f"    OK   {name}")
            except Exception as e:
                print(f"    FAIL {name}: {type(e).__name__}: {e}")
        print(f"\n  done — deterministic figures rewritten (bootstrap figures untouched).")
    finally:
        ff.CONFIG.clear(); ff.CONFIG.update(saved)


if __name__ == "__main__":
    main()
