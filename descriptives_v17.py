"""
descriptives_v17.py - descriptive and point-estimate numbers for the v17 manuscript.

No bootstrap. Builds the prepared data exactly as run_v17.py does, refits the point
estimate from the same start (checked against the reported v17 estimate), and reports
sample flow, exposure, weighting cells, demographics, dates, residuals and the
Results-text numbers at the data-derived mean interval. Regenerates the Fig. 5 panel
at 440 gameplays. Writes out/v17/descriptives.md and out/v17/supp_table1_weights.csv;
does not touch out/v17/report.md.

Run:  python descriptives_v17.py            (add --rebuild to rebuild the merged data)
"""
from __future__ import annotations
import argparse, os
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

import transfer_model as ff
import paper_pipeline as pp
import figures as figs
import data_build as db
import run_v17 as rv

PO = ff.PARAM_ORDER
OUT = os.path.join("out", "v17")
V17 = np.array([0.0045704, 0.0021256, 0.3076, 0.0014601, 3.0535, 7.2487])   # report.md, commit 252d83b
LINES: list[str] = []


def say(s=""):
    print(s); LINES.append(s)


def header(t):
    say("\n" + "=" * 74); say("  " + t); say("=" * 74)


def run_ids(s):
    return pd.to_numeric(s, errors="coerce").astype("Int64").astype(str)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data/newsubset.csv")
    ap.add_argument("--composite", "--nicole", dest="composite", default="data/short_intervals.csv")
    ap.add_argument("--min-valid-subtests", type=int, default=3)
    ap.add_argument("--uid-prefix", default="NIC_")
    ap.add_argument("--rebuild", action="store_true")
    args = ap.parse_args()
    os.makedirs(os.path.join(OUT, "fig_main"), exist_ok=True)
    pre = args.uid_prefix

    newsub, merged = db.build_merged_once(args)
    df, uids, P, D, Y, w = rv.prepare(merged)
    is_comp = df["user_id"].astype(str).str.startswith(pre)

    header("POINT ESTIMATE (refit from the v17 start; no bootstrap)")
    r = ff._fit(rv.osman_start(), P, D, Y, w, rv.BOUNDS)
    x = np.asarray(r.x); p = dict(zip(PO, x))
    rel = float(np.max(np.abs(x / V17 - 1)))
    say(f"  WMSE {r.fun:.6f}   " + "  ".join(f"{k}={v:.5g}" for k, v in zip(PO, x)))
    say(f"  largest relative difference from the reported v17 estimate: {100 * rel:.4f}%")
    if rel > 1e-3:
        say("  !! differs from the reported v17 run by more than 0.1%; do not use these numbers until resolved")

    header("SAMPLE AND ADMINISTRATIONS")
    m = merged.copy()
    m["user_id"] = m["user_id"].astype(str)
    m["nth_test"] = pd.to_numeric(m["nth_test"], errors="coerce")
    mc = m["user_id"].str.startswith(pre)
    for lab, sub in (("Grand Index", m[~mc]), ("composite", m[mc]), ("all", m)):
        say(f"  {lab:12s} participants {sub['user_id'].nunique():>7,}   administrations {len(sub):>8,}   "
            f"within first five {int((sub['nth_test'] <= 5).sum()):>8,}")
    say(f"  mean administrations per participant (all records): {len(m) / m['user_id'].nunique():.2f}")
    k = df.groupby("user_id")["nth_test"].max()
    say(f"  participants entering the fit: {Y.shape[0]:,}   "
        f"post-baseline administrations in the fit: {int(np.isfinite(Y).sum()):,}")
    say("  retained administrations per participant (first five): " +
        ", ".join(f"{int(a)}: {n:,}" for a, n in k.value_counts().sort_index().items()))
    say(f"  participants with at least three retained administrations: {int((k >= 3).sum()):,}")

    header("EXPOSURE - FIRST INTERVAL")
    t2 = df[df["nth_test"] == 2]
    days = t2["days_interval"].astype(float); plays = t2["plays_interval"].astype(float)
    vc = days.round().astype(int).value_counts()
    say(f"  modal interval {vc.idxmax()} d ({100 * vc.max() / len(days):.1f}%)   mean {days.mean():.1f} d")
    say("  percentiles (days): " + "  ".join(f"p{q} {np.percentile(days, q):.0f}" for q in (25, 50, 75, 90, 95, 99))
        + f"   max {days.max():.0f}")
    short = (days >= 1) & (days <= 69)
    say(f"  same-day first intervals: {int((days == 0).sum()):,}   1-69 days: {int(short.sum()):,} ({100 * short.mean():.2f}%)")
    say(f"  longest interval at any position: {df.loc[df['nth_test'] >= 2, 'days_interval'].max():.0f} d")
    say("  gameplays: " + "  ".join(f"p{q} {np.percentile(plays, q):.0f}" for q in (25, 50, 75, 90, 95))
        + f"   max {plays.max():.0f}   (median = {plays.median() * figs.MINUTES_PER_GAME / 60:.1f} h)")
    say(f"  total gameplays between consecutive retained administrations: "
        f"{df.loc[df['nth_test'] >= 2, 'plays_interval'].sum():,.0f}")
    strata = pd.cut(plays, [-1, 50, 200, 500, np.inf], labels=["<=50", "51-200", "201-500", ">=501"])
    say("  gameplay strata (first interval): n, %, mean change at second administration")
    for lab, g in t2.groupby(strata, observed=False):
        say(f"    {lab:8s} {len(g):>7,}  {100 * len(g) / len(t2):5.2f}%  {g['score_delta'].mean():+.2f}")

    header("SUPPLEMENTARY TABLE 1 - WEIGHTING CELLS")
    _, ub = ff.compute_user_weights(df, ff.CONFIG["play_bin_edges"], ff.CONFIG["play_bin_labels"],
                                    pp.MAIN_DAY_EDGES, pp.MAIN_DAY_LBLS)
    cnt = ub.value_counts(); raw_w = len(ub) / (len(cnt) * cnt)
    tab = pd.DataFrame({"participants": cnt, "raw_weight": raw_w,
                        "weight": raw_w.clip(upper=ff.CONFIG["max_weight"])})
    tab.round(3).to_csv(os.path.join(OUT, "supp_table1_weights.csv"))
    for c, rr in tab.sort_index().iterrows():
        say(f"  {c:20s} {int(rr.participants):>7,}  weight {rr.weight:.3f}")
    say(f"  populated cells {len(cnt)} of {len(ff.CONFIG['play_bin_labels']) * len(pp.MAIN_DAY_LBLS)};  "
        f"capped: {int((raw_w > ff.CONFIG['max_weight']).sum())}")
    rho, _ = spearmanr(days, plays)
    rho2, _ = spearmanr(days[days > 0], plays[days > 0])
    say(f"  Spearman rho (first-interval days, gameplays) = {rho:.3f};  excluding same-day = {rho2:.3f}")

    header("DEMOGRAPHICS AT FIRST ADMINISTRATION")
    t1 = df[df["nth_test"] == 1]
    t1c = t1["user_id"].astype(str).str.startswith(pre)
    for lab, sub in (("Grand Index", t1[~t1c]), ("composite", t1[t1c])):
        age = pd.to_numeric(sub["age"], errors="coerce")
        say(f"  [{lab}] n = {len(sub):,}")
        say(f"    age: n {age.notna().sum():,}  mean {age.mean():.1f}  SD {age.std():.1f}  "
            f"range {age.min():.0f}-{age.max():.0f}  under 18: {int((age < 18).sum()):,}")
        gnd = sub["gender"].str.lower().fillna("missing").value_counts(normalize=True, dropna=False)
        say("    gender: " + ", ".join(f"{g} {100 * v:.1f}%" for g, v in gnd.items()))
        edu = pd.to_numeric(sub["education_level"], errors="coerce")
        say(f"    education_level codes (n {edu.notna().sum():,}): " +
            ", ".join(f"{int(c)}: {n:,}" for c, n in edu.value_counts().sort_index().items()))

    header("DATES OF ADMINISTRATIONS IN THE FIT")
    gi = df[~is_comp]
    s = pd.to_datetime(gi["signup_date"], format="%d/%m/%y", errors="coerce")
    dgi = s + pd.to_timedelta(gi["days_since_signup"], unit="D")
    say(f"  Grand Index: {dgi.min().date()} to {dgi.max().date()}   (unparseable signup dates: {int(s.isna().sum()):,})")
    rawc = pd.read_csv(args.composite, usecols=["TEST_RUN_ID", "TRESULT_CREATED_AT"], low_memory=False)
    tf = pd.to_datetime(rawc["TRESULT_CREATED_AT"], errors="coerce").groupby(run_ids(rawc["TEST_RUN_ID"])).min()
    dc = run_ids(df.loc[is_comp, "test_run_id"]).map(tf)
    say(f"  composite:   {dc.min().date()} to {dc.max().date()}   (sittings without a date: {int(dc.isna().sum()):,})")

    header("RESULTS-TEXT NUMBERS AT THE ESTIMATE")
    mean_d = float(days.mean())
    for frac in (0.5, 0.75, 0.8):
        g = figs._games_for_transfer_frac(p, frac, 90)
        say(f"  {int(frac * 100)}% of transfer ceiling over 90 days: {g:.0f} gameplays = "
            f"{g * figs.MINUTES_PER_GAME / 60:.1f} h")
    adv = lambda Dd, Pp: ff.advance_interval(0, 0, Dd, Pp, p["k_Ld"], p["k_Fd"], p["k_Lt"], p["k_Ft"], p["A_d"], p["A_t"])
    sd0, st0 = adv(mean_d, 0)
    say(f"  Fig. 4 at the mean first interval ({mean_d:.0f} d): no training {sd0 + st0:.2f}; "
        f"with extensive training {sd0 + p['A_t']:.2f}")
    for Dd in (1, 365):
        sd, st = adv(Dd, 440)
        say(f"  Fig. 5, 440 gameplays over {Dd:3d} d: total {sd + st:.2f} (retest {sd:.2f}, transfer {st:.2f})")
    dv = rv.derived(x)
    say("  steady state (% of ceiling): " + "  ".join(f"{mm} min {dv[f'ss_{mm}min']:.1f}" for mm in rv.MINUTES))
    for key in ("even", "load", "boost"):
        say(f"  {rv.NAMES[key]:28s} endpoint {dv[f'{key}_end']:.1f}%   average {dv[f'{key}_avg']:.1f}%")

    header("IN-SAMPLE RESIDUALS AT THE SECOND ADMINISTRATION")
    pr = ff.simulate_matrix(P, D, x)[:, 0]; ob = Y[:, 0]; ok = np.isfinite(pr) & np.isfinite(ob)
    res = ob[ok] - pr[ok]
    say(f"  mean {res.mean():.2f}   SD {res.std():.2f}   MAE {np.abs(res).mean():.2f}   "
        f"R2 {1 - np.sum(res ** 2) / np.sum((ob[ok] - ob[ok].mean()) ** 2):.3f}")
    say(f"  correlation of baseline score with change at second administration: "
        f"{t2['t1_score'].corr(t2['score_delta']):.3f}")

    header("BOOTSTRAP CONVERGENCE (from the v17 run)")
    bi_path = os.path.join(OUT, "bootstrap_info.csv")
    if os.path.exists(bi_path):
        bi = pd.read_csv(bi_path)
        say(f"  converged {int(bi['success'].sum())} of {len(bi)}")
        for _, rr in bi[~bi["success"].astype(bool)].iterrows():
            say(f"    sample {int(rr['b'])}: iterations {int(rr['nit'])}, WMSE {rr['wmse']:.4f}, message: {rr['message']}")
    else:
        say(f"  {bi_path} not found")

    header("FIGURE")
    path = os.path.join(OUT, "fig_main", "fig_time_window.png")
    figs.fig_time_window(df, p, path, fixed_games=440)
    say(f"  regenerated {path} at 440 gameplays (22 h)")

    with open(os.path.join(OUT, "descriptives.md"), "w") as fh:
        fh.write("\n".join(LINES) + "\n")
    print(f"\n  wrote {OUT}/descriptives.md and {OUT}/supp_table1_weights.csv")


if __name__ == "__main__":
    main()
