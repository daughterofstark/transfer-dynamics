"""
figures.py — figure set for the dynamic two-state transfer model (merged fit).
=============================================================================
All figures are driven from one point fit: pass (df, params, P, D, Y, w). Dynamics
use the engine's advance_interval; captions are number-driven from `params`.

MAIN builders:
  fig_schematic            conceptual 6-parameter diagram (no data)
  fig_param_bootstrap      bootstrap distributions of the six parameters
  fig_dose_9panel          3x3 empirical match: T1->T2 dose x T2->T3 dose, shown to T3
  fig_dose_partition       stacked dose-response (direct intercept + transfer), Osman-style
  fig_time_window          fixed dose, varying T1->T2 interval (1..365 d); direct+transfer decay
  fig_dose_time_heatmap    predicted T2 change over games x days
  fig_maintenance_concept  transfer over T1->T2->T3: what a maintenance dose means
  fig_maintenance          steady-state transfer held vs daily dose (3 min/game)
  fig_schedules            fixed-budget regimen comparison (even / front-load / boosters)
SUPPLEMENT builders:
  fig_exposure, fig_cdf, fig_two_channel, fig_Ad_identification,
  + engine primitives (dose curve, loss, k_Ft profile, residuals, calibration, RTM).

Maintenance steady state (D=1):  f(d) = g/(g+k_Ft),  g = 1-(1-k_Lt)^d.
"""
from __future__ import annotations
import os, tempfile
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch

import transfer_model as ff

DPI = ff.CONFIG["dpi"]
PO = ff.PARAM_ORDER
TEAL, CORAL, INK, PURPLE, SAND, SKY = "#2a9d8f", "#e76f51", "#264653", "#6a4c93", "#f2cc8f", "#8ecae6"
MINUTES_PER_GAME = 3.0          # maintenance dose expressed at ~3 min per game
DOSE_BINS  = [(-1, 50), (50, 400), (400, np.inf)]
DOSE_LBLS  = ["<=50 games", "51-400 games", "400+ games"]


# ───────────────────────── shared dynamics helpers ─────────────────────────
def _adv(params, SD, ST, D, P):
    p = params
    return ff.advance_interval(SD, ST, D, P, p["k_Ld"], p["k_Fd"], p["k_Lt"], p["k_Ft"], p["A_d"], p["A_t"])


def _sim_transfer(games_per_day, params, n_days):
    """Day-by-day transfer trajectory (ST) under a games/day schedule (array or scalar)."""
    ST = 0.0; tr = [0.0]
    for day in range(n_days):
        g = games_per_day[day] if np.ndim(games_per_day) else games_per_day
        _, ST = _adv(params, 0.0, ST, 1.0, g)
        tr.append(ST)
    return np.array(tr)


def _T2_states(params, games, days):
    """Direct and transfer accrued at T2 from a single interval (from zero)."""
    return _adv(params, 0.0, 0.0, days, games)


def _games_for_transfer_frac(params, frac, days):
    """Games in one interval (length `days`) to reach frac*A_t of transfer."""
    target = frac * params["A_t"]
    grid = np.linspace(0, 5000, 6001)
    st = np.array([_T2_states(params, g, days)[1] for g in grid])
    i = int(np.argmin(np.abs(st - target)))
    return grid[i]


def _wide(df):
    g = df.sort_values(["user_id", "nth_test"])
    piv = lambda col: g.pivot_table(index="user_id", columns="nth_test", values=col, aggfunc="first")
    return piv("normed_score"), piv("plays_interval"), piv("days_interval")


def _binidx(v):
    for i, (lo, hi) in enumerate(DOSE_BINS):
        if lo < v <= hi:
            return i
    return np.nan


# ═══════════════════════ conceptual schematic ═══════════════════════
def fig_schematic(params, out):
    """Conceptual: two INDEPENDENT processes, three parameters each; observed change
       is their sum. Not fitted here — a diagram of the model's structure."""
    p = params
    t = np.linspace(0, 6, 400); stop = 3.0
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.9))
    specs = [("Transfer  S_T   (gameplay -> NCPT)", p["A_t"], p["k_Lt"], p["k_Ft"], TEAL, ("k_Lt", "A_t", "k_Ft")),
             ("Direct  S_D   (repeated testing)",   p["A_d"], p["k_Ld"], p["k_Fd"], CORAL, ("k_Ld", "A_d", "k_Fd"))]
    for ax, (nm, A, kL, kF, col, (nL, nA, nF)) in zip(axes, specs):
        rise = A * (1 - np.exp(-kL * t * 3)); curve = rise.copy()
        peak = A * (1 - np.exp(-kL * stop * 3)); m = t > stop
        curve[m] = peak * np.exp(-kF * (t[m] - stop) * 6)
        ax.plot(t, curve, color=col, lw=2.8)
        ax.axhline(A, color=col, ls=":", lw=1.4)
        ax.text(6, A, "  ceiling " + nA, color=col, va="center", fontsize=10, fontweight="bold")
        ax.annotate("learning rate " + nL + "\n(rise toward ceiling)", (0.9, curve[58]), (1.2, A * 0.30),
                    fontsize=9, color=col, arrowprops=dict(arrowstyle="->", color=col))
        ax.annotate("forgetting rate " + nF + "\n(decay when idle)", (4.4, curve[290]), (3.3, A * 0.42),
                    fontsize=9, color=col, arrowprops=dict(arrowstyle="->", color=col))
        ax.axvline(stop, color="0.7", ls="--", lw=1); ax.text(stop, 0, " training stops", fontsize=8, color="0.4")
        ax.set_title(nm, fontweight="bold"); ax.set_xlabel("time"); ax.set_ylabel("accrued benefit")
        ax.set_xticks([]); ax.set_ylim(0, A * 1.15); ax.grid(alpha=.25)
    fig.text(0.5, 0.02, "Observed change in NCPT  =  S_T + S_D    "
             "(channels modelled as independent; each has a learning rate, a ceiling, and a forgetting rate)",
             ha="center", fontsize=9.5, style="italic")
    fig.suptitle("Model structure: two independent processes, three parameters each",
                 fontweight="bold", fontsize=12)
    fig.tight_layout(rect=[0, 0.05, 1, 1]); fig.savefig(out, dpi=DPI, bbox_inches="tight"); plt.close(fig)


# ═══════════════════════ exposure ═══════════════════════
def fig_exposure(df, out, day_cuts=(90, 150), play_cuts=(50, 400)):
    t2 = df[df["nth_test"] == 2]
    d = t2["days_interval"].dropna().values; p = t2["plays_interval"].dropna().values
    dclip = np.quantile(d, 0.99) if len(d) else 1.0
    pclip = np.quantile(p, 0.99) if len(p) else 1.0
    fig = plt.figure(figsize=(11, 8))
    gs = fig.add_gridspec(2, 2, width_ratios=[4, 1], height_ratios=[1, 4], hspace=.05, wspace=.05)
    ax = fig.add_subplot(gs[1, 0]); axx = fig.add_subplot(gs[0, 0], sharex=ax); axy = fig.add_subplot(gs[1, 1], sharey=ax)
    hb = ax.hexbin(np.clip(d, 0, dclip), np.clip(p, 0, pclip), gridsize=40, cmap="Blues", bins="log", mincnt=1)
    for c in day_cuts:  ax.axvline(c, color="0.45", ls=":", lw=1)
    for c in play_cuts: ax.axhline(c, color="0.45", ls=":", lw=1)
    ax.set_xlabel("T1->T2 interval (days)"); ax.set_ylabel("T1->T2 games played")
    fig.colorbar(hb, ax=axy, fraction=.5, pad=.05).set_label("participants (log)")
    ecdf = lambda a: (np.sort(a), np.arange(1, len(a) + 1) / len(a))
    xd, yd = ecdf(d); axx.plot(xd, yd, color=INK, lw=1.8); axx.set_xlim(0, dclip)
    xp, yp = ecdf(p); axy.plot(yp, xp, color=INK, lw=1.8); axy.set_ylim(0, pclip)
    axx.set_ylabel("CDF", fontsize=8); axx.tick_params(labelbottom=False); axx.grid(alpha=.3)
    axy.set_xlabel("CDF", fontsize=8); axy.tick_params(labelleft=False); axy.grid(alpha=.3)
    fig.suptitle("Joint T1->T2 exposure — dotted = propensity-weight grid (90/150 d, 50/400 games)",
                 fontweight="bold", fontsize=11)
    fig.savefig(out, dpi=DPI, bbox_inches="tight"); plt.close(fig)


def fig_cdf(df, out):
    t2 = df[df["nth_test"] == 2]
    days = t2["days_interval"].dropna().values; plays = t2["plays_interval"].dropna().values
    ntests = df.groupby("user_id")["nth_test"].max().values
    ecdf = lambda a: (np.sort(a), np.arange(1, len(a) + 1) / len(a))
    fig, ax = plt.subplots(1, 3, figsize=(16, 4.6))
    for a, arr, title, xlab, marks, clip in [
        (ax[0], days, "T1->T2 interval (days)", "Days between T1 and T2", [90, 150], .99),
        (ax[1], plays, "T1->T2 interval (games)", "Games played T1->T2", [50, 200, 500], .99),
        (ax[2], ntests, "NCPT administrations per participant", "Tests per participant", [3, 5], 1.0)]:
        x, y = ecdf(arr); a.plot(x, y, color=INK, lw=2)
        for m in marks: a.axvline(m, color="firebrick", ls="--", lw=1, alpha=.7)
        for q in (.5, .9, .95):
            xv = np.quantile(arr, q); a.axhline(q, color="0.8", ls=":", lw=.8)
            a.text(xv, q, f"  p{int(q*100)}={xv:.0f}", va="bottom", fontsize=8)
        a.set_title(title, fontweight="bold"); a.set_xlabel(xlab)
        a.set_ylabel("Cumulative fraction"); a.grid(alpha=.3); a.set_ylim(0, 1.02)
        if clip < 1.0 and len(arr): a.set_xlim(0, np.quantile(arr, clip))
    fig.suptitle("Exposure and assessment distributions — empirical CDFs", fontweight="bold")
    fig.tight_layout(); fig.savefig(out, dpi=DPI, bbox_inches="tight"); plt.close(fig)


# ═══════════════════════ parameter bootstrap ═══════════════════════
def _bootstrap(P, D, Y, w, params, n_boot=200, seed=7, kft_floor=1e-6):
    rng = np.random.default_rng(seed); n = P.shape[0]
    b6 = [(1e-6, .99), (kft_floor, .99), (1e-6, .99), (1e-6, .99), (0.0, 30.0), (0.0, ff.CONFIG["A_d_ceiling"])]
    x0 = [params[k] for k in PO]; draws = np.full((n_boot, 6), np.nan)
    for b in range(n_boot):
        idx = rng.integers(0, n, n)
        r = ff._fit(x0, P[idx], D[idx], Y[idx], w[idx], b6, maxiter=300)
        if r.success: draws[b] = r.x
        if (b + 1) % max(1, n_boot // 5) == 0: print(f"    bootstrap {b+1}/{n_boot}")
    return draws


def _ci(a):
    a = a[~np.isnan(a)]; return np.percentile(a, 2.5), np.percentile(a, 97.5)


def fig_param_bootstrap(draws, params, out):
    names = ["k_Lt", "k_Ft", "k_Ld", "k_Fd", "A_t", "A_d"]
    fig, axes = plt.subplots(2, 3, figsize=(15, 8)); axes = axes.flatten()
    for nm, ax in zip(names, axes):
        col = draws[:, PO.index(nm)]; col = col[~np.isnan(col)]
        lo, hi = _ci(col)
        ax.hist(col, bins=32, color="#6b8ea3", alpha=.85, edgecolor="white")
        ax.axvline(params[nm], color="black", lw=2)
        ax.axvline(lo, color="firebrick", ls="--", lw=1.2); ax.axvline(hi, color="firebrick", ls="--", lw=1.2)
        hl = ""
        if nm in ("k_Ft", "k_Fd"):
            hl = f"  (HL {np.log(2)/(-np.log(1-params[nm]))/365:.2f} yr)"
        ax.set_title(f"{nm} = {params[nm]:.4g}{hl}\n95% CI [{lo:.3g}, {hi:.3g}]", fontsize=10, fontweight="bold")
        ax.grid(alpha=.3)
    fig.suptitle("Bootstrap parameter distributions (participants resampled with replacement)",
                 fontsize=13, fontweight="bold")
    plt.tight_layout(); fig.savefig(out, dpi=DPI, bbox_inches="tight"); plt.close(fig)


# ═══════════════════════ 3x3 empirical match (to T3) ═══════════════════════
def fig_dose_row(df, params, out, draws=None, fix_row=1):
    """Leaner alternative to the 3x3: fix T1->T2 dose at one level (default the
       moderate 51-400 band) and vary T2->T3 across the three dose bins. Isolates the
       one comparison that matters — does more T2->T3 gameplay predict more T3 gain —
       without the 9-cell clutter. Same per-participant model + bootstrap band."""
    S, Pl, Da = _wide(df)
    for c in (1, 2, 3):
        if c not in S.columns or c not in Pl.columns or c not in Da.columns:
            raise RuntimeError("need T1..T3 present")

    def _params_of(row): return {k: row[PO.index(k)] for k in PO}
    d2 = S[2] - S[1]; d3 = S[3] - S[1]
    b12 = Pl[2].apply(_binidx); b23 = Pl[3].apply(_binidx)
    fig, axes = plt.subplots(1, 3, figsize=(15, 5), sharey=True)
    ymax = 0
    for j in range(3):
        ax = axes[j]
        uids = ((b12 == fix_row) & (b23 == j)); uids = uids[uids].index; n = len(uids)
        if n < 20:
            ax.text(.5, .5, f"n={n}", transform=ax.transAxes, ha="center", color="0.6"); continue
        o2 = d2.loc[uids].dropna(); o3 = d3.loc[uids].dropna()
        m2, m3 = o2.mean(), o3.mean()
        c2 = 1.96 * o2.std() / np.sqrt(len(o2)); c3 = 1.96 * o3.std() / np.sqrt(len(o3))
        P2, D2, P3, D3 = Pl[2].loc[uids], Da[2].loc[uids], Pl[3].loc[uids], Da[3].loc[uids]
        pr2, pr3 = [], []
        for u in uids:
            if np.isnan(P2[u]) or np.isnan(D2[u]): continue
            s1, t1 = _adv(params, 0, 0, D2[u], P2[u]); pr2.append(s1 + t1)
            if not (np.isnan(P3[u]) or np.isnan(D3[u])):
                s2, t2 = _adv(params, s1, t1, D3[u], P3[u]); pr3.append(s2 + t2)
        mp2 = np.mean(pr2) if pr2 else np.nan; mp3 = np.mean(pr3) if pr3 else np.nan
        if draws is not None:
            mp = np.nanmean(P2.values), np.nanmean(D2.values), np.nanmean(P3.values), np.nanmean(D3.values)
            bb2, bb3 = [], []
            for row in draws:
                if np.any(np.isnan(row)): continue
                dp = _params_of(row)
                s1, t1 = _adv(dp, 0, 0, mp[1], mp[0]); bb2.append(s1 + t1)
                s2, t2 = _adv(dp, s1, t1, mp[3], mp[2]); bb3.append(s2 + t2)
            if bb2:
                lo2, hi2 = np.percentile(bb2, [2.5, 97.5]); lo3, hi3 = np.percentile(bb3, [2.5, 97.5])
                ax.fill_between([1, 2, 3], [0, lo2, lo3], [0, hi2, hi3], color=INK, alpha=.15, zorder=0)
        ax.errorbar([1, 2, 3], [0, m2, m3], yerr=[0, c2, c3], fmt="o-", color=CORAL, capsize=3, ms=6,
                    label="observed" if j == 0 else None)
        ax.plot([1, 2, 3], [0, mp2, mp3], "s--", color=INK, ms=5,
                label="model" if j == 0 else None)
        ax.text(.03, .95, f"n={n:,}\nmean {D2.mean():.0f} d to T2", transform=ax.transAxes,
                fontsize=9, color="0.4", va="top")
        ymax = max(ymax, m3 + c3, mp3 if not np.isnan(mp3) else 0)
        ax.set_title(f"T2->T3 gameplay: {DOSE_LBLS[j]}", fontsize=11)
        ax.set_xlabel("assessment"); ax.set_xticks([1, 2, 3]); ax.grid(alpha=.3)
    axes[0].set_ylabel(f"GI change from T1\n(T1->T2 fixed at {DOSE_LBLS[fix_row]})")
    axes[0].legend(fontsize=9, loc="lower right")
    for a in axes: a.set_ylim(-0.5, ymax * 1.12 if ymax else 8)
    fig.suptitle("Model reproduces the T2->T3 dose effect (T1->T2 dose held fixed)",
                 fontsize=13, fontweight="bold")
    fig.tight_layout(); fig.savefig(out, dpi=DPI, bbox_inches="tight"); plt.close(fig)


def fig_dose_9panel(df, params, out, draws=None):
    """Rows = T1->T2 dose bin, cols = T2->T3 dose bin (<=50 / 51-400 / 400+).
       Observed mean delta (+/-95% CI) vs model (each participant's own intervals).
       If `draws` (bootstrap param sets) is given, a model uncertainty band is added
       at each cell's mean exposure, so low-N cells show model range too. Shared axes."""
    S, Pl, Da = _wide(df)
    for c in (1, 2, 3):
        if c not in S.columns or c not in Pl.columns or c not in Da.columns:
            raise RuntimeError("need T1..T3 present for the 3x3 panel")

    def _params_of(row):
        return {k: row[PO.index(k)] for k in PO}
    d2 = S[2] - S[1]; d3 = S[3] - S[1]
    b12 = Pl[2].apply(_binidx); b23 = Pl[3].apply(_binidx)
    total = int(((b12.notna()) & (b23.notna())).sum())
    fig, axes = plt.subplots(3, 3, figsize=(13, 11), sharex=True, sharey=True)
    ymax = 0
    for i in range(3):
        for j in range(3):
            ax = axes[i, j]
            uids = ((b12 == i) & (b23 == j))
            uids = uids[uids].index; n = len(uids)
            if n < 20:
                ax.text(.5, .5, f"n={n}", transform=ax.transAxes, ha="center", color="0.6"); continue
            o2 = d2.loc[uids].dropna(); o3 = d3.loc[uids].dropna()
            m2, m3 = o2.mean(), o3.mean()
            c2 = 1.96 * o2.std() / np.sqrt(len(o2)); c3 = 1.96 * o3.std() / np.sqrt(len(o3))
            # model = each participant's OWN intervals, then averaged (no median/90d proxy)
            P2, D2, P3, D3 = Pl[2].loc[uids], Da[2].loc[uids], Pl[3].loc[uids], Da[3].loc[uids]
            pr2, pr3 = [], []
            for u in uids:
                if np.isnan(P2[u]) or np.isnan(D2[u]):
                    continue
                sd1, st1 = _adv(params, 0, 0, D2[u], P2[u]); pr2.append(sd1 + st1)
                if not (np.isnan(P3[u]) or np.isnan(D3[u])):
                    sd2, st2 = _adv(params, sd1, st1, D3[u], P3[u]); pr3.append(sd2 + st2)
            mp2 = np.mean(pr2) if pr2 else np.nan; mp3 = np.mean(pr3) if pr3 else np.nan
            # bootstrap model band at the cell's mean exposure (parameter uncertainty)
            if draws is not None:
                mp = np.nanmean(P2.values), np.nanmean(D2.values), np.nanmean(P3.values), np.nanmean(D3.values)
                b2, b3 = [], []
                for row in draws:
                    if np.any(np.isnan(row)):
                        continue
                    dp = _params_of(row)
                    s1, t1 = _adv(dp, 0, 0, mp[1], mp[0]); b2.append(s1 + t1)
                    s2, t2 = _adv(dp, s1, t1, mp[3], mp[2]); b3.append(s2 + t2)
                if b2:
                    lo2, hi2 = np.percentile(b2, [2.5, 97.5]); lo3, hi3 = np.percentile(b3, [2.5, 97.5])
                    ax.fill_between([1, 2, 3], [0, lo2, lo3], [0, hi2, hi3], color=INK, alpha=.15, zorder=0)
            ax.errorbar([1, 2, 3], [0, m2, m3], yerr=[0, c2, c3], fmt="o-", color=CORAL, capsize=3, ms=5,
                        label="observed" if (i == 0 and j == 0) else None)
            ax.plot([1, 2, 3], [0, mp2, mp3], "s--", color=INK, ms=4,
                    label="model (each participant's own intervals)" if (i == 0 and j == 0) else None)
            note = f"n={n:,}\nmean {D2.mean():.0f} d to T2"
            ax.text(.03, .97, note, transform=ax.transAxes, fontsize=8, color="0.4", va="top")
            ymax = max(ymax, m3 + c3, mp3 if not np.isnan(mp3) else 0)
            if i == 0: ax.set_title(f"T2->T3: {DOSE_LBLS[j]}", fontsize=10)
            if j == 0: ax.set_ylabel(f"T1->T2: {DOSE_LBLS[i]}\nGI change from T1", fontsize=9)
            if i == 2: ax.set_xlabel("assessment")
            ax.set_xticks([1, 2, 3]); ax.grid(alpha=.3)
    axes[0, 0].legend(fontsize=8, loc="lower right")
    for a in axes.flat: a.set_ylim(-0.5, ymax * 1.12 if ymax else 8)
    fig.suptitle("Observed vs model NCPT change by T1->T2 and T2->T3 gameplay dose (to T3)\n"
                 f"model uses each participant's own intervals; n={total:,} participants with >=3 assessments",
                 fontsize=12, fontweight="bold")
    fig.tight_layout(); fig.savefig(out, dpi=DPI, bbox_inches="tight"); plt.close(fig)


# ═══════════════════════ stacked dose-response (Osman-style) ═══════════════════════
def fig_dose_partition(df, params, out, days=None, gmax=1800):
    p = params
    if days is None:
        days = float(df[df["nth_test"] == 2]["days_interval"].mean())   # population mean interval
    g = np.linspace(0, gmax, 600)
    SD = np.array([_T2_states(p, gi, days)[0] for gi in g])
    ST = np.array([_T2_states(p, gi, days)[1] for gi in g])
    total = SD + ST
    I = SD.mean()                       # direct intercept (near-constant in games)
    print(f"  [dose-partition] intercept I = {I:.3f} GI pts at {days:.0f} d "
          f"(one retest of familiarity, decayed): k_Ld={p['k_Ld']:.3f}, A_d={p['A_d']:.2f}, "
          f"raw one-dose k_Ld*A_d = {p['k_Ld']*p['A_d']:.3f}; asymptote A = I + A_t = {I + p['A_t']:.2f}. "
          f"A higher A_d (from the short-interval augmentation) raises this intercept vs "
          f"long-interval-only estimates.")
    d80 = _games_for_transfer_frac(p, 0.80, days)
    st80 = _T2_states(p, d80, days)[1]
    fig, ax = plt.subplots(figsize=(9.5, 6))
    ax.fill_between(g, 0, SD, color=SKY, alpha=.55, label="Direct practice (repeated testing)")
    ax.fill_between(g, SD, total, color=SAND, alpha=.75, label="Transfer of learning (games -> NCPT)")
    ax.plot(g, total, color=CORAL, lw=2.4)
    ax.axhline(I, color="0.5", ls="--", lw=1); ax.text(gmax, I, "  intercept I", va="center", fontsize=9, color="0.4")
    ax.axhline(I + p["A_t"], color="0.5", ls="--", lw=1); ax.text(gmax, I + p["A_t"], "  asymptote A", va="center", fontsize=9, color="0.4")
    ax.plot(d80, I + st80, "o", color=INK, ms=7)
    ax.annotate(f"80% of transfer ceiling\n~{d80:.0f} games (at {days:.0f} d;\ndepends on the interval)",
                (d80, I + st80), (d80 + 250, I + st80 - 1.2), fontsize=9,
                arrowprops=dict(arrowstyle="->", color=INK))
    ax.set_xlabel("Games between T1 and T2"); ax.set_ylabel("Change in GI (T2 - T1)")
    ax.set_xlim(0, gmax); ax.set_ylim(0, (I + p["A_t"]) * 1.12); ax.legend(loc="center right"); ax.grid(alpha=.3)
    ax.set_title("Dose-response partition: direct practice + transfer\n(reproduces Osman et al. decomposition)",
                 fontweight="bold")
    fig.tight_layout(); fig.savefig(out, dpi=DPI, bbox_inches="tight"); plt.close(fig)


# ═══════════════════════ fixed dose, varying time window ═══════════════════════
def fig_time_window(df, params, out, fixed_games=None, day_max=365):
    p = params
    if fixed_games is None:
        med_d = float(df[df["nth_test"] == 2]["days_interval"].median())
        fixed_games = _games_for_transfer_frac(p, 0.80, med_d)
    days = np.arange(1, day_max + 1)
    SD = np.array([_T2_states(p, fixed_games, dd)[0] for dd in days])
    ST = np.array([_T2_states(p, fixed_games, dd)[1] for dd in days])
    fig, ax = plt.subplots(figsize=(9.5, 6))
    # direct on the bottom, transfer stacked on top — same order as fig_dose_partition
    ax.fill_between(days, 0, SD, color=SKY, alpha=.55, label="Direct practice (decays at k_Fd)")
    ax.fill_between(days, SD, SD + ST, color=SAND, alpha=.75, label="Transfer (decays at k_Ft)")
    ax.plot(days, SD + ST, color=CORAL, lw=2.2)
    ax.set_xlabel("Days between T1 and T2 (single retest)"); ax.set_ylabel("Predicted change in GI at T2")
    ax.set_xlim(1, day_max); ax.set_ylim(0, None); ax.legend(loc="upper right"); ax.grid(alpha=.3)
    ax.set_title(f"Same gameplay dose ({fixed_games:.0f} games), different T1->T2 windows\n"
                 "the retained benefit — and its split — depends on time", fontweight="bold")
    fig.tight_layout(); fig.savefig(out, dpi=DPI, bbox_inches="tight"); plt.close(fig)


# ═══════════════════════ dose x time heatmap ═══════════════════════
def fig_dose_time_heatmap(params, out, gmax=1000, day_max=365):
    p = params
    G = np.linspace(0, gmax, 120); Dd = np.linspace(1, day_max, 120)
    Z = np.zeros((len(Dd), len(G)))
    for iy, dd in enumerate(Dd):
        for ix, gg in enumerate(G):
            sd, st = _T2_states(p, gg, dd)
            Z[iy, ix] = sd + st
    fig, ax = plt.subplots(figsize=(8.4, 6.2))
    im = ax.pcolormesh(G, Dd, Z, cmap="viridis", shading="auto", rasterized=True)
    cs = ax.contour(G, Dd, Z, levels=6, colors="white", linewidths=.6, alpha=.85)
    ax.clabel(cs, inline=True, fontsize=8, fmt="%.1f")
    cbar = fig.colorbar(im, ax=ax); cbar.set_label("Predicted change in GI at T2", fontsize=9)
    cbar.ax.tick_params(labelsize=8)
    ax.set_xlabel("Games between T1 and T2", fontsize=9); ax.set_ylabel("Days between T1 and T2", fontsize=9)
    ax.tick_params(labelsize=8)
    ax.set_title("Predicted NCPT change as a joint function of dose and time", fontsize=11, fontweight="bold")
    fig.tight_layout(); fig.savefig(out, dpi=DPI, bbox_inches="tight"); plt.close(fig)


# ═══════════════════════ maintenance concept ═══════════════════════
def fig_maintenance_concept(df, params, out, maint_doses=(1.0, 5.0), seg_days=90):
    """Transfer only, y in % of asymptote. Two panels, each a different maintenance
       dose. In each: load (90 d) to 50/75/95% of A_t, then apply that constant dose;
       every level converges to the dose's steady state (higher decays, lower rises)."""
    p = params; At = p["A_t"]
    fig, axes = plt.subplots(1, len(maint_doses), figsize=(6.6 * len(maint_doses), 5.6), sharey=True)
    if len(maint_doses) == 1:
        axes = [axes]
    for ax, gpd in zip(axes, maint_doses):
        for frac, col in [(0.5, TEAL), (0.75, PURPLE), (0.95, CORAL)]:
            g_load = _games_for_transfer_frac(p, frac, seg_days)
            load = _sim_transfer(g_load / seg_days, p, seg_days)
            ST = load[-1]; maint = [ST]
            for _ in range(seg_days):
                _, ST = _adv(p, 0.0, ST, 1.0, gpd); maint.append(ST)
            x1 = np.arange(0, seg_days + 1); x2 = np.arange(seg_days, 2 * seg_days + 1)
            ax.plot(x1, 100 * load / At, color=col, lw=2.2)
            arrow = "decays to" if maint[-1] < load[-1] else "rises to"
            ax.plot(x2, 100 * np.array(maint) / At, color=col, lw=2.2, ls="--",
                    label=f"loaded to {frac*100:.0f}%  →  {arrow} {maint[-1]/At*100:.0f}%")
        gg = 1.0 - (1.0 - p["k_Lt"]) ** gpd; ss = gg / (gg + p["k_Ft"])
        ax.axhline(ss * 100, color="0.35", ls="-.", lw=1.6)
        ax.text(2 * seg_days, ss * 100, f"  steady state {ss*100:.0f}%", va="center",
                fontsize=8, color="0.35", fontweight="bold")
        ax.axvline(seg_days, color="0.8", lw=1); ax.text(seg_days, 1, " maintenance begins", fontsize=8, color="0.4")
        ax.set_xlabel("Day of trial"); ax.set_title(f"maintenance dose = {gpd:g} game/day", fontweight="bold")
        ax.legend(loc="lower right", fontsize=8); ax.grid(alpha=.3); ax.set_ylim(0, 100)
    axes[0].set_ylabel("Transfer benefit (% of asymptote A_t)")
    fig.suptitle("A maintenance dose defines a steady state (90-day loading, then a constant dose)\n"
                 "higher levels decay toward it; lower levels rise to it", fontweight="bold")
    fig.tight_layout(); fig.savefig(out, dpi=DPI, bbox_inches="tight"); plt.close(fig)


# ═══════════════════════ maintenance dose-response ═══════════════════════
def fig_maintenance(params, out, kft_ci=None, minutes_per_game=MINUTES_PER_GAME):
    p = params; kLt, kFt = p["k_Lt"], p["k_Ft"]
    d = np.linspace(0.01, 6, 400); g = 1.0 - (1.0 - kLt) ** d
    frac = lambda kft: 100.0 * g / (g + kft)
    fig, ax = plt.subplots(figsize=(9, 5.6))
    if kft_ci is not None:
        lo, hi = kft_ci
        ax.fill_between(d, frac(hi), frac(lo), color=TEAL, alpha=.18, label=f"k_Ft 95% CI [{lo:.1e}, {hi:.1e}]")
    ax.plot(d, frac(kFt), color=INK, lw=2.5,
            label=f"fitted k_Ft = {kFt:.2e}  (HL ≈ {np.log(2)/(-np.log(1-kFt))/365:.2f} yr)")
    ax.axhline(90, color="0.5", ls=":", lw=1.2); ax.text(0.05, 90.5, "90% of ceiling", fontsize=8, color="0.4")
    for dose in (0.5, 1.0, 1.3, 2.0, 5.0):
        gg = 1.0 - (1.0 - kLt) ** dose; f = 100 * gg / (gg + kFt)
        ax.plot(dose, f, "o", color=CORAL, ms=6)
        tag = " (prescribed)" if dose == 5.0 else ""
        ax.annotate(f"{dose:g} g/day (≈{dose*minutes_per_game:.0f} min) → {f:.0f}%{tag}",
                    (dose, f), textcoords="offset points", xytext=(6, -12), fontsize=8, color=CORAL)
    ax.set_xlabel("Maintenance dose (games per day)"); ax.set_ylabel("Steady-state transfer held (% of A_t)")
    sec = ax.secondary_xaxis("top", functions=(lambda x: x * minutes_per_game, lambda x: x / minutes_per_game))
    sec.set_xlabel(f"≈ minutes per day (at {minutes_per_game:.0f} min/game)")
    ax.set_ylim(0, 102); ax.set_xlim(0, 6); ax.grid(alpha=.3)
    ax.set_title("Maintenance dose-response — steady-state transfer held by a constant daily dose\n"
                 "(at the fitted forgetting rate; band = k_Ft bootstrap CI)", fontweight="bold")
    ax.legend(loc="lower right"); fig.tight_layout(); fig.savefig(out, dpi=DPI, bbox_inches="tight"); plt.close(fig)


# ═══════════════════════ schedule simulation ═══════════════════════
def fig_schedules(params, out, horizon=547, budget=1094, load_days=60, load_rate=7.0, boost_rate=7.0):
    """Three regimens at the SAME cumulative budget; transfer in % of asymptote.
    Budget ~2 games/day (1094 over 547 d) so the maintenance arms sit near their
    ~81% steady state — true maintenance rather than decay to a low floor.
    Green spreads it evenly; purple loads then maintains the remainder; orange loads
    then delivers two 6-month-apart booster blocks sized to the remainder, zero between."""
    p = params; At = p["A_t"]
    load_cost = load_days * load_rate
    rem = budget - load_cost

    even = np.full(horizon, budget / horizon)
    fl = np.zeros(horizon); fl[:load_days] = load_rate
    maint_fl = rem / (horizon - load_days); fl[load_days:] = maint_fl

    n_boost = 2
    boost_starts = (240, 420)                             # ~6-month spacing (mo 8 and mo 14)
    per_boost = rem / n_boost                             # each booster spends half the remainder
    boost_days = int(round(per_boost / boost_rate))       # ~48 d each at ~7/day ("training block")
    bo = np.zeros(horizon); bo[:load_days] = load_rate
    for s in boost_starts:
        e = min(s + boost_days, horizon)
        bo[s:e] = boost_rate
    seg = bo[load_days:]                                   # rescale post-load to exact remainder
    if seg.sum() > 0:
        bo[load_days:] = seg * (rem / seg.sum())

    schedules = {
        f"Even spread ({budget/horizon:.2f}/day)": (even, TEAL),
        f"Load 60 d @{load_rate:g}/day, then maintain {maint_fl:.2f}/day": (fl, PURPLE),
        f"Load 60 d @{load_rate:g}/day, then 2 boosters (~{boost_days} d, 6-mo apart), zero between": (bo, CORAL),
    }
    for lab, (sch, _) in schedules.items():
        assert abs(sch.sum() - budget) < 1.0, f"{lab} spends {sch.sum():.0f}, not {budget}"

    fig, (a0, a1) = plt.subplots(2, 1, figsize=(11, 7.2), gridspec_kw={"height_ratios": [3, 1]}, sharex=True)
    for lab, (sch, col) in schedules.items():
        tr = _sim_transfer(sch, p, horizon)
        a0.plot(np.arange(horizon + 1), 100 * tr / At, color=col, lw=2,
                label=f"{lab}\n   end {100*tr[-1]/At:.0f}% · mean {100*np.mean(tr)/At:.0f}%")
        a1.plot(np.arange(horizon), sch, color=col, lw=1.2)
    a0.axhline(100, color="0.6", ls=":", lw=1); a0.text(horizon, 100, "  A_t", va="center", color="0.4")
    a0.set_ylabel("Transfer benefit (% of asymptote A_t)"); a0.legend(loc="lower right", fontsize=8.5)
    a0.grid(alpha=.3); a0.set_ylim(0, 100)
    a0.set_title(f"Training-schedule comparison at a fixed budget ({budget:.0f} games over {horizon} d)\n"
                 "same cumulative volume, three paths — even spread, steady maintenance, or boosters",
                 fontweight="bold")
    a1.set_ylabel("games/day"); a1.set_xlabel("Day of trial"); a1.grid(alpha=.3)
    fig.tight_layout(); fig.savefig(out, dpi=DPI, bbox_inches="tight"); plt.close(fig)


# ═══════════════════════ two-channel accrual + ceilings ═══════════════════════
def fig_two_channel(df, params, out, max_test=5):
    p = params; meds = []
    for k in range(2, max_test + 1):
        sub = df[df["nth_test"] == k]; mp, md = sub["plays_interval"].median(), sub["days_interval"].median()
        if np.isnan(mp) or np.isnan(md): break
        meds.append((mp, md))
    SD, ST = 0.0, 0.0; sd_tr, st_tr = [0.0], [0.0]
    for (Pi, Di) in meds:
        SD, ST = _adv(p, SD, ST, Di, Pi); sd_tr.append(SD); st_tr.append(ST)
    tests = np.arange(1, len(sd_tr) + 1)
    fig, (a0, a1) = plt.subplots(1, 2, figsize=(12.5, 5), gridspec_kw={"width_ratios": [1.4, 1]})
    a0.plot(tests, st_tr, "o-", color=TEAL, lw=2.2, ms=7, label="Transfer S_T (gameplay)")
    a0.plot(tests, sd_tr, "s-", color=CORAL, lw=2.2, ms=7, label="Familiarity S_D (direct)")
    a0.axhline(p["A_t"], color=TEAL, ls=":", lw=1.2); a0.axhline(p["A_d"], color=CORAL, ls=":", lw=1.2)
    a0.set_xlabel("Assessment"); a0.set_ylabel("Accrued component (GI points)")
    a0.set_title("Both channels accrue over the observation window\n(median exposure)", fontweight="bold")
    a0.legend(); a0.grid(alpha=.3); a0.set_xticks(tests)
    At, Ad = p["A_t"], p["A_d"]; share = Ad / (At + Ad)
    a1.bar(["Transfer\nA_t", "Direct\nA_d"], [At, Ad], color=[TEAL, CORAL])
    for i, v in enumerate([At, Ad]): a1.text(i, v, f"{v:.2f}", ha="center", va="bottom", fontweight="bold")
    a1.set_ylabel("Asymptotic ceiling (GI points)")
    a1.set_title(f"Asymptotic ceilings\ndirect share = {share*100:.1f}%", fontweight="bold"); a1.grid(alpha=.3, axis="y")
    fig.tight_layout(); fig.savefig(out, dpi=DPI, bbox_inches="tight"); plt.close(fig)


def fig_Ad_identification(draws_orig, draws_merged, out):
    i = PO.index("A_d"); ceil = ff.CONFIG["A_d_ceiling"]
    ao = draws_orig[:, i][~np.isnan(draws_orig[:, i])]; am = draws_merged[:, i][~np.isnan(draws_merged[:, i])]
    fig, ax = plt.subplots(figsize=(9, 5)); bins = np.linspace(0, ceil, 50)
    ax.hist(ao, bins=bins, color="#9aa0a6", alpha=.6, density=True, label=f"T1-T3 records ({np.mean(ao>=.95*ceil)*100:.0f}% at bound)")
    ax.hist(am, bins=bins, color=TEAL, alpha=.6, density=True, label=f"augmented ({np.mean(am>=.95*ceil)*100:.0f}% at bound)")
    ax.set_xlim(0, min(ceil, max(np.percentile(ao, 98), np.percentile(am, 98)) * 1.1))
    ax.set_xlabel("A_d bootstrap draws (direct-practice ceiling)"); ax.set_ylabel("density"); ax.legend()
    ax.set_title("Short-interval retakes pin the direct-practice ceiling", fontweight="bold"); ax.grid(alpha=.3)
    fig.tight_layout(); fig.savefig(out, dpi=DPI, bbox_inches="tight"); plt.close(fig)


# ═══════════════════════ driver ═══════════════════════
def _try(man, name, fn):
    try:
        fn(); man.append((name, "OK")); print(f"    OK   {name}")
    except Exception as e:
        man.append((name, f"FAIL: {type(e).__name__}: {e}")); print(f"    FAIL {name}: {e}")


def make_all(df, params, P, D, Y, w, main_dir, supp_dir, nboot=200, seed=7, max_test=5, draws_orig=None):
    man = []; os.makedirs(main_dir, exist_ok=True); os.makedirs(supp_dir, exist_ok=True)
    saved = ff.CONFIG.get("save_dir", ".")
    print(f"\n  bootstrapping merged fit (B={nboot}) …")
    draws = _bootstrap(P, D, Y, w, params, n_boot=nboot, seed=seed, kft_floor=1e-6)
    kft_ci = _ci(draws[:, PO.index("k_Ft")])

    ff.CONFIG["save_dir"] = main_dir; md = main_dir
    print(f"\n  MAIN figures -> {md}/")
    _try(man, "schematic (6 params)",      lambda: fig_schematic(params, f"{md}/fig_schematic.png"))
    _try(man, "exposure",                  lambda: fig_exposure(df, f"{md}/fig_exposure.png"))
    _try(man, "parameter bootstrap",       lambda: fig_param_bootstrap(draws, params, f"{md}/fig_param_bootstrap.png"))
    _try(man, "3x3 empirical match",       lambda: fig_dose_9panel(df, params, f"{md}/fig_dose_9panel.png", draws=draws))
    _try(man, "3-panel dose row",          lambda: fig_dose_row(df, params, f"{md}/fig_dose_row.png", draws=draws))
    _try(man, "dose-response partition",   lambda: fig_dose_partition(df, params, f"{md}/fig_dose_partition.png"))
    _try(man, "fixed dose x time window",  lambda: fig_time_window(df, params, f"{md}/fig_time_window.png"))
    _try(man, "dose x time heatmap",       lambda: fig_dose_time_heatmap(params, f"{md}/fig_dose_time_heatmap.png"))
    _try(man, "maintenance concept",       lambda: fig_maintenance_concept(df, params, f"{md}/fig_maintenance_concept.png"))
    _try(man, "maintenance dose",          lambda: fig_maintenance(params, f"{md}/fig_maintenance.png", kft_ci=kft_ci))
    _try(man, "schedule comparison",       lambda: fig_schedules(params, f"{md}/fig_schedules.png"))

    ff.CONFIG["save_dir"] = supp_dir; sd = supp_dir
    print(f"\n  SUPPLEMENT figures -> {sd}/")
    _try(man, "S CDFs",                    lambda: fig_cdf(df, f"{sd}/figS_cdf.png"))
    _try(man, "S two-channel",             lambda: fig_two_channel(df, params, f"{sd}/figS_two_channel.png", max_test))
    _try(man, "S dose curve",              lambda: ff.plot_dose_response(params))
    _try(man, "S residuals",               lambda: ff.plot_residuals_distribution(P, D, Y, params))
    _try(man, "S regression-to-mean",      lambda: ff.plot_regression_to_mean(df))
    if draws_orig is not None:
        _try(man, "S A_d identification",  lambda: fig_Ad_identification(draws_orig, draws, f"{sd}/figS_Ad_identification.png"))
    ff.CONFIG["save_dir"] = saved
    return man, draws


def bootstrap_for_orig(P, D, Y, w, params, nboot=200, seed=7):
    return _bootstrap(P, D, Y, w, params, n_boot=nboot, seed=seed, kft_floor=1e-6)
