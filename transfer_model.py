"""
transfer_model.py - engine for the two-state model of NCPT composite-score change.

Two latent states, each with a ceiling, a learning rate and a forgetting rate:
  retest effect (SD)  A_d, k_Ld, k_Fd   gained once per NCPT administration, decays by day
  transfer (ST)       A_t, k_Lt, k_Ft   gained from gameplays, decays by day
Predicted change from the first administration = SD + ST.
Parameter order throughout: [k_Lt, k_Ft, k_Ld, k_Fd, A_t, A_d].

Core used by the v17 analysis: advance_interval, simulate_matrix, wmse_matrix, _fit,
half_life, prepare_data, compute_user_weights, df_to_matrices, CONFIG, PARAM_ORDER.
The remaining functions (multi-start optimizer, profile and bootstrap helpers, plotting
functions, main()) come from earlier versions; their printed and figure text uses older terms.
"""
from __future__ import annotations

import argparse
import warnings
from typing import Dict, List, Optional, Tuple

import matplotlib
matplotlib.use("Agg")                       # headless-safe; we only save PNGs
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd
import seaborn as sns
from scipy.optimize import minimize, OptimizeResult

warnings.filterwarnings("ignore")


# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════
CONFIG: Dict = {
    # ── I/O ──────────────────────────────────────────────────────────────────
    "data_file": "newsubset.csv",
    "save_dir":  ".",

    # ── Data filters ───────────────────────────────────────────────────────────
    "min_tests":            3,
    "max_t1_plays":        25,
    "max_plays_interval": 1000,
    "max_days_interval":   730,
    "max_plays_per_day":    20,
    # If True, winsorise offending intervals to the ceilings instead of dropping
    # the whole user (sensitivity option; default False = original behaviour).
    "winsorize_outliers": False,

    # ── Weighting ──────────────────────────────────────────────────────────────
    "max_weight": 5.0,
    "play_bin_edges":  [-1, 50, 400, 9_999],
    "play_bin_labels": ["P0-50", "P51-400", "P400+"],

    # ── Optimiser ──────────────────────────────────────────────────────────────
    "rng_seed":   42,
    "maxiter":    10_000,
    "ftol":       1e-13,
    "gtol":       1e-9,
    # Parameter order throughout: [k_Lt, k_Ft, k_Ld, k_Fd, A_t, A_d]
    "x0_smart": [0.0028, 0.0012, 0.59, 0.001, 4.9, 2.2],
    "bounds_unconstrained": [
        (1e-6, 0.99), (1e-6, 0.99), (1e-6, 0.99),
        (1e-6, 0.99), (0.0, 30.0), (0.0, 30.0),
    ],

    # ── k_Ft identifiability / theoretical constraint ──────────────────────────
    "k_Ft_diagnostic_value": 0.001,    # ~1.9-yr HL probe start
    "k_Ft_floor_trigger":    0.0001,   # trigger TC if unconstrained k_Ft < this
    "k_Ft_lower_bound_tc":   0.0010,   # TC lower bound (~1.90-yr HL)
    "kFt_profile_grid":      None,     # set in code; np.geomspace(1e-6, 2e-2, 16)

    # ── Heavy diagnostics ───────────────────────────────────────────────────────
    "run_heavy_diagnostics": True,
    "n_boot":  200,                    # bootstrap resamples for parameter CIs
    "n_folds": 5,                      # CV folds for out-of-sample calibration

    # ── Cohorts (CONFIG-driven, consistent across figures) ──────────────────────
    # Each: (label, lo_plays, hi_plays, description, color). hi=None => open top.
    "cohort_scheme": [
        ("A",   0,   50, "≤50 games (Control)",     "#e63946"),
        ("B",  51,  200, "51–200 games (Light)",    "#f4a261"),
        ("C", 201,  500, "201–500 games (Moderate)", "#2a9d8f"),
        ("D", 501, None, "≥501 games (Heavy)",      "#264653"),
    ],
    # The two-cohort figures (viz1/viz2) use the extreme cohorts of the scheme:
    "cohort_low":  50,     # ≤ this  = low-dose cohort
    "cohort_high": 501,    # ≥ this  = high-dose cohort   (matches cohort D)
    "max_test":      5,
    "dpi":         150,

    # ── viz3 assessment overlay (illustrative) ──────────────────────────────────
    # Days on which an NCPT is (hypothetically) re-administered, producing a
    # transient direct-familiarity spike. Set to [] to disable (then Total = ST).
    "assessment_days": [0, 91, 182, 273, 364],
}
CONFIG["kFt_profile_grid"] = np.geomspace(1e-6, 2e-2, 16)

PARAM_ORDER = ["k_Lt", "k_Ft", "k_Ld", "k_Fd", "A_t", "A_d"]

# Upper bound for A_d in refits/bootstrap. The direct ceiling is not identified
# by a ~5-test window; a high bound lets the bootstrap REVEAL that (A_d drifts to
# the bound) rather than hiding it behind an artificially tight cap at 30.
CONFIG["A_d_ceiling"] = 100.0


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 1 — SCALAR MECHANISTIC ENGINE  (used by the figures)
# ═══════════════════════════════════════════════════════════════════════════════
def advance_interval(SD, ST, D, P, k_Ld, k_Fd, k_Lt, k_Ft, A_d, A_t):
    """Advance Direct (SD) and Transfer (ST) skill through one interval.

    Direct: instantaneous test-familiarity dose at the start, then D-day decay.
    Transfer: geometric closed form for uniform daily play across the interval.
    Both clamped to [0, asymptote].
    """
    D = max(float(D), 1.0)

    # Direct
    SD_dosed = max(0.0, SD + k_Ld * max(0.0, A_d - SD))
    SD_end   = max(0.0, min(SD_dosed * (1.0 - k_Fd) ** D, A_d))

    # Transfer
    if P <= 0:
        ST_end = max(0.0, ST * (1.0 - k_Ft) ** D)
    else:
        gpd = P / D
        g   = 1.0 - (1.0 - k_Lt) ** gpd
        # FIX: floor r at a small POSITIVE value. A negative r raised to a
        # fractional D yields nan/complex; flooring is behaviourally correct
        # (over-saturation pins ST at A_t via the clamp below).
        r   = float(np.clip(1.0 - g - k_Ft, 1e-9, 1.0 - 1e-12))
        if abs(1.0 - r) < 1e-9:
            ST_end = ST + D * (g * A_t - (g + k_Ft) * ST)
        else:
            r_D    = r ** D
            ST_end = ST * r_D + g * A_t * (1.0 - r_D) / (1.0 - r)
        ST_end = max(0.0, min(float(ST_end), A_t))

    return SD_end, ST_end


def simulate_user(plays_arr, days_arr, k_Lt, k_Ft, k_Ld, k_Fd, A_t, A_d):
    """Predicted score-delta trajectory for one user (scalar reference engine)."""
    SD = ST = 0.0
    out = np.empty(len(plays_arr))
    for i in range(len(plays_arr)):
        SD, ST = advance_interval(SD, ST, days_arr[i], plays_arr[i],
                                  k_Ld, k_Fd, k_Lt, k_Ft, A_d, A_t)
        out[i] = SD + ST
    return out


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 2 — VECTORISED ENGINE  (used for fitting, profiling, bootstrap, CV)
#   Validated to machine precision against the scalar engine in main().
# ═══════════════════════════════════════════════════════════════════════════════
def simulate_matrix(plays: np.ndarray, days: np.ndarray, x) -> np.ndarray:
    """Vectorised SD+ST prediction. plays/days: (n_users, n_int); nan = empty."""
    k_Lt, k_Ft, k_Ld, k_Fd, A_t, A_d = x
    n_u, n_i = plays.shape
    valid = ~np.isnan(plays)
    P = np.where(valid, plays, 0.0)
    D = np.where(valid, np.maximum(days, 1.0), 1.0)

    SD = np.zeros(n_u)
    ST = np.zeros(n_u)
    out = np.full((n_u, n_i), np.nan)
    for i in range(n_i):
        Pi, Di = P[:, i], D[:, i]
        SD_dosed = np.maximum(0.0, SD + k_Ld * np.maximum(0.0, A_d - SD))
        SD_new   = np.clip(SD_dosed * (1.0 - k_Fd) ** Di, 0.0, A_d)

        gpd = np.where(Di > 0, Pi / Di, 0.0)
        g   = 1.0 - (1.0 - k_Lt) ** gpd
        r   = np.clip(1.0 - g - k_Ft, 1e-9, 1.0 - 1e-12)
        omr = np.where(np.abs(1.0 - r) < 1e-9, 1e-9, 1.0 - r)
        rD  = r ** Di
        ST_geo  = ST * rD + g * A_t * (1.0 - rD) / omr
        ST_lin  = ST + Di * (g * A_t - (g + k_Ft) * ST)
        ST_play = np.where(np.abs(1.0 - r) < 1e-9, ST_lin, ST_geo)
        ST_rest = ST * (1.0 - k_Ft) ** Di
        ST_new  = np.clip(np.where(Pi > 0, ST_play, ST_rest), 0.0, A_t)

        SD, ST = SD_new, ST_new
        out[:, i] = np.where(valid[:, i], SD + ST, np.nan)
    return out


def wmse_matrix(x, plays, days, deltas, w) -> float:
    """Weighted MSE identical to the scalar weighted_mse (per-user mean SE)."""
    preds = simulate_matrix(plays, days, x)
    valid = ~np.isnan(deltas)
    se = np.where(valid, (deltas - preds) ** 2, 0.0)
    per_user = se.sum(axis=1) / np.maximum(valid.sum(axis=1), 1)
    return float((w * per_user).sum() / max(w.sum(), 1e-12))


# Type alias + scalar WMSE retained for the heatmap / API compatibility
RecordList = List[Tuple[np.ndarray, np.ndarray, np.ndarray, float]]


def weighted_mse(x: List[float], records: RecordList) -> float:
    """Scalar reference WMSE (kept for compatibility / validation)."""
    k_Lt, k_Ft, k_Ld, k_Fd, A_t, A_d = x
    total_wse = total_w = 0.0
    for plays_arr, days_arr, deltas_arr, w in records:
        preds = simulate_user(plays_arr, days_arr,
                              k_Lt, k_Ft, k_Ld, k_Fd, A_t, A_d)
        total_wse += w * float(np.mean((deltas_arr - preds) ** 2))
        total_w   += w
    return total_wse / max(total_w, 1e-12)


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 3 — DATA PREPARATION  (transparent per-filter counts; winsorise option)
# ═══════════════════════════════════════════════════════════════════════════════
def prepare_data(filepath: str = "newsubset.csv") -> pd.DataFrame:
    print(f"\n{'═'*62}")
    print(f"  DATA PREPARATION  ←  {filepath}")
    print(f"{'═'*62}")

    df = pd.read_csv(filepath)
    df.columns = [c.replace('\ufeff', '') for c in df.columns]
    required = ["user_id", "nth_test", "normed_score",
                "num_plays_before", "days_since_signup"]
    for c in required:
        if c not in df.columns:
            raise ValueError(f"Missing required column: '{c}'")
    for col in ["days_since_signup", "num_plays_before", "normed_score"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df.dropna(subset=required, inplace=True)
    df = df.sort_values(["user_id", "nth_test"]).reset_index(drop=True)

    df["plays_interval"] = (df.groupby("user_id")["num_plays_before"]
                              .diff().fillna(0).clip(lower=0))
    df["days_interval"]  = (df.groupby("user_id")["days_since_signup"]
                              .diff().fillna(0).clip(lower=0))

    n0 = df["user_id"].nunique()
    print(f"  Raw users (≥1 test, non-null)  : {n0:>8,}")

    # Filter 1: minimum test count
    max_nth = df.groupby("user_id")["nth_test"].max()
    keep1   = max_nth[max_nth >= CONFIG["min_tests"]].index
    df = df[df["user_id"].isin(keep1)].copy()
    n1 = df["user_id"].nunique()
    print(f"  After ≥{CONFIG['min_tests']}-test filter         : "
          f"{n1:>8,} users  (−{n0-n1:,})")

    # Filter 2: naive at T1
    t1_plays = df[df["nth_test"] == 1].set_index("user_id")["num_plays_before"]
    keep2    = t1_plays[t1_plays <= CONFIG["max_t1_plays"]].index
    df = df[df["user_id"].isin(keep2)].copy()
    n2 = df["user_id"].nunique()
    note = "  (NON-BINDING on this subset)" if n2 == n1 else ""
    print(f"  After ≤{CONFIG['max_t1_plays']} plays at T1         : "
          f"{n2:>8,} users  (−{n1-n2:,}){note}")

    # Filter 3: outliers — drop user OR winsorise offending intervals
    days_safe = df["days_interval"].replace(0, np.nan)
    bad = (
        (df["plays_interval"] > CONFIG["max_plays_interval"]) |
        (df["days_interval"]  > CONFIG["max_days_interval"])  |
        (df["plays_interval"] / days_safe > CONFIG["max_plays_per_day"])
    )
    if CONFIG["winsorize_outliers"]:
        df.loc[df["plays_interval"] > CONFIG["max_plays_interval"],
               "plays_interval"] = CONFIG["max_plays_interval"]
        df.loc[df["days_interval"] > CONFIG["max_days_interval"],
               "days_interval"]  = CONFIG["max_days_interval"]
        ratio = df["plays_interval"] / df["days_interval"].replace(0, np.nan)
        cap_mask = ratio > CONFIG["max_plays_per_day"]
        df.loc[cap_mask, "plays_interval"] = (
            CONFIG["max_plays_per_day"] * df.loc[cap_mask, "days_interval"])
        n3 = df["user_id"].nunique()
        print(f"  After outlier WINSORISE       : "
              f"{n3:>8,} users  (kept; {int(bad.sum()):,} intervals capped)")
    else:
        drop_uids = df.loc[bad, "user_id"].unique()
        df = df[~df["user_id"].isin(drop_uids)].copy()
        n3 = df["user_id"].nunique()
        print(f"  After outlier exclusion       : "
              f"{n3:>8,} users  (−{n2-n3:,}, {100*(n2-n3)/max(n2,1):.1f}% dropped)")

    # T1 centring
    t1_scores = (df[df["nth_test"] == 1]
                 .set_index("user_id")["normed_score"].rename("t1_score"))
    df = df.join(t1_scores, on="user_id")
    df["score_delta"] = df["normed_score"] - df["t1_score"]

    # ── Empirical T2 reference (two SEPARATE, clearly-labelled quantities) ──────
    lo, hi = CONFIG["cohort_low"], CONFIG["cohort_high"]
    t2  = df[df["nth_test"] == 2]
    cA  = t2[t2["plays_interval"] <= lo]["score_delta"]
    cB  = t2[t2["plays_interval"] >= hi]["score_delta"]
    print(f"\n  EMPIRICAL T2 REFERENCE")
    print(f"  Low-dose  (≤{lo}  plays T1→T2): mean Δ = {cA.mean():+.3f}  (n={len(cA):,})")
    print(f"  High-dose (≥{hi} plays T1→T2): mean Δ = {cB.mean():+.3f}  (n={len(cB):,})")
    if cB.mean() != 0:
        print(f"  One-retest non-gameplay share : "
              f"{cA.mean()/cB.mean()*100:.1f}%")
        print(f"    (low-dose Δ as % of high-dose Δ AFTER ONE RETEST; this is a")
        print(f"     lower bound on the non-gameplay component, NOT the asymptotic share)")
    return df


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 4 — HISTOGRAM + FIXED CLINICAL BINS
# ═══════════════════════════════════════════════════════════════════════════════
def plot_days_histogram_and_get_bins(df, n_day_bins=4, n_play_bins=3):
    """Save T1→T2 interval distributions; return fixed clinical bin edges.

    Day edges are fixed at [0, 90, 180, 9999]. (The earlier 0/60/90 split made
    the D0-60 cell so sparse it always hit the weight cap; merging 0–90 fixes
    that without discarding users.)
    """
    t2_rows  = df[df["nth_test"] == 2]
    t2_days  = t2_rows["days_interval"].dropna()
    t2_plays = t2_rows["plays_interval"].dropna()

    FIXED_DAY_EDGES = [0.0, 90.0, 180.0, 9_999.0]
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    ax = axes[0]
    ax.hist(t2_days, bins=80, color="steelblue", edgecolor="white", alpha=0.85)
    ax.set_xlabel("Days between T1 and T2", fontsize=12)
    ax.set_ylabel("Number of users", fontsize=12)
    ax.set_title("Distribution of T1→T2 Interval (Days)", fontsize=13, fontweight="bold")
    ax.grid(True, alpha=0.3)
    for edge in FIXED_DAY_EDGES[1:-1]:
        ax.axvline(edge, color="firebrick", linestyle="--", lw=1.5, label=f"cut {edge:.0f}d")
    ax.legend(fontsize=8, title="Clinical bin edges (fixed)")
    pct = pd.Series(t2_days).describe(percentiles=[.25, .5, .75, .9, .95])
    stat = "\n".join([f"p{int(p*100):>3}: {v:.0f}d" for p, v in
                      zip([.25, .5, .75, .9, .95],
                          pct[["25%", "50%", "75%", "90%", "95%"]])])
    ax.text(0.97, 0.97, stat, transform=ax.transAxes, fontsize=8, va="top",
            ha="right", bbox=dict(boxstyle="round", facecolor="white", alpha=0.8))

    ax2 = axes[1]
    ax2.hist(t2_plays.clip(upper=600), bins=60, color="coral",
             edgecolor="white", alpha=0.85)
    ax2.set_xlabel("Games played T1→T2  (clipped at 600)", fontsize=12)
    ax2.set_ylabel("Number of users", fontsize=12)
    ax2.set_title("Distribution of T1→T2 Interval (Plays)", fontsize=13, fontweight="bold")
    ax2.grid(True, alpha=0.3)
    plt.suptitle("T1→T2 Interval Distributions  —  used to set propensity bins",
                 fontsize=13, fontweight="bold")
    plt.tight_layout()
    path = f"{CONFIG['save_dir']}/hist_days_t1_t2.png"
    plt.savefig(path, dpi=CONFIG["dpi"], bbox_inches="tight"); plt.close()
    print(f"\n  Histogram saved: {path}")

    day_bins = FIXED_DAY_EDGES
    day_lbls = []
    for i in range(len(FIXED_DAY_EDGES) - 1):
        lo = int(FIXED_DAY_EDGES[i]); hi = FIXED_DAY_EDGES[i + 1]
        day_lbls.append(f"D{lo}+" if hi >= 9_000 else f"D{lo}-{int(hi)}")
    play_bins = CONFIG["play_bin_edges"]; play_lbls = CONFIG["play_bin_labels"]
    print(f"\n  FIXED CLINICAL BIN EDGES")
    print(f"  Play bins : {play_bins}  → {play_lbls}")
    print(f"  Day bins  : {day_bins}  → {day_lbls}")
    print(f"  Joint bins: {len(play_lbls)} × {len(day_lbls)} = {len(play_lbls)*len(day_lbls)}")
    return play_bins, play_lbls, day_bins, day_lbls


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 5 — 2D FREQUENCY REWEIGHTING  (per-user weights)
# ═══════════════════════════════════════════════════════════════════════════════
def compute_user_weights(df, play_bins, play_lbls, day_bins, day_lbls):
    """Return (user_weight Series, uid_to_bin Series) and print the bin table.

    Weights are inverse joint-cell frequency at T1→T2, capped at max_weight.
    (This is descriptive frequency reweighting across a 2D stratification — it is
    NOT IPW for a causal estimand; see Discussion caveats.)
    """
    t2 = df[df["nth_test"] == 2][["user_id", "plays_interval", "days_interval"]].copy()
    t2["play_bin"] = pd.cut(t2["plays_interval"], bins=play_bins, labels=play_lbls)
    t2["day_bin"]  = pd.cut(t2["days_interval"],  bins=day_bins,  labels=day_lbls)
    t2["joint"]    = t2["play_bin"].astype(str) + "__" + t2["day_bin"].astype(str)
    uid_to_bin = t2.set_index("user_id")["joint"]

    counts  = uid_to_bin.value_counts()
    n_bins  = len(counts); total_u = len(uid_to_bin)
    raw     = total_u / (n_bins * counts)
    capped  = raw.clip(upper=CONFIG["max_weight"])
    print(f"\n  2D FREQUENCY-REWEIGHT BINS  ({n_bins} populated buckets)")
    print(f"  {'Bin':38s}  {'N':>7}  {'Raw w':>8}  {'Cap w':>8}")
    print(f"  {'─'*66}")
    for b in counts.index:
        print(f"  {b:38s}  {counts[b]:>7,}  {raw[b]:>8.3f}  {capped[b]:>8.3f}")

    user_weight = pd.Series(
        {u: float(capped.get(uid_to_bin.get(u), 1.0)) for u in df["user_id"].unique()})
    return user_weight, uid_to_bin


def df_to_matrices(df, user_weight=None):
    """Padded (n_users, n_int) matrices for T≥2 intervals + aligned weights.

    Returns uids, P, D, Y, w, t2_plays  (t2_plays = P[:,0] for cohort assignment).
    """
    sub = df[df["nth_test"] >= 2].sort_values(["user_id", "nth_test"])
    uids = sub["user_id"].unique()
    n_int = int(sub.groupby("user_id").size().max())
    P = np.full((len(uids), n_int), np.nan)
    D = np.full((len(uids), n_int), np.nan)
    Y = np.full((len(uids), n_int), np.nan)
    pos = {u: k for k, u in enumerate(uids)}
    counter = {u: 0 for u in uids}
    for uid, pl, dy, sd in zip(sub["user_id"], sub["plays_interval"],
                               sub["days_interval"], sub["score_delta"]):
        k = pos[uid]; j = counter[uid]
        P[k, j] = pl; D[k, j] = dy; Y[k, j] = sd; counter[uid] += 1
    if user_weight is None:
        w = np.ones(len(uids))
    else:
        w = np.array([float(user_weight.get(u, 1.0)) for u in uids])
    return uids, P, D, Y, w, P[:, 0].copy()


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 6 — UTILITIES
# ═══════════════════════════════════════════════════════════════════════════════
def half_life(k_F):
    return np.log(0.5) / np.log(max(1.0 - k_F, 1e-14))


def _fit(x0, P, D, Y, w, bounds, maxiter=None):
    return minimize(wmse_matrix, x0, args=(P, D, Y, w), method="L-BFGS-B",
                    bounds=bounds, options={"maxiter": maxiter or CONFIG["maxiter"],
                                            "ftol": CONFIG["ftol"], "gtol": CONFIG["gtol"]})


def _print_params(label, res):
    k_Lt, k_Ft, k_Ld, k_Fd, A_t, A_d = res.x
    hl_t, hl_d = half_life(k_Ft), half_life(k_Fd)
    print(f"\n  ┌─ {label} {'─'*(47-len(label))}┐")
    print(f"  │  WMSE = {res.fun:.6f}   converged = {res.success}")
    print(f"  ├─ Transfer ──────────────────────────────────────────┤")
    print(f"  │  k_Lt (learning)  = {k_Lt:.6f}")
    print(f"  │  k_Ft (forgetting)= {k_Ft:.6f}   HL = {hl_t:>8.1f} d  ({hl_t/365.25:.2f} yr)")
    print(f"  │  A_t  (asymptote) = {A_t:.4f}")
    print(f"  ├─ Direct ────────────────────────────────────────────┤")
    print(f"  │  k_Ld (learning)  = {k_Ld:.6f}")
    print(f"  │  k_Fd (forgetting)= {k_Fd:.6f}   HL = {hl_d:>8.1f} d  ({hl_d/365.25:.2f} yr)")
    print(f"  │  A_d  (asymptote) = {A_d:.4f}")
    print(f"  │  Asymptotic direct share A_d/(A_t+A_d) = "
          f"{A_d/max(A_t+A_d,1e-9)*100:.1f}%")
    print(f"  │    (share AFTER many retests; distinct from the one-retest T2 ratio)")
    print(f"  └─────────────────────────────────────────────────────┘")


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 7 — OPTIMISATION  (multi-start + profile-likelihood + TC fallback)
# ═══════════════════════════════════════════════════════════════════════════════
def run_optimization(P, D, Y, w):
    bounds = CONFIG["bounds_unconstrained"]; x0s = CONFIG["x0_smart"]
    print(f"\n{'═'*62}\n  OPTIMISATION  —  full dataset, L-BFGS-B (vectorised)\n{'═'*62}")
    print(f"  Users: {P.shape[0]:,}")

    print("\n  ── Phase 1: Smart Start ──────────────────────────────")
    res_A = _fit(x0s, P, D, Y, w, bounds)
    print(f"  WMSE = {res_A.fun:.6f}   converged = {res_A.success}")

    print("\n  ── Phase 2: Multi-Start (±20%) ───────────────────────")
    best_B = None
    for i, mult in enumerate([1.0, 1.2, 0.8]):
        x0 = [float(np.clip(v*mult, lo, hi)) for v, (lo, hi) in zip(x0s, bounds)]
        res = _fit(x0, P, D, Y, w, bounds)
        tag = "✓ best" if (best_B is None or res.fun < best_B.fun) else ""
        print(f"  Start {i+1}/3: WMSE = {res.fun:.6f}   conv={res.success}  {tag}")
        if best_B is None or res.fun < best_B.fun:
            best_B = res

    print("\n  ── Phase 3: Diagnostic Perturbation (k_Ft probe) ─────")
    x0d = list(x0s); x0d[1] = CONFIG["k_Ft_diagnostic_value"]
    x0d = [float(np.clip(v, lo, hi)) for v, (lo, hi) in zip(x0d, bounds)]
    res_diag = _fit(x0d, P, D, Y, w, bounds)
    print(f"    Start k_Ft = {CONFIG['k_Ft_diagnostic_value']:.4f}  →  "
          f"fitted k_Ft = {res_diag.x[1]:.2e}  (WMSE {res_diag.fun:.6f})")

    winner = min([res_A, best_B, res_diag], key=lambda r: r.fun)
    _print_params("UNCONSTRAINED WINNER", winner)
    print("\n  NOTE: k_Ft is reported below via a profile likelihood (viz9). The")
    print("  loss is flat in k_Ft across the observable window, so its value is")
    print("  set by assumption, not estimated. The TC pass fixes a plausible floor.")

    if winner.x[1] < CONFIG["k_Ft_floor_trigger"]:
        lb = CONFIG["k_Ft_lower_bound_tc"]; hl = half_life(lb)
        print(f"\n{'─'*62}")
        print(f"  ⚠  THEORETICALLY CONSTRAINED (TC) PASS TRIGGERED")
        print(f"     unconstrained k_Ft = {winner.x[1]:.2e} < floor "
              f"{CONFIG['k_Ft_floor_trigger']:.2e}")
        print(f"     k_Ft lower bound → {lb}  (HL ≥ {hl:.1f} d ≈ {hl/365.25:.2f} yr)")
        print(f"{'─'*62}")
        b_tc = [list(x) for x in bounds]; b_tc[1][0] = lb
        x0_tc = list(winner.x); x0_tc[1] = max(x0_tc[1], lb)
        res_tc = _fit(x0_tc, P, D, Y, w, [tuple(x) for x in b_tc])
        _print_params("THEORETICALLY CONSTRAINED WINNER", res_tc)
        d = res_tc.fun - winner.fun
        print(f"\n  WMSE cost of TC constraint: Δ = +{d:.5f}  "
              f"({d/winner.fun*100:.2f}%) — the price of a plausibility assumption,")
        print(f"  NOT evidence for durability (see viz9 profile likelihood).")
        final = res_tc
    else:
        print(f"\n  k_Ft above floor; TC pass not triggered.")
        final = winner

    k_Lt, k_Ft, k_Ld, k_Fd, A_t, A_d = final.x
    return dict(k_Lt=k_Lt, k_Ft=k_Ft, k_Ld=k_Ld, k_Fd=k_Fd, A_t=A_t, A_d=A_d), final


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 8 — COHORT HELPERS  (consistent assignment from CONFIG scheme)
# ═══════════════════════════════════════════════════════════════════════════════
def assign_cohort_ids(df):
    """Return dict label -> array of user_ids based on CONFIG['cohort_scheme']."""
    t2 = df[df["nth_test"] == 2].set_index("user_id")["plays_interval"]
    out = {}
    for label, lo, hi, desc, color in CONFIG["cohort_scheme"]:
        m = t2 >= lo if hi is None else (t2 >= lo) & (t2 <= hi)
        out[label] = (t2[m].index.values, desc, color)
    return out


def _predict_cohort_trajectory(sub, p, max_test=5):
    sub_t2p = sub[sub["nth_test"] > 1]
    med_plays = sub_t2p.groupby("nth_test")["plays_interval"].median()
    med_days  = sub_t2p.groupby("nth_test")["days_interval"].median()
    SD = ST = 0.0; pred = {1: 0.0}
    for nth in sorted(med_plays.index):
        if nth > max_test:
            break
        SD, ST = advance_interval(SD, ST, max(float(med_days[nth]), 1.0),
                                  float(med_plays[nth]), p["k_Ld"], p["k_Fd"],
                                  p["k_Lt"], p["k_Ft"], p["A_d"], p["A_t"])
        pred[nth] = SD + ST
    return pred, med_plays, med_days


# ═══════════════════════════════════════════════════════════════════════════════
# VIZ 1 — actual vs predicted (2 cohorts; IN-SAMPLE cohort-median calibration)
# ═══════════════════════════════════════════════════════════════════════════════
def plot_actual_vs_predicted(df, params, low, high, max_test=5):
    t2_plays = df[df["nth_test"] == 2].set_index("user_id")["plays_interval"].rename("t2p")
    dfx = df.join(t2_plays, on="user_id")
    cA = t2_plays[t2_plays <= low].index
    cB = t2_plays[t2_plays >= high].index
    print(f"\n  Cohort A (≤{low} games): {len(cA):,}   Cohort B (≥{high} games): {len(cB):,}")
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    for ax, (label, cids, desc, color) in zip(axes, [
            ("A", cA, f"≤{low} games T1→T2", "coral"),
            ("B", cB, f"≥{high} games T1→T2", "steelblue")]):
        sub = dfx[dfx["user_id"].isin(cids) & (dfx["nth_test"] <= max_test)]
        truth = sub.groupby("nth_test")["score_delta"].agg(mean="mean", sem="sem").reset_index()
        pred, mp, md = _predict_cohort_trajectory(sub, params, max_test)
        ax.errorbar(truth["nth_test"], truth["mean"], yerr=truth["sem"]*1.96,
                    fmt="o-", color=color, lw=2, ms=6, capsize=4, label="Actual (mean ± 95% CI)")
        ax.plot(sorted(pred), [pred[t] for t in sorted(pred)], "s--", color="black",
                lw=2, ms=6, label="Model predicted")
        ax.axhline(0, color="gray", ls=":", alpha=0.5)
        info = "\n".join([f"T{n-1}→T{n}: {md[n]:.0f}d, {mp[n]:.0f}g"
                          for n in sorted(mp.index) if n <= 3])
        ax.text(0.04, 0.04, f"Median intervals:\n{info}", transform=ax.transAxes,
                fontsize=8, va="bottom", bbox=dict(boxstyle="round", facecolor="white", alpha=0.8))
        ax.set_xlabel("Test number"); ax.set_ylabel("Score delta from T1")
        ax.set_title(f"Cohort {label}: {desc}\n(n={len(cids):,})", fontsize=11)
        ax.legend(fontsize=9); ax.grid(alpha=0.3)
    fig.suptitle("Actual vs Predicted | Four Forces  (IN-SAMPLE calibration:\n"
                 "each cohort fed its own empirical median intervals — see viz10 for out-of-sample)",
                 fontsize=12, fontweight="bold")
    plt.tight_layout()
    path = f"{CONFIG['save_dir']}/viz1_actual_vs_predicted.png"
    plt.savefig(path, dpi=CONFIG["dpi"], bbox_inches="tight"); plt.close()
    print(f"  Saved: {path}")


# ═══════════════════════════════════════════════════════════════════════════════
# VIZ 2 — day sensitivity
# ═══════════════════════════════════════════════════════════════════════════════
def plot_day_sensitivity(df, params, low, high, max_test=5, day_values=None):
    t2_plays = df[df["nth_test"] == 2].set_index("user_id")["plays_interval"].rename("t2p")
    dfx = df.join(t2_plays, on="user_id")
    day_values = day_values or [30, 90, 180]
    print(f"\n  Day-sensitivity at {day_values} days")
    cA = t2_plays[t2_plays <= low].index; cB = t2_plays[t2_plays >= high].index
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    dcols = ["#2196F3", "#4CAF50", "#FF5722"]; dls = ["-.", "-", "--"]
    for ax, (cids, desc, base) in zip(axes,
            [(cA, f"Cohort A: ≤{low} games", "coral"),
             (cB, f"Cohort B: ≥{high} games", "steelblue")]):
        sub = dfx[dfx["user_id"].isin(cids) & (dfx["nth_test"] <= max_test)]
        truth = sub.groupby("nth_test")["score_delta"].agg(mean="mean", sem="sem").reset_index()
        ax.errorbar(truth["nth_test"], truth["mean"], yerr=truth["sem"]*1.96,
                    fmt="o", color=base, lw=2.5, ms=7, capsize=4, zorder=5, label="Actual data")
        mp = sub[sub["nth_test"] > 1].groupby("nth_test")["plays_interval"].median()
        for dval, dc, dl in zip(day_values, dcols, dls):
            SD = ST = 0.0; pred = {1: 0.0}
            for nth in sorted(mp.index):
                if nth > max_test:
                    break
                SD, ST = advance_interval(SD, ST, float(dval), float(mp[nth]),
                                          params["k_Ld"], params["k_Fd"], params["k_Lt"],
                                          params["k_Ft"], params["A_d"], params["A_t"])
                pred[nth] = SD + ST
            ax.plot(sorted(pred), [pred[t] for t in sorted(pred)], ls=dl, color=dc,
                    lw=2, ms=5, marker="s", label=f"Model @ {dval}d")
        ax.axhline(0, color="gray", ls=":", alpha=0.5)
        ax.set_xlabel("Test number"); ax.set_ylabel("Score delta from T1")
        ax.set_title(f"{desc}\n(n={len(cids):,})", fontsize=11)
        ax.legend(fontsize=9); ax.grid(alpha=0.3)
    fig.suptitle(f"Day-Sensitivity Check — Model at {'/'.join(str(d) for d in day_values)}d",
                 fontsize=12, fontweight="bold")
    plt.tight_layout()
    path = f"{CONFIG['save_dir']}/viz2_day_sensitivity.png"
    plt.savefig(path, dpi=CONFIG["dpi"], bbox_inches="tight"); plt.close()
    print(f"  Saved: {path}")


# ═══════════════════════════════════════════════════════════════════════════════
# VIZ 3 — 365-day simulation (transfer-skill AUC; honest SD handling)
# ═══════════════════════════════════════════════════════════════════════════════
def simulate_vector(daily_games, params, assessment_days=None):
    """Daily SD/ST histories. SD is dosed ONLY on assessment_days (an NCPT sit);
    under pure home play SD stays 0. Returns (history_SD, history_ST)."""
    N = len(daily_games)
    aset = set(int(d) for d in (assessment_days or []))
    k_Lt, k_Ft, k_Ld, k_Fd, A_t, A_d = (params[k] for k in
                                         ["k_Lt", "k_Ft", "k_Ld", "k_Fd", "A_t", "A_d"])
    SD = ST = 0.0; hSD = np.empty(N); hST = np.empty(N)
    for t in range(N):
        if t in aset:                                   # NCPT administered today
            SD = max(0.0, SD + k_Ld * max(0.0, A_d - SD))
        SD = float(np.clip(SD * (1.0 - k_Fd), 0.0, A_d))
        g_today = float(daily_games[t])
        if g_today <= 0:
            ST = float(np.clip(ST * (1.0 - k_Ft), 0.0, A_t))
        else:
            g = 1.0 - (1.0 - k_Lt) ** g_today
            r = float(np.clip(1.0 - g - k_Ft, 1e-9, 1.0 - 1e-12))
            ST = float(np.clip(ST * r + g * A_t, 0.0, A_t))
        hSD[t] = SD; hST[t] = ST
    return hSD, hST


def _neg_auc_ST(x, params):
    _, hST = simulate_vector(x, params, assessment_days=None)   # gameplay benefit only
    return -float(np.sum(hST))


def _blocks(n_days, n_blocks):
    """Return block lengths (in days) that partition n_days into ~equal blocks."""
    base = n_days // n_blocks
    rem  = n_days - base * n_blocks
    lens = np.full(n_blocks, base, dtype=int)
    lens[:rem] += 1
    return lens


def optimise_schedule_auc(params, total_games=1000, n_days=365, max_per_day=10.0,
                          n_blocks=36):
    """Maximise transfer-skill AUC over a PIECEWISE-CONSTANT daily schedule.

    Optimising n_blocks (~10-day) block rates instead of 365 individual days is
    far faster for SLSQP and yields a clinically cleaner schedule (you don't
    prescribe a different game count every single day). The block solution is
    expanded back to a 365-day vector for simulation/plotting.
    """
    print(f"\n  AUC optimisation (transfer-skill ST): {n_days}d, budget={total_games}, "
          f"max={max_per_day}/day, {n_blocks} blocks …")
    lens = _blocks(n_days, n_blocks)

    def expand(z):
        return np.repeat(z, lens)

    def neg_auc(z):
        return _neg_auc_ST(expand(z), params)

    z0 = np.full(n_blocks, total_games / n_days)
    bounds = [(0.0, max_per_day)] * n_blocks
    cons = [{"type": "eq", "fun": lambda z: float(np.dot(z, lens) - total_games),
             "jac": lambda z: lens.astype(float)}]
    res = minimize(neg_auc, z0, method="SLSQP", bounds=bounds, constraints=cons,
                   options={"maxiter": 500, "ftol": 1e-9})
    daily = np.clip(expand(res.x), 0.0, max_per_day)
    print(f"  {'converged' if res.success else 'stopped'}: "
          f"ST-AUC={-res.fun:.2f}, total games={daily.sum():.1f}")
    return daily


def plot_clinical_simulation(params):
    print("\n  Generating viz3: 365-day simulation + AUC opt…")
    N, TOT, MX = 365, 1000, 10.0
    consistent = np.full(N, np.clip(TOT / N, 0, MX))
    front = np.zeros(N); front[:100] = MX
    opt = optimise_schedule_auc(params, TOT, N, MX)
    ad = CONFIG["assessment_days"]
    schedules = [("Consistent (2.74 g/day)", consistent, "#2a9d8f"),
                 ("Front-Loaded (10 g/day ×100d)", front, "#e63946"),
                 ("AUC-Optimised (SLSQP)", opt, "#457b9d")]
    days = np.arange(N)
    fig = plt.figure(figsize=(14, 8))
    ax = fig.add_axes([0.07, 0.32, 0.88, 0.60]); axg = fig.add_axes([0.07, 0.07, 0.88, 0.20])
    rows = []
    for label, vec, color in schedules:
        hSD, hST = simulate_vector(vec, params, assessment_days=ad)
        auc = float(np.sum(hST))
        ax.plot(days, hST, color=color, lw=2.5, label=f"{label}  [ST-AUC={auc:.0f}]")
        if ad:   # show transient familiarity spikes only if assessments simulated
            ax.plot(days, hSD + hST, color=color, lw=1.0, alpha=0.45, ls=":")
        ax.annotate(f"ST={hST[-1]:.2f}", xy=(N-1, hST[-1]), xytext=(N+2, hST[-1]),
                    fontsize=8, color=color, va="center")
        rows.append((label, auc, hST[-1]))
    title = ("365-Day Simulation — Transfer Skill (ST) under three schedules\n"
             "Solid = ST (durable gameplay benefit). ")
    title += ("Dotted = ST + transient test-familiarity IF NCPT re-administered "
              f"on days {ad}." if ad else
              "Home play confers NO test-familiarity, so SD≡0 and Total≡ST.")
    ax.set_title(title, fontsize=11, fontweight="bold")
    ax.set_ylabel("Predicted Score Δ from Baseline"); ax.set_xlim(0, N + 20)
    ax.xaxis.set_major_locator(mticker.MultipleLocator(30)); ax.tick_params(labelbottom=False)
    ax.legend(fontsize=8, loc="upper left"); ax.grid(alpha=0.3)
    axm = ax.twiny(); axm.set_xlim(ax.get_xlim())
    axm.set_xticks([30*m for m in range(13)]); axm.set_xticklabels([f"M{m}" for m in range(13)], fontsize=8)
    axm.set_xlabel("Month", fontsize=9)
    for label, vec, color in schedules:
        disp = pd.Series(vec).rolling(7, center=True, min_periods=1).mean().values
        axg.plot(days, disp, color=color, lw=1.5, alpha=0.85)
    axg.set_xlim(0, N + 20); axg.set_xlabel("Day of Trial"); axg.set_ylabel("Games/Day\n(7-day avg)", fontsize=9)
    axg.xaxis.set_major_locator(mticker.MultipleLocator(30)); axg.grid(alpha=0.3); axg.set_ylim(bottom=0)
    axg.text(0.5, 0.9, "NB: the optimiser's end-of-year taper is a finite-horizon artifact "
             "(late games have ~0 marginal AUC), not a clinical recommendation.",
             transform=axg.transAxes, fontsize=7.5, ha="center", va="top",
             bbox=dict(boxstyle="round", facecolor="#fff3cd", alpha=0.85))
    print(f"\n  {'Schedule':32s}  {'ST-AUC':>8}  {'Final ST':>9}")
    for label, auc, fst in rows:
        print(f"  {label:32s}  {auc:>8.1f}  {fst:>9.3f}")
    path = f"{CONFIG['save_dir']}/viz3_clinical_simulation.png"
    plt.savefig(path, dpi=CONFIG["dpi"], bbox_inches="tight"); plt.close()
    print(f"  Saved: {path}")


# ═══════════════════════════════════════════════════════════════════════════════
# VIZ 5 — dose-response
# ═══════════════════════════════════════════════════════════════════════════════
def plot_dose_response(params):
    print("  Generating viz5: dose-response transfer curve…")
    doses = np.linspace(0, 1000, 200)
    gains = [advance_interval(0, 0, 90.0, d, params["k_Ld"], params["k_Fd"],
                              params["k_Lt"], params["k_Ft"], params["A_d"], params["A_t"])[1]
             for d in doses]
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(doses, gains, color="#2a9d8f", lw=3)
    ax.axhline(params["A_t"], color="gray", ls="--", alpha=0.7,
               label=f"Asymptote (A_t = {params['A_t']:.2f})")
    tgt = params["A_t"] * 0.8; idx = int(np.argmax(np.array(gains) >= tgt))
    if idx > 0:
        ax.plot(doses[idx], tgt, "ro", zorder=5)
        ax.annotate(f"80% benefit\n~{int(doses[idx])} games", xy=(doses[idx], tgt),
                    xytext=(doses[idx]+50, tgt-0.5),
                    arrowprops=dict(facecolor="black", shrink=0.05, width=1, headwidth=5))
    ax.set_title("Dose-Response: Transfer Skill over a single 90-Day window",
                 fontsize=13, fontweight="bold")
    ax.set_xlabel("Cumulative games in the window"); ax.set_ylabel("Predicted Transfer Skill (ST)")
    ax.grid(alpha=0.3); ax.legend()
    ax.text(0.97, 0.05, "Model-implied curve (uniform play, 90d). Associational:\n"
            "dose was self-selected — not an experimental dose-response.",
            transform=ax.transAxes, fontsize=8, ha="right", va="bottom",
            bbox=dict(boxstyle="round", facecolor="white", alpha=0.85))
    path = f"{CONFIG['save_dir']}/viz5_dose_response.png"
    plt.savefig(path, dpi=CONFIG["dpi"], bbox_inches="tight"); plt.close()
    print(f"  Saved: {path}")


# ═══════════════════════════════════════════════════════════════════════════════
# VIZ 6 — loss heatmap (identified pair) — kept, with a pointer to viz9
# ═══════════════════════════════════════════════════════════════════════════════
def plot_loss_landscape_heatmap(params, P, D, Y, w, grid_size=20):
    print("  Generating viz6: k_Lt × k_Ld loss heatmap…")
    kl = np.linspace(params["k_Lt"]*0.5, params["k_Lt"]*1.5, grid_size)
    kd = np.linspace(params["k_Ld"]*0.5, params["k_Ld"]*1.5, grid_size)
    grid = np.zeros((grid_size, grid_size))
    for i, a in enumerate(kl):
        for j, b in enumerate(kd):
            grid[j, i] = wmse_matrix([a, params["k_Ft"], b, params["k_Fd"],
                                      params["A_t"], params["A_d"]], P, D, Y, w)
    fig, ax = plt.subplots(figsize=(7, 6))
    c = ax.contourf(kl, kd, grid, levels=30, cmap="viridis")
    fig.colorbar(c).set_label("WMSE", rotation=270, labelpad=15)
    ax.plot(params["k_Lt"], params["k_Ld"], "r*", ms=12, label="Optimum")
    ax.set_title("Loss Landscape: the IDENTIFIED learning rates\n"
                 "(k_Ft is NOT identified — see viz9 profile likelihood)",
                 fontsize=12, fontweight="bold")
    ax.set_xlabel(f"Transfer learning k_Lt\nOptimal: {params['k_Lt']:.5f}")
    ax.set_ylabel(f"Direct learning k_Ld\nOptimal: {params['k_Ld']:.5f}")
    ax.legend(loc="upper left")
    path = f"{CONFIG['save_dir']}/viz6_parameter_heatmap.png"
    plt.savefig(path, dpi=CONFIG["dpi"], bbox_inches="tight"); plt.close()
    print(f"  Saved: {path}")


# ═══════════════════════════════════════════════════════════════════════════════
# VIZ 7 — residual diagnostics (4 panels + in-sample R²)
# ═══════════════════════════════════════════════════════════════════════════════
def plot_residuals_distribution(P, D, Y, params):
    print("  Generating viz7: residual diagnostics (4-panel)…")
    x = [params[k] for k in ["k_Lt", "k_Ft", "k_Ld", "k_Fd", "A_t", "A_d"]]
    pred = simulate_matrix(P, D, x)
    # T2 = first interval
    p2, a2, days2, plays2 = pred[:, 0], Y[:, 0], D[:, 0], P[:, 0]
    ok = ~np.isnan(p2) & ~np.isnan(a2)
    p2, a2, days2, plays2 = p2[ok], a2[ok], days2[ok], plays2[ok]
    res = a2 - p2
    r2_t2 = 1 - np.sum(res**2)/np.sum((a2 - a2.mean())**2)
    # all-interval R²
    okall = ~np.isnan(pred) & ~np.isnan(Y)
    ra, rp = Y[okall], pred[okall]
    r2_all = 1 - np.sum((ra-rp)**2)/np.sum((ra-ra.mean())**2)

    fig, ax = plt.subplots(2, 2, figsize=(13, 9))
    sns.histplot(res, bins=50, kde=True, color="mediumpurple", edgecolor="white", ax=ax[0, 0])
    ax[0, 0].axvline(0, color="black", ls="--", lw=2)
    ax[0, 0].set_title("Residuals at T2", fontweight="bold")
    ax[0, 0].set_xlabel("Actual − Predicted Δ"); ax[0, 0].set_ylabel("Users")
    ax[0, 0].text(0.97, 0.95, f"Mean: {res.mean():.3f}\nSD: {res.std():.3f}\n"
                  f"MAE: {np.abs(res).mean():.3f}\nR²(T2): {r2_t2:.3f}\nR²(all): {r2_all:.3f}",
                  transform=ax[0, 0].transAxes, fontsize=9, va="top", ha="right",
                  bbox=dict(boxstyle="round", facecolor="white", alpha=0.85))
    for axi, xv, xl in [(ax[0, 1], p2, "Predicted Δ"),
                        (ax[1, 0], days2, "Interval length (days)"),
                        (ax[1, 1], plays2, "Games in interval")]:
        axi.scatter(xv, res, s=6, alpha=0.12, color="#457b9d", rasterized=True)
        axi.axhline(0, color="black", ls="--", lw=1)
        # binned mean residual
        try:
            qs = np.quantile(xv, np.linspace(0, 1, 9)); qs[-1] += 1e-6
            idx = np.digitize(xv, qs) - 1
            bx = [xv[idx == b].mean() for b in range(8) if (idx == b).sum() > 5]
            by = [res[idx == b].mean() for b in range(8) if (idx == b).sum() > 5]
            axi.plot(bx, by, "o-", color="#e63946", lw=2, ms=6)
        except Exception:
            pass
        axi.set_title(f"Residual vs {xl}", fontweight="bold")
        axi.set_xlabel(xl); axi.set_ylabel("Residual"); axi.grid(alpha=0.3)
    fig.suptitle("Residual Diagnostics at T2 (in-sample)", fontsize=13, fontweight="bold")
    plt.tight_layout()
    path = f"{CONFIG['save_dir']}/viz7_residuals.png"
    plt.savefig(path, dpi=CONFIG["dpi"], bbox_inches="tight"); plt.close()
    print(f"  Saved: {path}  | in-sample R²(T2)={r2_t2:.3f} R²(all)={r2_all:.3f}")


# ═══════════════════════════════════════════════════════════════════════════════
# VIZ 8 — 4-panel actual vs predicted (full spectrum; CONFIG cohorts)
# ═══════════════════════════════════════════════════════════════════════════════
def plot_actual_vs_predicted_4panel(df, params, max_test=5):
    print("  Generating viz8: 4-panel spectrum (in-sample cohort medians)…")
    cohorts = assign_cohort_ids(df)
    t2_plays = df[df["nth_test"] == 2].set_index("user_id")["plays_interval"].rename("t2p")
    dfx = df.join(t2_plays, on="user_id")
    fig, axes = plt.subplots(2, 2, figsize=(14, 10), sharey=True, sharex=True)
    axes = axes.flatten()
    for ax, (label, lo, hi, desc, color) in zip(axes, CONFIG["cohort_scheme"]):
        cids, _, _ = cohorts[label]
        sub = dfx[dfx["user_id"].isin(cids) & (dfx["nth_test"] <= max_test)]
        truth = sub.groupby("nth_test")["score_delta"].agg(mean="mean", sem="sem").reset_index()
        ax.errorbar(truth["nth_test"], truth["mean"], yerr=truth["sem"]*1.96,
                    fmt="o-", color=color, lw=2.5, ms=7, capsize=4, label="Actual (mean ± 95% CI)")
        pred, mp, md = _predict_cohort_trajectory(sub, params, max_test)
        ax.plot(sorted(pred), [pred[t] for t in sorted(pred)], "s--", color="black",
                lw=2, ms=6, label="Model predicted")
        ax.axhline(0, color="gray", ls=":", alpha=0.5)
        ax.set_title(f"Cohort {label}: {desc}\n(n={len(cids):,})", fontsize=11, fontweight="bold")
        ax.grid(alpha=0.3)
        if label in ["A", "B"]:
            ax.legend(fontsize=9)
        info = [f"T{n-1}→T{n}: {md.get(n,0):.0f}d, {mp.get(n,0):.0f}g"
                for n in range(2, max_test+1) if n in mp.index]
        ax.text(0.04, 0.04, "Cohort medians:\n" + "\n".join(info), transform=ax.transAxes,
                fontsize=7.5, va="bottom", bbox=dict(boxstyle="round", facecolor="white", alpha=0.8))
    for ax in axes[2:]:
        ax.set_xlabel("Test number")
    for ax in [axes[0], axes[2]]:
        ax.set_ylabel("Score delta from T1")
    fig.suptitle("Actual vs Predicted Across Gameplay Spectrum (IN-SAMPLE; cohort medians)",
                 fontsize=13, fontweight="bold", y=0.98)
    plt.tight_layout()
    path = f"{CONFIG['save_dir']}/viz8_actual_vs_predicted_4panel.png"
    plt.savefig(path, dpi=CONFIG["dpi"], bbox_inches="tight"); plt.close()
    print(f"  Saved: {path}")


# ═══════════════════════════════════════════════════════════════════════════════
# VIZ 9 — PROFILE LIKELIHOOD of k_Ft  (identifiability)
# ═══════════════════════════════════════════════════════════════════════════════
def plot_kFt_profile(P, D, Y, w, params):
    print("  Generating viz9: k_Ft profile likelihood…")
    grid = CONFIG["kFt_profile_grid"]
    b5 = [(1e-6, 0.99), (1e-6, 0.99), (1e-6, 0.99), (0.0, 30.0), (0.0, CONFIG["A_d_ceiling"])]
    x0 = [params["k_Lt"], params["k_Ld"], params["k_Fd"], params["A_t"], params["A_d"]]
    prof = []
    for kft in grid:
        f = lambda v: wmse_matrix([v[0], kft, v[1], v[2], v[3], v[4]], P, D, Y, w)
        r = minimize(f, x0, method="L-BFGS-B", bounds=b5, options={"maxiter": 400, "ftol": 1e-12})
        prof.append(r.fun); x0 = list(r.x)
    prof = np.array(grid, dtype=float) * 0 + prof  # ensure array
    prof = np.array(prof)
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.semilogx(grid, prof, "o-", color="#264653", lw=2, ms=6)
    ax.axvline(CONFIG["k_Ft_lower_bound_tc"], color="firebrick", ls="--", lw=1.8,
               label=f"TC floor (k_Ft={CONFIG['k_Ft_lower_bound_tc']}, "
                     f"HL≈{half_life(CONFIG['k_Ft_lower_bound_tc'])/365.25:.1f} yr)")
    ax.axhspan(prof.min(), prof.min() + 0.0001*max(prof.min(), 1), color="gray", alpha=0.15,
               label="±0.01% of min WMSE (practically flat)")
    obs = np.nanmax(D)
    left = prof[grid <= CONFIG["k_Ft_lower_bound_tc"]]
    ax.set_title("Profile Likelihood of Transfer-Forgetting k_Ft\n"
                 "(other 5 parameters re-optimised at each grid point)",
                 fontsize=12, fontweight="bold")
    ax.set_xlabel("k_Ft (per-day transfer forgetting)"); ax.set_ylabel("Best attainable WMSE")
    ax.grid(alpha=0.3, which="both"); ax.legend(fontsize=9, loc="upper left")
    ax.text(0.5, 0.04, f"WMSE varies by only {left.max()-left.min():.4f} across "
            f"k_Ft=1e-6→{CONFIG['k_Ft_lower_bound_tc']:g}\n(half-lives ~1898 yr → "
            f"~{half_life(CONFIG['k_Ft_lower_bound_tc'])/365.25:.1f} yr fit equally well). "
            f"Max observed interval = {obs:.0f} d.",
            transform=ax.transAxes, fontsize=8.5, ha="center", va="bottom",
            bbox=dict(boxstyle="round", facecolor="#fff3cd", alpha=0.9))
    path = f"{CONFIG['save_dir']}/viz9_kFt_profile.png"
    plt.savefig(path, dpi=CONFIG["dpi"], bbox_inches="tight"); plt.close()
    print(f"  Saved: {path}  | flat-left WMSE span = {left.max()-left.min():.5f}")


# ═══════════════════════════════════════════════════════════════════════════════
# VIZ 10 — k-fold OUT-OF-SAMPLE calibration at T2
# ═══════════════════════════════════════════════════════════════════════════════
def plot_kfold_calibration(P, D, Y, w, params, k=5, seed=0):
    print(f"  Generating viz10: {k}-fold out-of-sample calibration…")
    rng = np.random.default_rng(seed); n = P.shape[0]; fold = rng.integers(0, k, n)
    b6 = [(1e-6, 0.99), (CONFIG["k_Ft_lower_bound_tc"], 0.99), (1e-6, 0.99),
          (1e-6, 0.99), (0.0, 30.0), (0.0, CONFIG["A_d_ceiling"])]
    x0 = [params[p] for p in ["k_Lt", "k_Ft", "k_Ld", "k_Fd", "A_t", "A_d"]]
    pr, ac = [], []
    for fi in range(k):
        tr, te = fold != fi, fold == fi
        r = _fit(x0, P[tr], D[tr], Y[tr], w[tr], b6, maxiter=400)
        preds = simulate_matrix(P[te], D[te], r.x)
        pr.append(preds[:, 0]); ac.append(Y[te][:, 0])
    pr = np.concatenate(pr); ac = np.concatenate(ac)
    ok = ~np.isnan(pr) & ~np.isnan(ac); pr, ac = pr[ok], ac[ok]
    r2 = 1 - np.sum((ac-pr)**2)/np.sum((ac-ac.mean())**2); mae = np.abs(ac-pr).mean()
    qs = np.quantile(pr, np.linspace(0, 1, 11)); qs[-1] += 1e-6; idx = np.digitize(pr, qs) - 1
    bx, by, ci = [], [], []
    for b in range(10):
        m = idx == b
        if m.sum() < 5:
            continue
        bx.append(pr[m].mean()); by.append(ac[m].mean())
        ci.append(1.96*ac[m].std(ddof=1)/np.sqrt(m.sum()))
    fig, ax = plt.subplots(figsize=(7.5, 6.5))
    lim = [min(pr.min(), ac.min())-1, np.quantile(ac, 0.99)+1]
    ax.plot(lim, lim, "k--", lw=1.5, label="Perfect calibration (y=x)")
    ax.scatter(pr, ac, s=6, alpha=0.10, color="#457b9d", rasterized=True)
    ax.errorbar(bx, by, yerr=[ci, ci], fmt="o-", color="#e63946", lw=2, ms=7, capsize=4,
                label="Binned mean actual (decile) ± 95% CI")
    ax.set_xlim(lim); ax.set_ylim(lim)
    ax.set_title(f"Out-of-Sample Calibration at T2 ({k}-fold over users)\n"
                 "honest analogue of in-sample cohort-median traces", fontsize=12, fontweight="bold")
    ax.set_xlabel("Predicted T2 Δ (held-out)"); ax.set_ylabel("Actual T2 Δ")
    ax.grid(alpha=0.3); ax.legend(fontsize=9, loc="upper left")
    ax.text(0.97, 0.05, f"Out-of-sample\nR² = {r2:.3f}\nMAE = {mae:.2f}\nN = {len(pr):,}",
            transform=ax.transAxes, fontsize=10, ha="right", va="bottom",
            bbox=dict(boxstyle="round", facecolor="white", alpha=0.85))
    path = f"{CONFIG['save_dir']}/viz10_calibration.png"
    plt.savefig(path, dpi=CONFIG["dpi"], bbox_inches="tight"); plt.close()
    print(f"  Saved: {path}  | out-of-sample R²={r2:.3f} MAE={mae:.2f}")


# ═══════════════════════════════════════════════════════════════════════════════
# VIZ 11 — bootstrap parameter CIs
# ═══════════════════════════════════════════════════════════════════════════════
def plot_bootstrap_cis(P, D, Y, w, params, n_boot=200, seed=7):
    print(f"  Generating viz11: bootstrap parameter CIs (B={n_boot})…")
    rng = np.random.default_rng(seed); n = P.shape[0]
    b6 = [(1e-6, 0.99), (CONFIG["k_Ft_lower_bound_tc"], 0.99), (1e-6, 0.99),
          (1e-6, 0.99), (0.0, 30.0), (0.0, CONFIG["A_d_ceiling"])]
    x0 = [params[p] for p in ["k_Lt", "k_Ft", "k_Ld", "k_Fd", "A_t", "A_d"]]
    draws = np.full((n_boot, 6), np.nan)
    for b in range(n_boot):
        idx = rng.integers(0, n, n)
        r = _fit(x0, P[idx], D[idx], Y[idx], w[idx], b6, maxiter=300)
        if r.success:
            draws[b] = r.x
        if (b+1) % max(1, n_boot//5) == 0:
            print(f"    bootstrap {b+1}/{n_boot}")
    names = ["k_Lt", "k_Ft", "k_Ld", "k_Fd", "A_t", "A_d"]
    fig, axes = plt.subplots(2, 3, figsize=(14, 8)); axes = axes.flatten()
    print(f"\n  {'Param':6s}  {'Estimate':>10}  {'2.5%':>10}  {'97.5%':>10}")
    for i, (nm, ax) in enumerate(zip(names, axes)):
        col = draws[:, i]; col = col[~np.isnan(col)]
        lo, hi = np.percentile(col, [2.5, 97.5]); est = x0[i]
        ax.hist(col, bins=30, color="#457b9d", alpha=0.8, edgecolor="white")
        ax.axvline(est, color="black", lw=2, label="point est.")
        ax.axvline(lo, color="firebrick", ls="--", lw=1.5)
        ax.axvline(hi, color="firebrick", ls="--", lw=1.5)
        ax.set_title(f"{nm}: {est:.4g}\n[{lo:.4g}, {hi:.4g}]", fontsize=10, fontweight="bold")
        ax.grid(alpha=0.3)
        if nm == "k_Ft":
            ax.set_title(f"{nm}: {est:.4g}  [{lo:.4g}, {hi:.4g}]\n(floored — UNIDENTIFIED)",
                         fontsize=9, fontweight="bold", color="firebrick")
        print(f"  {nm:6s}  {est:>10.5f}  {lo:>10.5f}  {hi:>10.5f}")
    fig.suptitle("Bootstrap Parameter Distributions (resampled over users)",
                 fontsize=13, fontweight="bold")
    plt.tight_layout()
    path = f"{CONFIG['save_dir']}/viz11_bootstrap_cis.png"
    plt.savefig(path, dpi=CONFIG["dpi"], bbox_inches="tight"); plt.close()
    print(f"  Saved: {path}")


# ═══════════════════════════════════════════════════════════════════════════════
# VIZ 12 — regression-to-the-mean diagnostic
# ═══════════════════════════════════════════════════════════════════════════════
def plot_regression_to_mean(df):
    print("  Generating viz12: regression-to-the-mean diagnostic…")
    t1 = df[df["nth_test"] == 1].set_index("user_id")["t1_score"]
    t2 = df[df["nth_test"] == 2].set_index("user_id")["score_delta"]
    j = pd.concat([t1.rename("t1"), t2.rename("d2")], axis=1).dropna()
    if len(j) < 50:
        print("  (too few users for RTM diagnostic; skipped)"); return
    r = np.corrcoef(j["t1"], j["d2"])[0, 1]
    j["dec"] = pd.qcut(j["t1"], 10, labels=False, duplicates="drop")
    g = j.groupby("dec")["d2"].agg(["mean", "sem", "count"]).reset_index()
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.errorbar(g["dec"]+1, g["mean"], yerr=g["sem"]*1.96, fmt="o-", color="#6a4c93",
                lw=2, ms=7, capsize=4)
    ax.axhline(0, color="gray", ls=":")
    ax.set_title("Regression-to-the-Mean Check\nT2 gain by T1 baseline decile",
                 fontsize=12, fontweight="bold")
    ax.set_xlabel("T1 baseline score decile (1=lowest)"); ax.set_ylabel("Mean T2 score delta")
    ax.grid(alpha=0.3)
    ax.text(0.97, 0.95, f"corr(T1, ΔT2) = {r:+.3f}\nA strong negative slope indicates\n"
            "RTM inflating low-baseline gains.", transform=ax.transAxes, fontsize=9,
            va="top", ha="right", bbox=dict(boxstyle="round", facecolor="white", alpha=0.85))
    path = f"{CONFIG['save_dir']}/viz12_regression_to_mean.png"
    plt.savefig(path, dpi=CONFIG["dpi"], bbox_inches="tight"); plt.close()
    print(f"  Saved: {path}  | corr(T1, ΔT2) = {r:+.3f}")


# ═══════════════════════════════════════════════════════════════════════════════
# SELF-CHECK
# ═══════════════════════════════════════════════════════════════════════════════
def engine_selfcheck(df, params):
    sub = df[df["nth_test"] >= 2].sort_values(["user_id", "nth_test"])
    x = [params[k] for k in ["k_Lt", "k_Ft", "k_Ld", "k_Fd", "A_t", "A_d"]]
    err = 0.0
    for uid in sub["user_id"].unique()[:8]:
        g = sub[sub["user_id"] == uid]
        scal = simulate_user(g["plays_interval"].values.astype(float),
                             g["days_interval"].values.astype(float), *x)
        vec = simulate_matrix(g["plays_interval"].values[None, :].astype(float),
                              g["days_interval"].values[None, :].astype(float), x)[0, :len(scal)]
        err = max(err, float(np.nanmax(np.abs(scal - vec))))
    return err


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════
KFT_BAND = {
    "fitted (near-0, ~1898 yr)": 1e-6,
    "TC floor (~1.9 yr)":        0.0010,
    "conservative (~1 yr)":      np.log(2) / 365.0,     # ~0.00190
    "aggressive (~6 mo)":        np.log(2) / 182.0,     # ~0.00381
}


# ════════════════════════════════════════════════════════════════════════════
# MAINTENANCE EQUILIBRIUM  (closed form; validated against simulation)
# ════════════════════════════════════════════════════════════════════════════
def maintenance_equilibrium(g_per_day, k_Lt, k_Ft, A_t):
    """Steady-state transfer skill ST* sustained by a constant g games/day.

    Daily map: ST -> ST*r + g_eff*A_t,  g_eff = 1-(1-k_Lt)**g,  r = 1-g_eff-k_Ft.
    Fixed point: ST* = g_eff*A_t / (g_eff + k_Ft).
    """
    g_eff = 1.0 - (1.0 - k_Lt) ** np.asarray(g_per_day, float)
    return g_eff * A_t / (g_eff + k_Ft)


def dose_for_fraction(frac, k_Lt, k_Ft, A_t, g_hi=50.0):
    """Games/day needed to sustain `frac` of A_t (root-find on the closed form)."""
    target = frac * A_t
    lo, hi = 0.0, g_hi
    if maintenance_equilibrium(hi, k_Lt, k_Ft, A_t) < target:
        return np.inf
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        if maintenance_equilibrium(mid, k_Lt, k_Ft, A_t) < target:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


# ════════════════════════════════════════════════════════════════════════════
# A) MAINTENANCE DOSE-RESPONSE  (battery figure, as a k_Ft band)
# ════════════════════════════════════════════════════════════════════════════
def viz_maintenance(params, minutes_per_game=4.0):
    """% of transfer asymptote sustained vs games/day, banded over k_Ft.

    minutes_per_game: used only for the secondary "minutes/day" axis and the
    '5 min or less' annotation (Lumosity sessions ~ a few minutes; adjust freely).
    """
    print("  Generating maintenance dose-response (battery figure)…")
    g = np.linspace(0, 6, 400)
    fig, ax = plt.subplots(figsize=(9, 5.5))

    # band across k_Ft (fastest forgetting = lower curve = MORE dose needed)
    kfts = sorted(KFT_BAND.values())
    lo_curve = maintenance_equilibrium(g, params["k_Lt"], max(kfts), params["A_t"]) / params["A_t"] * 100
    hi_curve = maintenance_equilibrium(g, params["k_Lt"], min(kfts), params["A_t"]) / params["A_t"] * 100
    ax.fill_between(g, lo_curve, hi_curve, color="#2a9d8f", alpha=0.18,
                    label="Range across k_Ft (1898 yr … 6 mo half-life)")

    # individual labelled curves
    styles = ["-", "--", "-.", ":"]
    for (lab, kft), ls in zip(KFT_BAND.items(), styles):
        frac = maintenance_equilibrium(g, params["k_Lt"], kft, params["A_t"]) / params["A_t"] * 100
        ax.plot(g, frac, ls, color="#264653", lw=2, label=f"k_Ft {lab}")

    # primary "1 game/day" marker at the conservative rate
    kft_cons = KFT_BAND["conservative (~1 yr)"]
    for gg in [1.0, 1.3]:
        f1 = maintenance_equilibrium(gg, params["k_Lt"], kft_cons, params["A_t"]) / params["A_t"] * 100
        ax.plot(gg, f1, "o", color="#e63946", ms=8, zorder=6)
        ax.annotate(f"{gg:g} game/day → {f1:.0f}% (≈{gg*minutes_per_game:.0f} min)",
                    xy=(gg, f1), xytext=(gg + 0.4, f1 - 12), fontsize=9,
                    arrowprops=dict(arrowstyle="->", color="#e63946"))

    ax.axhline(100, color="gray", ls=":", alpha=0.7)
    ax.set_ylim(0, 105); ax.set_xlim(0, 6)
    ax.set_xlabel("Maintenance dose (games per day)", fontsize=11)
    ax.set_ylabel("Sustained transfer skill (% of asymptote A_t)", fontsize=11)
    ax.set_title("Maintenance Dose-Response — 'Charging the Battery'\n"
                 "Steady-state transfer skill held by a constant daily dose",
                 fontsize=12, fontweight="bold")
    ax.grid(alpha=0.3); ax.legend(fontsize=8, loc="lower right")

    # secondary minutes axis
    secx = ax.secondary_xaxis("top", functions=(lambda x: x * minutes_per_game,
                                                 lambda x: x / minutes_per_game))
    secx.set_xlabel(f"≈ minutes per day  (at {minutes_per_game:g} min/game)", fontsize=9)

    ax.text(0.02, 0.04,
            "Read as a FLOOR ('this dose or less'): the curve gives the minimum\n"
            "daily play that holds each asymptote fraction. Dose needed grows as\n"
            "the forgetting rate k_Ft increases — the conservative regime is the\n"
            "demanding one, so the maintenance claim is stated against it.",
            transform=ax.transAxes, fontsize=8, va="bottom",
            bbox=dict(boxstyle="round", facecolor="#fff3cd", alpha=0.9))

    path = f"{CONFIG['save_dir']}/viz_maintenance_dose.png"
    plt.tight_layout(); plt.savefig(path, dpi=CONFIG['dpi'], bbox_inches="tight"); plt.close()
    # console summary table
    print(f"\n  MAINTENANCE TABLE (conservative k_Ft ≈ 1-yr half-life)")
    print(f"  {'games/day':>10}  {'min/day':>8}  {'% asymptote':>12}")
    for gg in [0.5, 0.75, 1.0, 1.3, 2.0, 2.74]:
        f = maintenance_equilibrium(gg, params["k_Lt"], kft_cons, params["A_t"]) / params["A_t"] * 100
        print(f"  {gg:>10.2f}  {gg*minutes_per_game:>8.1f}  {f:>11.1f}%")
    print(f"  Saved: {path}")


# ════════════════════════════════════════════════════════════════════════════
# B) k_Ft SENSITIVITY  (fit barely moves; maintenance dose moves a lot)
# ════════════════════════════════════════════════════════════════════════════
def viz_kFt_sensitivity(params, P, D, Y, w, frac=0.80):
    print("  Generating k_Ft sensitivity (supplemental)…")
    grid = np.geomspace(1e-6, 6e-3, 22)
    b5 = [(1e-6, 0.99), (1e-6, 0.99), (1e-6, 0.99), (0.0, 30.0), (0.0, CONFIG["A_d_ceiling"])]
    x0 = [params["k_Lt"], params["k_Ld"], params["k_Fd"], params["A_t"], params["A_d"]]
    wmse, dose, kLt_at, At_at = [], [], [], []
    for kft in grid:
        f = lambda v: wmse_matrix([v[0], kft, v[1], v[2], v[3], v[4]], P, D, Y, w)
        r = minimize(f, x0, method="L-BFGS-B", bounds=b5,
                     options={"maxiter": 400, "ftol": 1e-12})
        x0 = list(r.x)
        wmse.append(r.fun)
        kLt_i, At_i = r.x[0], r.x[3]
        kLt_at.append(kLt_i); At_at.append(At_i)
        dose.append(dose_for_fraction(frac, kLt_i, kft, At_i))
    wmse = np.array(wmse); dose = np.array(dose)

    fig, ax1 = plt.subplots(figsize=(9, 5.5))
    ax1.semilogx(grid, wmse, "o-", color="#264653", lw=2, ms=5, label="Best WMSE")
    ax1.set_xlabel("k_Ft  (per-day transfer forgetting)", fontsize=11)
    ax1.set_ylabel("Best attainable WMSE", color="#264653", fontsize=11)
    ax1.tick_params(axis="y", labelcolor="#264653")
    span = wmse.max() - wmse.min()
    ax1.set_ylim(wmse.min() - 0.05 * span, wmse.max() + 0.25 * span)
    ax1.grid(alpha=0.3, which="both")

    ax2 = ax1.twinx()
    ax2.semilogx(grid, dose, "s--", color="#e63946", lw=2, ms=5,
                 label=f"Dose for {int(frac*100)}% asymptote")
    ax2.set_ylabel(f"Maintenance dose for {int(frac*100)}% (games/day)",
                   color="#e63946", fontsize=11)
    ax2.tick_params(axis="y", labelcolor="#e63946")

    for lab, kft in KFT_BAND.items():
        if grid.min() <= kft <= grid.max():
            ax1.axvline(kft, color="gray", ls=":", alpha=0.6)
    ax1.set_title("k_Ft Sensitivity: fit is nearly flat, maintenance dose is not\n"
                  f"WMSE varies {span:.4f} across the grid; the dose for "
                  f"{int(frac*100)}% asymptote changes severalfold",
                  fontsize=12, fontweight="bold")
    lines = ax1.get_lines()[:1] + ax2.get_lines()[:1]
    ax1.legend(lines, [l.get_label() for l in lines], fontsize=9, loc="upper left")
    ax1.text(0.5, 0.02,
             "Takeaway for the manuscript: the data cannot pin k_Ft (left axis flat),\n"
             "so we adopt a CONSERVATIVE (faster) rate. That conservatism flows into\n"
             "the maintenance dose (right axis), which is the parameter clinicians use.",
             transform=ax1.transAxes, fontsize=8, ha="center", va="bottom",
             bbox=dict(boxstyle="round", facecolor="#fff3cd", alpha=0.9))
    path = f"{CONFIG['save_dir']}/viz_kFt_sensitivity.png"
    plt.tight_layout(); plt.savefig(path, dpi=CONFIG['dpi'], bbox_inches="tight"); plt.close()
    print(f"  WMSE span across k_Ft grid = {span:.5f}  "
          f"({span/wmse.min()*100:.3f}% of min)")
    print(f"  Saved: {path}")


# ════════════════════════════════════════════════════════════════════════════
# C) CONSTRAINED 3-PARAMETER SCHEDULE  (optimise 18 mo, display 12 mo)
# ════════════════════════════════════════════════════════════════════════════
def _daily_ST(daily_games, params):
    """Transfer-skill history under a daily-games vector (home play; no NCPT)."""
    k_Lt, k_Ft, A_t = params["k_Lt"], params["k_Ft"], params["A_t"]
    ST = 0.0; out = np.empty(len(daily_games))
    for t, gt in enumerate(daily_games):
        if gt <= 0:
            ST = ST * (1.0 - k_Ft)
        else:
            g = 1.0 - (1.0 - k_Lt) ** gt
            r = float(np.clip(1.0 - g - k_Ft, 1e-9, 1.0 - 1e-12))
            ST = ST * r + g * A_t
        ST = float(min(max(ST, 0.0), A_t))
        out[t] = ST
    return out


def _build_schedule(phase_len, intensive_rate, maint_rate, horizon, max_per_day):
    phase_len = int(np.clip(round(phase_len), 0, horizon))
    sched = np.empty(horizon)
    sched[:phase_len] = np.clip(intensive_rate, 0, max_per_day)
    sched[phase_len:] = np.clip(maint_rate, 0, max_per_day)
    return sched


def optimise_constrained_schedule(params, horizon_days, maint_floor,
                                   max_per_day=10.0, total_budget=None):
    """Optimise (phase_len, intensive_rate, maint_rate) to maximise ST-AUC over
    `horizon_days`. maint_floor sets the lower bound on the maintenance rate:
      0.0           -> pure AUC (maintenance may taper to nothing)
      >0 (auto)     -> a true holding dose (e.g. dose for 75% of asymptote)
    Optional total_budget adds an inequality cap on total games.
    """
    bounds = [(7, horizon_days), (0.0, max_per_day), (maint_floor, max_per_day)]

    def neg_auc(z):
        sched = _build_schedule(z[0], z[1], z[2], horizon_days, max_per_day)
        return -float(np.sum(_daily_ST(sched, params)))

    cons = []
    if total_budget is not None:
        def budget_ok(z):
            sched = _build_schedule(z[0], z[1], z[2], horizon_days, max_per_day)
            return total_budget - sched.sum()
        cons = [{"type": "ineq", "fun": budget_ok}]

    best = None
    for pl0 in [30, 60, 120]:                      # multi-start on phase length
        z0 = [pl0, max_per_day * 0.8, max(maint_floor, 1.0)]
        r = minimize(neg_auc, z0, method="SLSQP", bounds=bounds,
                     constraints=cons, options={"maxiter": 300, "ftol": 1e-9})
        if best is None or r.fun < best.fun:
            best = r
    pl, ir, mr = best.x
    return int(round(pl)), float(ir), float(mr), -best.fun


def viz_constrained_schedule(params, train_months=18, show_months=12,
                             max_per_day=10.0, budget_per_day=2.74):
    print(f"  Generating constrained schedule (train {train_months} mo, "
          f"show {show_months} mo)…")
    H = int(round(train_months * 30.4))
    show_days = int(round(show_months * 30.4))
    days = np.arange(H)
    # Total games budget = budget_per_day averaged over the FULL training horizon.
    # Without a budget, "maximise benefit" degenerates to "max dose every day";
    # the budget is what makes the intensive/maintenance split a real trade-off.
    total_budget = budget_per_day * H
    print(f"  Games budget: {total_budget:.0f} over {H}d "
          f"(≈{budget_per_day:g}/day average)")

    # 75%-asymptote holding dose (conservative k_Ft) for the forced-maintenance regime
    kft_cons = KFT_BAND["conservative (~1 yr)"]
    hold = dose_for_fraction(0.75, params["k_Lt"], kft_cons, params["A_t"])
    hold = float(np.clip(hold, 0.1, max_per_day))

    regimes = [
        ("Maintenance floor = 0 (pure AUC)", 0.0, "#457b9d"),
        (f"Maintenance ≥ holding dose ({hold:.1f}/day → 75% A_t)", hold, "#e76f51"),
    ]

    fig = plt.figure(figsize=(13, 8))
    ax = fig.add_axes([0.08, 0.34, 0.86, 0.58])
    axg = fig.add_axes([0.08, 0.08, 0.86, 0.20])
    print(f"\n  {'Regime':46s}  {'phase(d)':>8}  {'intens':>7}  {'maint':>6}  {'ST-AUC(18mo)':>12}")
    for label, floor, color in regimes:
        pl, ir, mr, auc = optimise_constrained_schedule(params, H, floor,
                                                         max_per_day, total_budget)
        sched = _build_schedule(pl, ir, mr, H, max_per_day)
        st = _daily_ST(sched, params)
        ax.plot(days[:show_days], st[:show_days], color=color, lw=2.5,
                label=f"{label}\n  phase={pl}d @ {ir:.1f}/day, then {mr:.1f}/day")
        # faint continuation beyond the displayed window
        ax.plot(days[show_days:], st[show_days:], color=color, lw=1.0,
                ls=":", alpha=0.45)
        axg.plot(days, sched, color=color, lw=1.8, alpha=0.85)
        print(f"  {label[:46]:46s}  {pl:>8}  {ir:>7.2f}  {mr:>6.2f}  {auc:>12.1f}")

    ax.axvline(show_days, color="gray", ls="--", alpha=0.6)
    ax.text(show_days, ax.get_ylim()[1] * 0.96, "  display horizon (12 mo)",
            fontsize=8, color="gray", va="top")
    ax.set_xlim(0, H); ax.set_ylabel("Transfer skill ST (Δ from baseline)")
    ax.set_title("Constrained 3-Parameter Schedule — optimise 18 months, display 12\n"
                 "Intensive loading phase → maintenance leg; two maintenance-floor regimes",
                 fontsize=12, fontweight="bold")
    ax.legend(fontsize=8, loc="lower right"); ax.grid(alpha=0.3)
    ax.tick_params(labelbottom=False)

    axg.axvline(show_days, color="gray", ls="--", alpha=0.6)
    axg.set_xlim(0, H); axg.set_ylim(bottom=0)
    axg.set_xlabel("Day of trial"); axg.set_ylabel("Games/day")
    axg.grid(alpha=0.3)
    axg.text(0.5, 0.92,
             "Optimising over 18 months removes the year-end drop-to-zero artifact "
             "that appears when the horizon coincides with the display window.",
             transform=axg.transAxes, fontsize=7.5, ha="center", va="top",
             bbox=dict(boxstyle="round", facecolor="#fff3cd", alpha=0.85))
    path = f"{CONFIG['save_dir']}/viz_constrained_schedule.png"
    plt.savefig(path, dpi=CONFIG['dpi'], bbox_inches="tight"); plt.close()
    print(f"  Saved: {path}")


# ════════════════════════════════════════════════════════════════════════════
# D) INCREMENTAL BOOTSTRAP  (CIs only; original fit untouched)
# ════════════════════════════════════════════════════════════════════════════
def incremental_bootstrap(params, P, D, Y, w, batch=10, batches=5,
                          k_Ft_floor=None, seed=7):
    """Resample users with replacement, refit, report stability after each batch.

    Stops early if estimates look stable (low coefficient of variation) after
    >= 2 batches; otherwise runs all batches. Specifically watches whether k_Ft
    pins to its lower bound (the identifiability tell).
    """
    if k_Ft_floor is None:
        k_Ft_floor = CONFIG["k_Ft_lower_bound_tc"]
    rng = np.random.default_rng(seed); n = P.shape[0]
    b6 = [(1e-6, 0.99), (k_Ft_floor, 0.99), (1e-6, 0.99),
          (1e-6, 0.99), (0.0, 30.0), (0.0, CONFIG["A_d_ceiling"])]
    x0 = [params[p] for p in PARAM_ORDER]
    draws: List[np.ndarray] = []
    print(f"\n  INCREMENTAL BOOTSTRAP  (batch={batch}, max batches={batches}, "
          f"k_Ft floor={k_Ft_floor:g})")
    print("  Watching k_Ft: 'pinned' = sits at the lower bound (unidentified).")
    for bi in range(batches):
        for _ in range(batch):
            idx = rng.integers(0, n, n)
            r = _fit(x0, P[idx], D[idx], Y[idx], w[idx], b6, maxiter=300)
            if r.success:
                draws.append(r.x.copy())
        arr = np.array(draws)
        pinned = np.mean(np.abs(arr[:, 1] - k_Ft_floor) < 1e-5 * max(k_Ft_floor, 1)) * 100
        print(f"\n  ── after {len(arr)} resamples ─────────────────────────────")
        print(f"  {'param':6s} {'mean':>10} {'cv%':>7} {'2.5%':>10} {'97.5%':>10}")
        cvs = []
        for i, nm in enumerate(PARAM_ORDER):
            col = arr[:, i]
            mean, sd = col.mean(), col.std()
            cv = sd / abs(mean) * 100 if mean != 0 else np.nan
            cvs.append(cv if np.isfinite(cv) else 0)
            lo, hi = np.percentile(col, [2.5, 97.5])
            star = "  ← pinned" if (nm == "k_Ft" and pinned > 80) else ""
            print(f"  {nm:6s} {mean:>10.5f} {cv:>6.1f}% {lo:>10.5f} {hi:>10.5f}{star}")
        print(f"  k_Ft pinned to bound in {pinned:.0f}% of resamples")
        # early-stop heuristic
        if len(arr) >= 2 * batch and max(c for c, nm in zip(cvs, PARAM_ORDER)
                                         if nm != "k_Ft") < 8.0:
            print(f"\n  Non-k_Ft parameters stable (all CV<8%) after {len(arr)} "
                  f"resamples — safe to scale up if you want tighter CIs.")
            break
    return np.array(draws)


def viz_bootstrap(draws, params, k_Ft_floor=None):
    if k_Ft_floor is None:
        k_Ft_floor = CONFIG["k_Ft_lower_bound_tc"]
    fig, axes = plt.subplots(2, 3, figsize=(14, 8)); axes = axes.flatten()
    x0 = [params[p] for p in PARAM_ORDER]
    for i, (nm, ax) in enumerate(zip(PARAM_ORDER, axes)):
        col = draws[:, i]
        lo, hi = np.percentile(col, [2.5, 97.5])
        ax.hist(col, bins=min(30, max(8, len(col)//4)), color="#457b9d",
                alpha=0.8, edgecolor="white")
        ax.axvline(x0[i], color="black", lw=2, label="point est.")
        ax.axvline(lo, color="firebrick", ls="--", lw=1.5)
        ax.axvline(hi, color="firebrick", ls="--", lw=1.5)
        ttl = f"{nm}: {x0[i]:.4g}\n[{lo:.4g}, {hi:.4g}]"
        col_c = "black"
        if nm == "k_Ft":
            pinned = np.mean(np.abs(col - k_Ft_floor) < 1e-5 * max(k_Ft_floor, 1)) * 100
            ttl = f"{nm}: pinned {pinned:.0f}% (UNIDENTIFIED)\n[{lo:.4g}, {hi:.4g}]"
            col_c = "firebrick"
        ax.set_title(ttl, fontsize=9.5, fontweight="bold", color=col_c)
        ax.grid(alpha=0.3)
    fig.suptitle(f"Bootstrap Parameter Distributions (B={len(draws)} resamples, "
                 "users sampled with replacement)", fontsize=13, fontweight="bold")
    plt.tight_layout()
    path = f"{CONFIG['save_dir']}/viz_bootstrap_cis.png"
    plt.savefig(path, dpi=CONFIG['dpi'], bbox_inches="tight"); plt.close()
    print(f"  Saved: {path}")




# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 14 — A_d IDENTIFIABILITY:  report what the data CAN pin
# ═══════════════════════════════════════════════════════════════════════════════
def report_direct_identifiability(df, params, P, D, Y, w, raised_bound=100.0):
    """The infinite-retest direct ceiling A_d is NOT identified by a ~5-test
    window (it runs to its upper bound). We therefore report two honest things:

      (1) A DERIVED, OBSERVABLE quantity — direct familiarity accrued by test 5
          under each cohort's own median intervals — which the data DOES pin.
      (2) A_d re-fit with a RAISED bound; if it climbs to the new bound, A_d is
          reported as a lower bound ('≥ x'), not a point estimate.

    Also computes the OBSERVABLE direct-vs-transfer split at T5 (the defensible
    replacement for the unstable asymptotic A_d/(A_t+A_d) ratio).
    """
    print(f"\n{'═'*62}\n  DIRECT-CEILING IDENTIFIABILITY\n{'═'*62}")

    # --- (1) familiarity accrued by T5 (observable) ---------------------------
    # Decompose the model prediction into SD (direct) and ST (transfer) at each
    # test, using the pooled median intervals actually seen in the data.
    sub = df[df["nth_test"] > 1]
    med_p = sub.groupby("nth_test")["plays_interval"].median()
    med_d = sub.groupby("nth_test")["days_interval"].median()
    SD = ST = 0.0
    rows = []
    for nth in sorted(med_p.index):
        if nth > CONFIG["max_test"]:
            break
        SD, ST = advance_interval(SD, ST, max(float(med_d[nth]), 1.0),
                                  float(med_p[nth]), params["k_Ld"], params["k_Fd"],
                                  params["k_Lt"], params["k_Ft"], params["A_d"], params["A_t"])
        rows.append((nth, SD, ST))
    nthN, SDN, STN = rows[-1]
    print(f"  Observable decomposition at T{nthN} (pooled median intervals):")
    print(f"    Direct (familiarity) SD  = {SDN:.3f}")
    print(f"    Transfer (gameplay)  ST  = {STN:.3f}")
    print(f"    Observable direct share  = {SDN/max(SDN+STN,1e-9)*100:.1f}%  "
          f"(at T{nthN}; this is what the data supports, NOT the asymptotic ratio)")

    # --- (2) raised-bound refit ----------------------------------------------
    bounds = [list(b) for b in CONFIG["bounds_unconstrained"]]
    bounds[1][0] = CONFIG["k_Ft_lower_bound_tc"]      # keep k_Ft floored as in TC
    bounds[5] = (0.0, raised_bound)                    # raise A_d ceiling
    x0 = [params[k] for k in PARAM_ORDER]
    r = _fit(x0, P, D, Y, w, [tuple(b) for b in bounds])
    A_d_raised = r.x[5]
    at_bound = A_d_raised > 0.98 * raised_bound
    print(f"\n  A_d with raised bound ({raised_bound:.0f}):  {A_d_raised:.3f}"
          + ("   ← STILL AT BOUND" if at_bound else ""))
    if at_bound:
        print(f"  → A_d is NOT upper-bounded by this {CONFIG['max_test']}-test window.")
        print(f"    Report as 'A_d ≥ (value at T{nthN} decomposition)', not a point.")
        print(f"    The OBSERVABLE familiarity at T{nthN} (SD={SDN:.2f}) is the")
        print(f"    quantity to cite; the infinite-retest ceiling is unidentified.")
    else:
        print(f"  → A_d identified below the raised bound; point estimate usable.")
    return dict(SD_T5=SDN, ST_T5=STN, A_d_raised=A_d_raised, at_bound=at_bound,
                observable_direct_share=SDN/max(SDN+STN,1e-9))


# ═══════════════════════════════════════════════════════════════════════════════
# MERGED MAIN  —  full corrected pipeline + maintenance/schedule/identifiability
# ═══════════════════════════════════════════════════════════════════════════════
def main():
    ap = argparse.ArgumentParser(description="Four Forces Model — merged pipeline")
    ap.add_argument("--data", default=CONFIG["data_file"])
    ap.add_argument("--nboot", type=int, default=50,
                    help="bootstrap resamples (default 50 = fast)")
    ap.add_argument("--nfolds", type=int, default=5)
    ap.add_argument("--boot-batch", type=int, default=10,
                    help="incremental bootstrap batch size")
    ap.add_argument("--fast", action="store_true",
                    help="quick run: tiny boot/grid for a smoke test")
    ap.add_argument("--thorough", action="store_true",
                    help="200 bootstraps, finer grids (slower, publication run)")
    ap.add_argument("--no-heavy", action="store_true",
                    help="skip profile/CV/bootstrap (figures only)")
    ap.add_argument("--minutes-per-game", type=float, default=4.0)
    ap.add_argument("--train-months", type=float, default=18.0)
    ap.add_argument("--show-months", type=float, default=12.0)
    ap.add_argument("--budget-per-day", type=float, default=2.74)
    ap.add_argument("--raised-Ad-bound", type=float, default=100.0)
    args = ap.parse_args()

    CONFIG["data_file"] = args.data
    CONFIG["n_folds"] = args.nfolds
    n_boot = args.nboot
    boot_batches = max(1, int(np.ceil(n_boot / max(args.boot_batch, 1))))
    if args.fast:
        n_boot = 12; boot_batches = 2; CONFIG["n_folds"] = 3
        CONFIG["kFt_profile_grid"] = np.geomspace(1e-6, 2e-2, 8)
    if args.thorough:
        n_boot = 200; boot_batches = max(1, 200 // args.boot_batch)
        CONFIG["kFt_profile_grid"] = np.geomspace(1e-6, 2e-2, 20)
    if args.no_heavy:
        CONFIG["run_heavy_diagnostics"] = False
    np.random.seed(CONFIG["rng_seed"])

    # ── data + fit (ONE fit; all figures use this original fit) ──────────────
    df = prepare_data(CONFIG["data_file"])
    play_bins, play_lbls, day_bins, day_lbls = plot_days_histogram_and_get_bins(df)
    user_weight, _ = compute_user_weights(df, play_bins, play_lbls, day_bins, day_lbls)
    uids, P, D, Y, w, t2_plays = df_to_matrices(df, user_weight)

    params, final = run_optimization(P, D, Y, w)
    err = engine_selfcheck(df, params)
    print(f"\n  engine self-check (scalar vs vectorised): max|Δ| = {err:.2e}  "
          f"({'OK' if err < 1e-6 else 'MISMATCH!'})")

    # ── A_d identifiability (honest reporting of the direct ceiling) ─────────
    report_direct_identifiability(df, params, P, D, Y, w,
                                  raised_bound=args.raised_Ad_bound)

    # ── standard figures (ALL on the original fit) ───────────────────────────
    print(f"\n{'═'*62}\n  GENERATING FIGURES\n{'═'*62}")
    low, high, mt = CONFIG["cohort_low"], CONFIG["cohort_high"], CONFIG["max_test"]
    plot_actual_vs_predicted(df, params, low, high, mt)
    plot_day_sensitivity(df, params, low, high, mt)
    plot_clinical_simulation(params)
    plot_dose_response(params)
    plot_loss_landscape_heatmap(params, P, D, Y, w)
    plot_residuals_distribution(P, D, Y, params)
    plot_actual_vs_predicted_4panel(df, params, mt)
    plot_regression_to_mean(df)

    # ── add-on analyses (advisor feedback) ───────────────────────────────────
    print(f"\n{'═'*62}\n  ADD-ON ANALYSES  (maintenance / schedule / sensitivity)\n{'═'*62}")
    viz_maintenance(params, minutes_per_game=args.minutes_per_game)
    viz_kFt_sensitivity(params, P, D, Y, w, frac=0.80)
    viz_constrained_schedule(params, train_months=args.train_months,
                             show_months=args.show_months,
                             budget_per_day=args.budget_per_day)

    # ── heavy identifiability diagnostics ────────────────────────────────────
    if CONFIG["run_heavy_diagnostics"]:
        plot_kFt_profile(P, D, Y, w, params)
        plot_kfold_calibration(P, D, Y, w, params, k=CONFIG["n_folds"])
        draws = incremental_bootstrap(params, P, D, Y, w,
                                      batch=args.boot_batch, batches=boot_batches)
        if len(draws) >= 4:
            viz_bootstrap(draws, params)
    else:
        print("\n  (heavy diagnostics skipped: --no-heavy)")

    print(f"\n{'═'*62}\n  ✓  Pipeline complete.\n{'═'*62}\n")


if __name__ == "__main__":
    main()
