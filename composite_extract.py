"""
composite_extract.py - composite records from the short-interval NCPT extract.
Used by v17 through paper_pipeline.build_merged:
  build_composite      mean of valid subtest index scores per sitting (>=3); one result per
                       subtest (first attempt); sitting date = first subtest result; gameplays
                       = the one stored value per sitting
  build_chains         consecutive same-battery sittings starting at the first sitting
  to_newsubset_schema  recast to the Grand Index schema; IDs prefixed NIC_
fit_spec, bootstrap_draws, stability_report and main() are legacy (v16) exploration code.
"""
from __future__ import annotations
import argparse, copy, os, sys, tempfile
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import transfer_model as ff
try:
    import paper_additions as add
    HAVE_ADD = True
except Exception:
    HAVE_ADD = False

PO = ff.PARAM_ORDER                    # ["k_Lt","k_Ft","k_Ld","k_Fd","A_t","A_d"]
HUGE = 10 ** 9

# no-exclusion overrides (mirror finetune_v4.py's "no exclusion" regime)
NOEXCL = dict(winsorize_outliers=False, max_plays_interval=HUGE,
              max_days_interval=HUGE, max_plays_per_day=HUGE)

# Step-4 fix: a same-day bucket. Default engine day edges are [0,90,180,9999],
# so 0 falls outside (0,90] -> NaN bin -> capped 5x. [-1,0.5,...] captures 0.
DAY_EDGES_D0 = [-1.0, 0.5, 90.0, 180.0, 9999.0]
DAY_LBLS_D0  = ["D0", "D0-90", "D90-180", "D180+"]


def _auto_day_labels(edges):
    """Human labels from edges. (-1,0.5]->'D0' (same-day); last bin ->'D{lo}+'."""
    lbls = []
    for i in range(len(edges) - 1):
        lo, hi = edges[i], edges[i + 1]
        if lo < 0 and hi <= 1:
            lbls.append("D0")
        elif i == len(edges) - 2:
            lbls.append(f"D{int(max(lo,0))}+")
        else:
            lbls.append(f"D{int(max(lo,0))}-{int(hi)}")
    return lbls

# the 12 un-normed subtests (index_score == 0); used only to cross-check the drop
UNNORMED_SUBTEST_IDS = {36, 51, 52, 53, 54, 55, 57, 58, 59, 60, 61, 63}

A_D_CEIL = ff.CONFIG.get("A_d_ceiling", 100.0)
AT_BOUND = 30.0


def flag_at_bounds(p):
    f = []
    if p["A_d"] >= 0.95 * A_D_CEIL:          f.append("A_d@ceiling")
    if p["A_t"] >= 0.95 * AT_BOUND:          f.append("A_t@bound")
    if p["k_Ft"] <= 2e-6:                    f.append("k_Ft@floor(unident)")
    if min(p["k_Lt"], p["k_Ld"]) <= 1.1e-6:  f.append("learn@0")
    return ",".join(f) if f else "-"


# ───────────────────────── column helpers ─────────────────────────
def _clean_cols(df):
    df.columns = [str(c).replace("\ufeff", "").strip().lower() for c in df.columns]
    return df


def _pick(df, candidates, required=True, what=""):
    for c in candidates:
        if c in df.columns:
            return c
    if required:
        raise ValueError(
            f"Could not find a column for {what or candidates[0]}. "
            f"Tried {candidates}. Present: {list(df.columns)}")
    return None


# ───────────────────────── STEP 1: composite MEAN composite ─────────────────────────
def build_composite(path, min_valid_subtests=3):
    print(f"\n{'='*72}\n  STEP 1  composite = MEAN of per-subtest index_score\n{'='*72}")
    raw = _clean_cols(pd.read_csv(path))
    print(f"  raw rows (subtest grain)      : {len(raw):,}")

    c_user   = _pick(raw, ["user_id"], what="user_id")
    c_run    = _pick(raw, ["test_run_id", "trun_id", "run_id"], what="test_run_id")
    c_batt   = _pick(raw, ["brainpower_test_id", "battery_id", "battery"], what="brainpower_test_id")
    c_nth    = _pick(raw, ["nth_run", "nth_run_specific"], what="nth_run")
    c_index  = _pick(raw, ["index_score"], what="index_score")
    c_days   = _pick(raw, ["days_between_test_runs", "days_between"], what="days_between_test_runs")
    c_plays  = _pick(raw, ["gameplays_between_test_runs", "gameplays_between", "plays_between"],
                     what="gameplays_between_test_runs")
    c_sub    = _pick(raw, ["section_id", "test_section_id", "subtest_id"], required=False,
                     what="subtest id (for drop cross-check)")
    c_gender = _pick(raw, ["gender"], required=False)
    c_age    = _pick(raw, ["age_at_signup", "age"], required=False)
    c_edu    = _pick(raw, ["education_level", "education"], required=False)
    c_signup = _pick(raw, ["signup_date"], required=False)
    c_tres   = _pick(raw, ["tresult_created_at"], what="tresult_created_at")

    for col in [c_index, c_days, c_plays, c_nth]:
        raw[col] = pd.to_numeric(raw[col], errors="coerce")
    # when each sitting was taken: its first subtest result (the anchor the Grand Index intervals use)
    raw["_t_first"] = pd.to_datetime(raw[c_tres], errors="coerce")
    t_first_run = raw.groupby(c_run)["_t_first"].min()

    # ── sanity on the raw per-subtest index scores (before dropping zeros) ──
    idx = raw[c_index]
    nz  = idx[(idx != 0) & idx.notna()]
    lo_b, hi_b = 40.0, 160.0                     # ~ +-4 SD around 100/15
    n_out = int(((nz < lo_b) | (nz > hi_b)).sum())
    print(f"  non-zero index_score          : n={len(nz):,}  "
          f"mean={nz.mean():.1f}  sd={nz.std():.1f}  "
          f"min/med/max={nz.min():.1f}/{nz.median():.1f}/{nz.max():.1f}")
    print(f"  index_score outside [{lo_b:.0f},{hi_b:.0f}] : {n_out:,}  "
          f"({100*n_out/max(len(nz),1):.2f}%  — flagged, not dropped)")

    # ── drop the un-normed / zero rows ──
    before = len(raw)
    zero_mask = (raw[c_index] == 0) | raw[c_index].isna()
    if c_sub is not None:
        dropped_ids = sorted(pd.to_numeric(raw.loc[zero_mask, c_sub], errors="coerce")
                             .dropna().astype(int).unique().tolist())
        unexpected = sorted(set(dropped_ids) - UNNORMED_SUBTEST_IDS)
        missing    = sorted(UNNORMED_SUBTEST_IDS - set(dropped_ids))
        print(f"  zero-index subtest ids dropped: {dropped_ids}")
        if unexpected:
            print(f"    NOTE: also zero for ids {unexpected} beyond the expected 12 "
                  f"— verify these are genuinely un-normed, not a normed subtest at 0.")
        if missing:
            print(f"    NOTE: expected-un-normed ids not seen as zero: {missing}")
    raw = raw[~zero_mask].copy()
    # one result per subtest per run: exact repeats, plus one in-run retake (first attempt kept)
    if c_sub is not None:
        c_time = _pick(raw, ["tresult_created_at"], required=False)
        if c_time is not None:
            raw = raw.sort_values(c_time, kind="stable")
        n_before = len(raw)
        raw = raw.drop_duplicates([c_run, c_sub], keep="first")
        print(f"  duplicate (run, subtest) rows dropped : {n_before - len(raw):,}  (first attempt kept)")
    print(f"  dropped zero-index rows        : {before-len(raw):,}  (kept {len(raw):,})")

    # ── collapse to run grain: MEAN of valid indices, count, per-run scalars ──
    g = raw.groupby(c_run, sort=False)
    run = pd.DataFrame({
        "user_id":   g[c_user].first(),
        "battery":   g[c_batt].first(),
        "nth_run":   g[c_nth].first(),
        "days_btw":  g[c_days].max(),      # reference only; intervals use t_first
        "plays_btw": g[c_plays].max(),     # one non-zero value per sitting
        "composite": g[c_index].mean(),      # <-- MEAN of per-subtest census-normed indices
        "n_valid":   g[c_index].size(),
    }).reset_index().rename(columns={c_run: "test_run_id"})
    for opt, name in [(c_gender, "gender"), (c_age, "age"),
                      (c_edu, "education_level"), (c_signup, "signup_date")]:
        run[name] = g[opt].first().values if opt is not None else np.nan

    run["t_first"] = run["test_run_id"].map(t_first_run).values
    n_runs_all = len(run)
    run = run[run["n_valid"] >= min_valid_subtests].copy()
    print(f"  runs total / with >= {min_valid_subtests} subtests : {n_runs_all:,} / {len(run):,}")
    print(f"  subtests per run  min/med/max  : "
          f"{run['n_valid'].min():.0f}/{run['n_valid'].median():.0f}/{run['n_valid'].max():.0f}")

    comp = run["composite"]
    n_cout = int(((comp < lo_b) | (comp > hi_b)).sum())
    print(f"\n  composite (mean) all runs      : mean={comp.mean():.1f}  sd={comp.std():.1f}  "
          f"min/med/max={comp.min():.1f}/{comp.median():.1f}/{comp.max():.1f}")
    print(f"  composite outside [{lo_b:.0f},{hi_b:.0f}] : {n_cout:,}  (flagged)")
    print(f"  (SD ~12 is expected for a mean of correlated subtests; newsubset GI is"
          f" ~15, a mild proportional difference — see header.)")
    bstat = (run.groupby("battery")["composite"].agg(["count", "mean", "std"])
             .sort_values("count", ascending=False).head(6))
    print("  largest batteries (count / composite mean / sd):")
    for b, r in bstat.iterrows():
        sd = r["std"]
        print(f"     battery {b}: n={int(r['count']):>6,}  mean={r['mean']:.1f}  "
              f"sd={sd:.1f}" if sd == sd else
              f"     battery {b}: n={int(r['count']):>6,}  mean={r['mean']:.1f}  sd=n/a")
    return run


# ───────────────────────── STEP 2: same-battery chains ─────────────────────────
def build_chains(run):
    print(f"\n{'='*72}\n  STEP 2  same-battery consecutive chains from each user's first run\n{'='*72}")
    run = run.sort_values(["user_id", "nth_run"]).reset_index(drop=True)

    first_two = run.groupby("user_id").head(2)
    share = []
    for u, sub in first_two.groupby("user_id"):
        if len(sub) >= 2:
            b = sub["battery"].values
            share.append(b[0] == b[1])
    share = np.array(share)
    if len(share):
        print(f"  users with >=2 runs           : {len(share):,}")
        print(f"  run1 & run2 SAME battery      : {int(share.sum()):,}  "
              f"({100*share.mean():.1f}%)")

    chains = []; n_late = 0
    for u, sub in run.groupby("user_id", sort=False):
        sub = sub.sort_values("nth_run")
        if sub["nth_run"].iloc[0] != 1:
            n_late += 1          # first NCPT dropped (<min valid subtests): baseline would be a retest
            continue
        b0 = sub["battery"].iloc[0]
        nth = sub["nth_run"].values
        keep_rows, prev = [], None
        for i in range(len(sub)):
            if sub["battery"].iloc[i] != b0:
                break
            if prev is not None and nth[i] != prev + 1:
                break               # require consecutive nth_run (no gaps)
            keep_rows.append(sub.index[i]); prev = nth[i]
        c = sub.loc[keep_rows].copy()
        c["nth_test"] = np.arange(1, len(c) + 1)
        chains.append(c)
    chains = pd.concat(chains, ignore_index=True)
    print(f"  users excluded, first run not their first NCPT : {n_late:,}")

    lengths = chains.groupby("user_id").size()
    print(f"\n  chain-length distribution (same-battery, consecutive):")
    vc = lengths.value_counts().sort_index()
    for L, n in vc.items():
        bar = "#" * min(40, int(40 * n / vc.max()))
        print(f"     length {int(L):>2} : {n:>6,}  {bar}")
    print(f"  users with a chain length >= 2 : {int((lengths>=2).sum()):,}")
    print(f"  users with a chain length >= 3 : {int((lengths>=3).sum()):,}")
    return chains, lengths


# ───────────────────────── STEP 3: newsubset schema ─────────────────────────
def to_newsubset_schema(chains, newsubset_cols, uid_prefix="NIC_"):
    print(f"\n{'='*72}\n  STEP 3  recast chains into newsubset native schema\n{'='*72}")
    keep_users = chains.groupby("user_id").size()
    keep_users = keep_users[keep_users >= 2].index
    ch = chains[chains["user_id"].isin(keep_users)].sort_values(
        ["user_id", "nth_test"]).copy()

    is_first = ch["nth_test"] == 1
    dbtw = ch["days_btw"].fillna(0.0).where(~is_first, 0.0)
    pbtw = ch["plays_btw"].fillna(0.0).where(~is_first, 0.0)
    t0 = ch["t_first"].dt.normalize()
    ch["days_since_signup"] = (t0 - t0.groupby(ch["user_id"]).transform("first")).dt.days.astype(float)
    n_back = int((ch.groupby("user_id")["days_since_signup"].diff() < 0).sum())
    print(f"  intervals from first-result dates; sittings taken before the previous one: {n_back:,}")
    ch["num_plays_before"]  = pbtw.groupby(ch["user_id"]).cumsum()

    out = pd.DataFrame({c: np.nan for c in newsubset_cols}, index=range(len(ch)))
    out["user_id"]           = (uid_prefix + ch["user_id"].astype(str).values)
    out["nth_test"]          = ch["nth_test"].astype(int).values
    out["normed_score"]      = ch["composite"].values             # mean composite (100-scale)
    out["num_plays_before"]  = ch["num_plays_before"].values
    out["days_since_signup"] = ch["days_since_signup"].values
    if "test_run_id" in newsubset_cols:
        out["test_run_id"]   = ch["test_run_id"].astype(str).values
    for name in ["gender", "age", "education_level", "signup_date"]:
        if name in newsubset_cols and name in ch.columns:
            out[name] = ch[name].values
    print(f"  composite participants kept (chain>=2)   : {out['user_id'].nunique():,}")
    print(f"  composite rows written            : {len(out):,}")
    return out


# ───────────────────────── same-battery on the ORIGINAL ─────────────────────────
BATT_CANDS = ["brainpower_test_id", "battery_id", "battery", "test_battery_id", "brainpower_test"]

def enforce_same_battery(df, label):
    """If the original carries a battery column, keep each user's leading
       same-battery run (chain stops at the first battery change), mirroring how
       composite's chains are built. If no battery column exists, warn and pass
       through — it cannot be enforced or verified from this file."""
    col = next((c for c in BATT_CANDS if c in df.columns), None)
    if col is None:
        print(f"  [{label}] NO battery column present ({'/'.join(BATT_CANDS[:3])}…). "
              f"Cannot enforce or VERIFY same-battery on the original from this file; "
              f"assuming it was enforced upstream before extraction.")
        return df
    df = df.sort_values(["user_id", "nth_test"])
    keep, trimmed = [], 0
    for u, sub in df.groupby("user_id", sort=False):
        b0 = sub[col].iloc[0]; kept = 0
        for i in range(len(sub)):
            if sub[col].iloc[i] != b0:
                break
            keep.append(sub.index[i]); kept += 1
        if kept < len(sub):
            trimmed += 1
    out = df.loc[keep].copy()
    out["nth_test"] = out.groupby("user_id").cumcount() + 1
    print(f"  [{label}] same-battery enforced on '{col}': trimmed {trimmed:,} users, "
          f"dropped {len(df)-len(out):,} rows.")
    return out


def chain_composition(frame, label, min_tests, max_test):
    """Report the short-vs-long chain imbalance on the sample ACTUALLY FITTED
       (i.e. after the min_tests filter), so it isn't misread at min_tests=3
       where 2-test users are excluded anyway."""
    f = frame.copy()
    f["nth_test"] = pd.to_numeric(f["nth_test"], errors="coerce")
    f = f[f["nth_test"] <= max_test]
    lens = f.groupby("user_id")["nth_test"].max()
    lens = lens[lens >= min_tests]                      # only users that enter the fit
    print(f"\n  [{label}] FITTED chain-length mix (min_tests={min_tests}, <= T{max_test}):")
    vc = lens.value_counts().sort_index(); tot = len(lens)
    for L, n in vc.items():
        print(f"     {int(L)} tests: {n:>7,}  ({100*n/max(tot,1):4.1f}%)")
    print(f"  [{label}] intervals contributed by position:")
    for k in range(2, max_test + 1):
        nk = int((lens >= k).sum())
        print(f"     T{k-1}->T{k}: {nk:>7,}")


# ───────────────────────── fit harness (mirror finetune_v4) ─────────────────────────
def _truncate_to_temp(df, max_test):
    d = df[pd.to_numeric(df["nth_test"], errors="coerce") <= max_test].copy()
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".csv").name
    d.to_csv(tmp, index=False)
    return tmp


def fit_spec(frame, label, min_tests, max_test=3,
             day_edges=DAY_EDGES_D0, day_lbls=DAY_LBLS_D0):
    """Fit one dataset under no-exclusion + T1..max_test + the D0 day-bins.
       Returns (row_dict, P, D, Y, w, params) so the caller can bootstrap it."""
    print(f"\n{'#'*72}\n#  FIT: {label}   (min_tests={min_tests}, T1-T{max_test}, no exclusion)\n{'#'*72}")
    saved = copy.deepcopy(ff.CONFIG)
    src = _truncate_to_temp(frame, max_test)
    try:
        ff.CONFIG.update(NOEXCL)
        ff.CONFIG["min_tests"] = min_tests
        ff.CONFIG["max_test"]  = max_test
        df = ff.prepare_data(src)
        uw, _ = ff.compute_user_weights(
            df, ff.CONFIG["play_bin_edges"], ff.CONFIG["play_bin_labels"],
            day_edges, day_lbls)
        uids, P, D, Y, w, _ = ff.df_to_matrices(df, uw)
        params, _res = ff.run_optimization(P, D, Y, w)
        wmse = float(ff.wmse_matrix([params[k] for k in PO], P, D, Y, w))
        dAIC = np.nan
        if HAVE_ADD:
            try:
                s = add.fit_static_baseline(P, D, Y, w, params)
                dAIC = s["aic_static"] - s["aic_dyn"]
            except Exception as e:
                print(f"  (static baseline failed: {e})")
        row = dict(label=label, N=int(P.shape[0]), wmse=wmse, dAIC=dAIC,
                   flags=flag_at_bounds(params), **{k: float(params[k]) for k in PO})
        return row, P, D, Y, w, params
    finally:
        ff.CONFIG.clear(); ff.CONFIG.update(saved)
        try: os.remove(src)
        except OSError: pass


def print_side_by_side(rows):
    print(f"\n{'='*84}\n  SIDE BY SIDE  (no exclusion, T1-T3, D0 day-bins)\n{'='*84}")
    keys = ["N", "A_t", "k_Lt", "k_Ft", "A_d", "k_Ld", "k_Fd", "wmse", "dAIC", "flags"]
    fmt  = {"N": "{:>10,.0f}", "A_t": "{:>10.3f}", "k_Lt": "{:>10.4f}",
            "k_Ft": "{:>10.5f}", "A_d": "{:>10.3f}", "k_Ld": "{:>10.3f}",
            "k_Fd": "{:>10.4f}", "wmse": "{:>10.4f}", "dAIC": "{:>10.0f}"}
    print(f"  {'param':7s}" + "".join(f"{r['label']:>18s}" for r in rows))
    print("  " + "-" * (7 + 18 * len(rows)))
    for k in keys:
        cells = []
        for r in rows:
            v = r.get(k, np.nan)
            if k == "flags":
                cells.append(f"{str(v):>18s}")
            elif isinstance(v, float) and np.isnan(v):
                cells.append(f"{'n/a':>18s}")
            else:
                cells.append(("  " + fmt[k].format(v)).rjust(18))
        print(f"  {k:7s}" + "".join(cells))
    print("\n  WMSE is NOT comparable across columns (different data). Compare A_t/k_Lt"
          "\n  (well-identified) and watch A_d / k_Ld / k_Ft and the flags. A jump in A_t"
          "\n  on the merged column is a red flag to investigate, not a finding.")


# ───────────────────────── STEP 6: bootstrap stability ─────────────────────────
def bootstrap_draws(P, D, Y, w, params, label, n_boot=200, seed=7, kft_floor=None):
    """User-level bootstrap that mirrors engine.plot_bootstrap_cis's refit path
       (single start at the point estimate, maxiter=300). k_Ft lower bound is
       kft_floor (defaults to the engine TC floor 0.001; set 1e-6 to let it run
       free and see how often it collapses). Returns (n_boot, 6) in PARAM_ORDER."""
    if kft_floor is None:
        kft_floor = ff.CONFIG["k_Ft_lower_bound_tc"]
    rng = np.random.default_rng(seed); n = P.shape[0]
    b6 = [(1e-6, 0.99), (kft_floor, 0.99), (1e-6, 0.99),
          (1e-6, 0.99), (0.0, 30.0), (0.0, ff.CONFIG["A_d_ceiling"])]
    x0 = [params[p] for p in PO]
    draws = np.full((n_boot, 6), np.nan)
    print(f"\n  bootstrapping [{label}]  B={n_boot}  (k_Ft floor={kft_floor:g}) …")
    for b in range(n_boot):
        idx = rng.integers(0, n, n)
        r = ff._fit(x0, P[idx], D[idx], Y[idx], w[idx], b6, maxiter=300)
        if r.success:
            draws[b] = r.x
        if (b + 1) % max(1, n_boot // 5) == 0:
            print(f"    [{label}] {b+1}/{n_boot}")
    return draws


def _ci(col):
    col = col[~np.isnan(col)]
    lo, hi = np.percentile(col, [2.5, 97.5])
    return lo, hi, hi - lo


def stability_report(draws_a, params_a, draws_m, params_m, out="merged_stability_bootstrap.png"):
    print(f"\n{'='*84}\n  STEP 6  bootstrap stability: original vs merged\n{'='*84}")
    watch = {"A_d", "k_Ld", "k_Ft"}
    print(f"  {'param':6s}  {'alone est':>10} {'alone CIw':>10}  "
          f"{'merged est':>11} {'merged CIw':>11}   {'CIw change':>10}")
    print("  " + "-" * 74)
    for i, nm in enumerate(PO):
        la, ha, wa = _ci(draws_a[:, i])
        lm, hm, wm = _ci(draws_m[:, i])
        chg = (wm - wa) / wa * 100 if wa > 0 else np.nan
        tag = "  <-- watch" if nm in watch else ""
        arrow = "narrower" if wm < wa else "wider"
        print(f"  {nm:6s}  {params_a[nm]:>10.4g} {wa:>10.4g}  "
              f"{params_m[nm]:>11.4g} {wm:>11.4g}   {chg:>+9.0f}% {arrow}{tag}")

    # A_d flat-ridge signal: fraction of draws pinned at the ceiling
    def frac_ceiling(draws):
        c = draws[:, PO.index("A_d")]; c = c[~np.isnan(c)]
        return 100 * np.mean(c >= 0.95 * A_D_CEIL) if len(c) else np.nan
    fa, fm = frac_ceiling(draws_a), frac_ceiling(draws_m)
    if max(fa, fm) < 2:
        verdict = "A_d identified in BOTH arms — no ceiling ridge here; judge on CI width, not pinning"
    elif fm < fa:
        verdict = "ridge weakening (merged pins less)"
    else:
        verdict = "ridge unchanged/worse"
    print(f"\n  A_d draws pinned at ceiling ({0.95*A_D_CEIL:.0f}+):  "
          f"alone {fa:.0f}%   merged {fm:.0f}%   ({verdict})")

    # k_Ft: how often does the free bootstrap collapse toward zero? (only meaningful
    # if the bootstrap floor was lowered to ~1e-6; with the 0.001 floor it can't.)
    def frac_collapse(draws, thr=1e-4):
        c = draws[:, PO.index("k_Ft")]; c = c[~np.isnan(c)]
        return 100 * np.mean(c <= thr) if len(c) else np.nan
    ca_k, cm_k = frac_collapse(draws_a), frac_collapse(draws_m)
    kmin_a = np.nanmin(draws_a[:, PO.index("k_Ft")])
    kmin_m = np.nanmin(draws_m[:, PO.index("k_Ft")])
    print(f"  k_Ft draws below 1e-4 (collapsed toward 0):  alone {ca_k:.0f}%   merged {cm_k:.0f}%"
          f"   (min draw: alone {kmin_a:.1e}, merged {kmin_m:.1e})")
    print("  Reading: k_Ft is UNIDENTIFIED (flat profile likelihood). The point fit not")
    print("  hitting the TC floor means the free optimum lands in a plausible slow-forget")
    print("  region — reassuring — but its CI is wide, so it is bounded/plausible, NOT")
    print("  measured. If A_d/k_Ld CIs narrow and A_d ceiling-pinning drops, the same-day")
    print("  data broke the A_d–k_Ld ridge. A_t/k_Lt should stay tight in both columns.")

    # overlaid figure
    names = PO
    fig, axes = plt.subplots(2, 3, figsize=(15, 8)); axes = axes.flatten()
    for i, (nm, ax) in enumerate(zip(names, axes)):
        ca = draws_a[:, i][~np.isnan(draws_a[:, i])]
        cm = draws_m[:, i][~np.isnan(draws_m[:, i])]
        lo = min(ca.min(), cm.min()); hi = max(ca.max(), cm.max())
        bins = np.linspace(lo, hi, 34)
        ax.hist(ca, bins=bins, color="#9aa0a6", alpha=0.55, edgecolor="white",
                label="original", density=True)
        ax.hist(cm, bins=bins, color="#2a9d8f", alpha=0.55, edgecolor="white",
                label="merged", density=True)
        ax.axvline(params_a[nm], color="#4d5156", lw=2)
        ax.axvline(params_m[nm], color="#1d6f63", lw=2, ls="--")
        _, _, wa = _ci(draws_a[:, i]); _, _, wm = _ci(draws_m[:, i])
        title = f"{nm}\nCIw {wa:.3g} → {wm:.3g}"
        ax.set_title(title, fontsize=10,
                     fontweight="bold", color=("firebrick" if nm in watch else "black"))
        ax.grid(alpha=0.3)
        if i == 0:
            ax.legend(fontsize=8)
    fig.suptitle("Bootstrap parameter distributions — original vs merged "
                 "(density; dashed = merged point est.)", fontsize=13, fontweight="bold")
    plt.tight_layout()
    plt.savefig(out, dpi=ff.CONFIG.get("dpi", 150), bbox_inches="tight"); plt.close()
    print(f"\n  saved {out}")


# ───────────────────────── min_tests survival flag ─────────────────────────
def min_tests_flag(newsubset_path, chain_lengths, min_tests=3, max_test=3):
    print(f"\n{'='*72}\n  FLAG (a): chain window — min_tests={min_tests}, up to T{max_test}\n{'='*72}")
    n_in  = int((chain_lengths >= min_tests).sum())
    n_out = int(((chain_lengths >= 2) & (chain_lengths < min_tests)).sum())
    print(f"  composite participants, same-battery chain length >= {min_tests} : {n_in:,}  (ENTER)")
    print(f"  composite participants, 2 <= chain length < {min_tests}      : {n_out:,}  (excluded at this threshold)")
    print(f"  -> at min_tests={min_tests} you keep {n_in:,} of {n_in+n_out:,} chained (>=2) composite participants."
          + ("  Most same-day signal is in the length-2 pairs." if min_tests > 2 else
             "  Length-2 pairs (incl. same-day retakes) ARE included."))
    try:
        raw = _clean_cols(pd.read_csv(newsubset_path))
        raw["nth_test"] = pd.to_numeric(raw["nth_test"], errors="coerce")
        raw = raw[raw["nth_test"] <= max_test]
        mx = raw.groupby("user_id")["nth_test"].max()
        added = int(((mx >= 2) & (mx < 3)).sum())
        print(f"  original users with exactly 2 tests          : {added:,}  "
              f"({'INCLUDED at min_tests=2' if min_tests<=2 else 'excluded at min_tests>=3'})")
    except Exception as e:
        print(f"  (could not count original 2-test users: {e})")


# ───────────────────────── main ─────────────────────────
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="newsubset.csv")
    ap.add_argument("--nicole", required=True)
    ap.add_argument("--min-tests", type=int, default=3)
    ap.add_argument("--max-test", type=int, default=3)
    ap.add_argument("--min-valid-subtests", type=int, default=3)
    ap.add_argument("--uid-prefix", default="NIC_")
    ap.add_argument("--save-nicole", default="out/nicole_model_ready.csv")
    ap.add_argument("--save-merged", default="out/merged_for_fit.csv")
    ap.add_argument("--nboot", type=int, default=200)
    ap.add_argument("--boot-kft-floor", type=float, default=None,
                    help="k_Ft lower bound in the bootstrap (default engine TC floor 0.001; "
                         "set 1e-6 to let it run free and see how often it collapses).")
    ap.add_argument("--no-bootstrap", action="store_true")
    ap.add_argument("--day-edges", default="-1,0.5,90,180,9999",
                    help="comma-sep day-bin edges for weighting. Default keeps the same-day "
                         "D0 split then 0-90/90-180/180+. alternative buckets: '-1,0.5,60,150,9999'.")
    ap.add_argument("--day-labels", default=None,
                    help="comma-sep labels (len = #edges-1). If omitted, auto-derived from edges.")
    ap.add_argument("--tag", default="",
                    help="suffix for all output files, so runs don't overwrite each other "
                         "(e.g. --tag base_90_180 vs --tag new_60_150).")
    args = ap.parse_args()

    # parse day bins (+ auto labels), tag outputs
    day_edges = [float(x) for x in args.day_edges.split(",")]
    if args.day_labels:
        day_lbls = args.day_labels.split(",")
    else:
        day_lbls = _auto_day_labels(day_edges)
    if len(day_lbls) != len(day_edges) - 1:
        sys.exit(f"day-labels ({len(day_lbls)}) must be one fewer than day-edges ({len(day_edges)}).")
    print(f"\n  DAY BUCKETS: edges={day_edges}  labels={day_lbls}")
    sfx = f"_{args.tag}" if args.tag else ""
    save_nicole = args.save_nicole.replace(".csv", f"{sfx}.csv")
    save_merged = args.save_merged.replace(".csv", f"{sfx}.csv")
    summary_csv = f"merge_refit_summary{sfx}.csv"
    boot_png    = f"merged_stability_bootstrap{sfx}.png"

    if not os.path.exists(args.data):   sys.exit(f"newsubset not found: {args.data}")
    if not os.path.exists(args.nicole): sys.exit(f"composite extract not found: {args.nicole}")

    run = build_composite(args.nicole, args.min_valid_subtests)
    chains, lengths = build_chains(run)

    newsub = _clean_cols(pd.read_csv(args.data))
    print(f"\n{'='*72}\n  same-battery enforcement on the ORIGINAL\n{'='*72}")
    newsub = enforce_same_battery(newsub, "original")

    nic = to_newsubset_schema(chains, list(newsub.columns), args.uid_prefix)
    nic.to_csv(save_nicole, index=False)
    print(f"  wrote {save_nicole}")

    newsub_m = newsub.copy()
    newsub_m["user_id"] = newsub_m["user_id"].astype(str)
    merged = pd.concat([newsub_m, nic], ignore_index=True)
    merged.to_csv(save_merged, index=False)
    print(f"  wrote {save_merged}  (N_rows={len(merged):,})")

    min_tests_flag(args.data, lengths, args.min_tests, args.max_test)

    # short-vs-long chain imbalance 
    print(f"\n{'='*72}\n  CHAIN COMPOSITION (short-vs-long balance)\n{'='*72}")
    chain_composition(newsub_m, "original", args.min_tests, args.max_test)
    chain_composition(merged,   "merged",   args.min_tests, args.max_test)

    row_a, Pa, Da, Ya, wa, pa = fit_spec(newsub, "original", args.min_tests,
                                         args.max_test, day_edges, day_lbls)
    row_m, Pm, Dm, Ym, wm, pm = fit_spec(merged, "merged", args.min_tests,
                                         args.max_test, day_edges, day_lbls)
    print_side_by_side([row_a, row_m])
    pd.DataFrame([row_a, row_m]).to_csv(summary_csv, index=False)
    print(f"\n  wrote {summary_csv}")

    if not args.no_bootstrap:
        da = bootstrap_draws(Pa, Da, Ya, wa, pa, "alone",  args.nboot, seed=7,
                             kft_floor=args.boot_kft_floor)
        dm = bootstrap_draws(Pm, Dm, Ym, wm, pm, "merged", args.nboot, seed=7,
                             kft_floor=args.boot_kft_floor)
        stability_report(da, pa, dm, pm, out=boot_png)


# legacy name, used by archived scripts
build_nicole_composite = build_composite


if __name__ == "__main__":
    main()
