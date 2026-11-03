"""
propagate_uncertainty.py — joint parameter uncertainty for the derived quantities.
==================================================================================
Closes completion item 4 and generates Supplementary Fig. 5.

The manuscript currently reports a ONE-PARAMETER band on the maintenance curve:
k_Ft is swept over its bootstrap interval while k_Lt and A_t are held at the point
estimate. That is a sensitivity band, not a confidence interval. This script
propagates the 200 joint bootstrap draws through the same quantities, so the
maintenance dose-response and the three schedule summaries can be reported with a
joint interval alongside the one-parameter sweep.

Drop into the repo root next to verify_numbers.py and run:

    python propagate_uncertainty.py --data newsubset.csv --nicole "<subtest csv>"
    python propagate_uncertainty.py ... --draws _verify_scratch/draws.npy   # reuse

Outputs
    _verify_scratch/draws.npy              200 x 6 bootstrap draws (cached)
    _verify_scratch/uncertainty.csv        schedule summaries per draw
    figS5_uncertainty.png                  Supplementary Fig. 5
"""
from __future__ import annotations
import argparse, copy, os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import transfer_model as ff
import paper_pipeline as pp
import figures as figs
import verify_numbers as vn

PO = ff.PARAM_ORDER
SCRATCH = vn.SCRATCH
MPG = figs.MINUTES_PER_GAME          # 3.0 minutes per gameplay
HORIZON, BUDGET, LOAD_DAYS, LOAD_RATE = 547, 1094, 60, 7.0


# ────────────────────────────── derived quantities ──────────────────────────────
def steady_state(dose_per_day, k_Lt, k_Ft):
    """Fraction of the transfer ceiling held at steady state under a constant dose."""
    g = 1.0 - (1.0 - k_Lt) ** dose_per_day
    return g / (g + k_Ft)


def schedules(budget=BUDGET, horizon=HORIZON, load_days=LOAD_DAYS, load_rate=LOAD_RATE):
    """The three daily-gameplay vectors used in Fig. 8. Identical to figures.fig_schedules."""
    rem = budget - load_days * load_rate
    even = np.full(horizon, budget / horizon)
    fl = np.zeros(horizon); fl[:load_days] = load_rate
    fl[load_days:] = rem / (horizon - load_days)
    boost_days = int(round((rem / 2) / load_rate))
    bo = np.zeros(horizon); bo[:load_days] = load_rate
    for s in (240, 420):
        bo[s:min(s + boost_days, horizon)] = load_rate
    seg = bo[load_days:]
    bo[load_days:] = seg * (rem / seg.sum())
    for name, sch in (("even", even), ("load", fl), ("boost", bo)):
        assert abs(sch.sum() - budget) < 1.0, f"{name} spends {sch.sum():.0f}"
    return {"even": even, "load": fl, "boost": bo}


def schedule_summary(params, sch):
    """Endpoint and period-average transfer, each as a percentage of that draw's ceiling."""
    tr = figs._sim_transfer(sch, params, len(sch))
    At = params["A_t"]
    return 100 * tr[-1] / At, 100 * tr.mean() / At


# ────────────────────────────────── main ──────────────────────────────────────
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="newsubset.csv")
    ap.add_argument("--nicole", required=True)
    ap.add_argument("--min-valid-subtests", type=int, default=3)
    ap.add_argument("--uid-prefix", default="NIC_")
    ap.add_argument("--nboot", type=int, default=200)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--draws", default=os.path.join(SCRATCH, "draws.npy"))
    ap.add_argument("--rebuild", action="store_true")
    ap.add_argument("--out", default="figS5_uncertainty.png")
    args = ap.parse_args()
    os.makedirs(SCRATCH, exist_ok=True)

    saved = copy.deepcopy(ff.CONFIG)
    try:
        _, merged = vn.build_merged_once(args)
        _, P, D, Y, w, params, wmse, _ = vn.main_fit(merged)
        print(f"\n  main fit: WMSE {wmse:.4f}   " +
              "  ".join(f"{k}={params[k]:.5g}" for k in PO))

        if os.path.exists(args.draws) and not args.rebuild:
            draws = np.load(args.draws)
            print(f"  reusing {len(draws)} draws from {args.draws}")
        else:
            draws = figs._bootstrap(P, D, Y, w, params,
                                    n_boot=args.nboot, seed=args.seed, kft_floor=1e-6)
            np.save(args.draws, draws)
    finally:
        vn.restore(saved)

    ok = ~np.isnan(draws).any(axis=1)
    n_failed = int((~ok).sum())
    print(f"  bootstrap samples converged: {ok.sum()} of {len(draws)}  (failed: {n_failed})")
    draws = draws[ok]

    # ── Table 1 check: all six parameters with percentile intervals ──────────
    print("\n  TABLE 1 — point estimate and 2.5/97.5 percentile interval")
    print(f"  {'param':>6} {'estimate':>12} {'2.5%':>12} {'97.5%':>12}   half-life (days)")
    for k in PO:
        col = draws[:, PO.index(k)]
        lo, hi = np.percentile(col, [2.5, 97.5])
        hl = ""
        if k.startswith("k_F"):
            f = lambda v: np.log(0.5) / np.log(1 - v)
            hl = f"{f(params[k]):.0f} ({f(hi):.0f}-{f(lo):.0f})"
        print(f"  {k:>6} {params[k]:>12.5g} {lo:>12.5g} {hi:>12.5g}   {hl}")
    print("  (half-life interval is inverted: the fast rate gives the short half-life)")

    # ── maintenance dose-response ────────────────────────────────────────────
    dose = np.linspace(0.01, 6, 300)
    joint = np.array([100 * steady_state(dose, d[PO.index("k_Lt")], d[PO.index("k_Ft")])
                      for d in draws])
    jlo, jhi = np.percentile(joint, [2.5, 97.5], axis=0)
    point = 100 * steady_state(dose, params["k_Lt"], params["k_Ft"])
    kft_lo, kft_hi = np.percentile(draws[:, PO.index("k_Ft")], [2.5, 97.5])
    swept_lo = 100 * steady_state(dose, params["k_Lt"], kft_hi)
    swept_hi = 100 * steady_state(dose, params["k_Lt"], kft_lo)

    print("\n  MAINTENANCE — steady-state % of ceiling")
    print(f"  {'min/day':>8} {'point':>7} {'joint 95%':>16} {'k_Ft sweep':>16}")
    for mins in (3, 4, 6, 8, 15):
        d = mins / MPG
        j = 100 * steady_state(d, draws[:, PO.index("k_Lt")], draws[:, PO.index("k_Ft")])
        jl, jh = np.percentile(j, [2.5, 97.5])
        sl = 100 * steady_state(d, params["k_Lt"], kft_hi)
        sh = 100 * steady_state(d, params["k_Lt"], kft_lo)
        print(f"  {mins:>8} {100*steady_state(d, params['k_Lt'], params['k_Ft']):>7.0f}"
              f" {jl:>7.0f}-{jh:<8.0f} {sl:>7.0f}-{sh:<8.0f}")

    # ── schedules ────────────────────────────────────────────────────────────
    sch = schedules()
    rows = []
    for d in draws:
        p = {k: d[PO.index(k)] for k in PO}
        row = {}
        for name, vec in sch.items():
            row[f"{name}_end"], row[f"{name}_mean"] = schedule_summary(p, vec)
        rows.append(row)
    tab = pd.DataFrame(rows)
    tab.to_csv(os.path.join(SCRATCH, "uncertainty.csv"), index=False)

    print("\n  SCHEDULES — % of that draw's ceiling")
    print(f"  {'schedule':>10} {'endpoint (95%)':>26} {'average (95%)':>26}")
    pt = {n: schedule_summary(params, v) for n, v in sch.items()}
    for name in ("even", "load", "boost"):
        e = np.percentile(tab[f"{name}_end"], [2.5, 97.5])
        m = np.percentile(tab[f"{name}_mean"], [2.5, 97.5])
        print(f"  {name:>10} {pt[name][0]:>8.0f} [{e[0]:.0f}, {e[1]:.0f}]"
              f"       {pt[name][1]:>8.0f} [{m[0]:.0f}, {m[1]:.0f}]")

    # ordering stability: how often does each criterion rank as reported?
    load_best_mean = (tab["load_mean"] > tab[["even_mean", "boost_mean"]].max(axis=1)).mean()
    even_best_end = (tab["even_end"] > tab[["load_end", "boost_end"]].max(axis=1)).mean()
    print(f"\n  load-and-maintain has the highest average in {100*load_best_mean:.0f}% of draws")
    print(f"  even use has the highest endpoint in    {100*even_best_end:.0f}% of draws")

    # ── figure ───────────────────────────────────────────────────────────────
    fig, (a0, a1) = plt.subplots(1, 2, figsize=(13, 5.2))
    a0.fill_between(dose * MPG, swept_lo, swept_hi, color="0.75", alpha=.45,
                    label="k_Ft swept, other parameters fixed")
    a0.fill_between(dose * MPG, jlo, jhi, color=figs.TEAL, alpha=.30,
                    label="joint 95% (bootstrap draws)")
    a0.plot(dose * MPG, point, color=figs.INK, lw=2.4, label="point estimate")
    a0.set_xlabel("Constant daily use (minutes)")
    a0.set_ylabel("Steady-state transfer held (% of ceiling)")
    a0.set_ylim(0, 102); a0.set_xlim(0, 6 * MPG); a0.grid(alpha=.3)
    a0.legend(loc="lower right", fontsize=9)
    a0.set_title("Maintenance dose-response", fontweight="bold")

    labels = {"even": "Even", "load": "Load + maintain", "boost": "Load + boosters"}
    xs = np.arange(3)
    for k, (crit, off) in enumerate((("end", -0.16), ("mean", 0.16))):
        vals = [tab[f"{n}_{crit}"] for n in ("even", "load", "boost")]
        lo = [np.percentile(v, 2.5) for v in vals]
        hi = [np.percentile(v, 97.5) for v in vals]
        pts = [pt[n][k] for n in ("even", "load", "boost")]
        a1.errorbar(xs + off, pts,
                    yerr=[np.array(pts) - lo, np.array(hi) - pts],
                    fmt="o", ms=7, capsize=5, lw=2,
                    color=figs.PURPLE if crit == "end" else figs.CORAL,
                    label="18-month endpoint" if crit == "end" else "18-month average")
    a1.set_xticks(xs); a1.set_xticklabels([labels[n] for n in ("even", "load", "boost")])
    a1.set_ylabel("Transfer (% of ceiling)"); a1.set_ylim(0, 102); a1.grid(alpha=.3)
    a1.legend(fontsize=9); a1.set_title("Schedule comparison at matched volume", fontweight="bold")

    fig.suptitle("Joint parameter uncertainty in the derived quantities "
                 f"({len(draws)} bootstrap draws)", fontweight="bold")
    fig.tight_layout()
    fig.savefig(args.out, dpi=ff.CONFIG["dpi"], bbox_inches="tight")
    print(f"\n  wrote {args.out}")


if __name__ == "__main__":
    main()
