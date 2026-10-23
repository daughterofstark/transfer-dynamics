"""
intercept_check.py — empirical intercept, no model. Fast.

The dose-response intercept (familiarity at ~one retest) fits at ~1.9 GI points,
higher than Allen's ~1.5. This checks the DATA directly: the mean T2-T1 change for
participants with very little gameplay between T1 and T2 (default <=25 games), any
interval. If it's ~1.9 the model is faithful; if it's ~1.5 the model's A_d is
inflating the intercept and we should say so.

Reports for the merged sample AND the original-only sample (they may differ, since
the augmentation is short-interval-heavy).

Run:
  python intercept_check.py --data newsubset.csv --nicole data/short_intervals.csv
"""
from __future__ import annotations
import argparse
import numpy as np, pandas as pd

import composite_extract as mnr


def _t2_delta(df, max_games=25):
    """Per-participant T2-T1 GI change for those with <= max_games between T1 and T2."""
    df = df.copy()
    df["nth_test"] = pd.to_numeric(df["nth_test"], errors="coerce")
    df["normed_score"] = pd.to_numeric(df["normed_score"], errors="coerce")
    df["plays_interval_raw"] = pd.to_numeric(df["num_plays_before"], errors="coerce")
    g = df.sort_values(["user_id", "nth_test"])
    s1 = g[g["nth_test"] == 1].set_index("user_id")["normed_score"]
    row2 = g[g["nth_test"] == 2].set_index("user_id")
    s2 = row2["normed_score"]
    # games between T1 and T2 = cumulative plays at T2 minus at T1
    p1 = g[g["nth_test"] == 1].set_index("user_id")["plays_interval_raw"]
    p2 = row2["plays_interval_raw"]
    users = s1.index.intersection(s2.index)
    delta = (s2.loc[users] - s1.loc[users])
    games = (p2.loc[users] - p1.loc[users])
    days = None
    if "days_since_signup" in df.columns:
        d1 = g[g["nth_test"] == 1].set_index("user_id")["days_since_signup"].astype(float)
        d2 = row2["days_since_signup"].astype(float)
        days = (d2.loc[users] - d1.loc[users])
    low = games <= max_games
    return delta[low].dropna(), (days[low].dropna() if days is not None else None), int(low.sum())


def report(name, df, max_games):
    d, days, n = _t2_delta(df, max_games)
    print(f"\n  [{name}]  participants with <= {max_games} games T1->T2 : n = {n:,}")
    print(f"     mean T2-T1 GI change = {d.mean():.3f}   (median {d.median():.3f}, "
          f"SE {d.std()/np.sqrt(len(d)):.3f}, 95% CI [{d.mean()-1.96*d.std()/np.sqrt(len(d)):.3f}, "
          f"{d.mean()+1.96*d.std()/np.sqrt(len(d)):.3f}])")
    if days is not None and len(days):
        print(f"     their T1->T2 interval: median {days.median():.0f} d, mean {days.mean():.0f} d")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="newsubset.csv")
    ap.add_argument("--nicole", required=True)
    ap.add_argument("--min-valid-subtests", type=int, default=3)
    ap.add_argument("--uid-prefix", default="NIC_")
    ap.add_argument("--max-games", type=int, default=25)
    args = ap.parse_args()

    orig = mnr._clean_cols(pd.read_csv(args.data))
    print("="*66)
    print("  EMPIRICAL INTERCEPT — mean GI change at very low gameplay (no model)")
    print("="*66)
    report("original", orig, args.max_games)

    # merged
    run = mnr.build_nicole_composite(args.nicole, args.min_valid_subtests)
    chains, _ = mnr.build_chains(run)
    nic = mnr.to_newsubset_schema(chains, list(orig.columns), args.uid_prefix)
    o = orig.copy(); o["user_id"] = o["user_id"].astype(str)
    merged = pd.concat([o, nic], ignore_index=True)
    report("merged", merged, args.max_games)

    print("\n  Read: model intercept fits ~1.9. If the empirical means above are ~1.9,")
    print("  the model is faithful; if ~1.5, A_d is inflating the intercept — flag it.")


if __name__ == "__main__":
    main()
