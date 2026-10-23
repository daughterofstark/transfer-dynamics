import numpy as np, pandas as pd
import composite_extract as mnr

raw = mnr._clean_cols(pd.read_csv("data/short_intervals.csv", low_memory=False))
for c in ["days_between_test_runs", "gameplays_between_test_runs", "nth_run"]:
    raw[c] = pd.to_numeric(raw[c], errors="coerce")
raw["t_res"] = pd.to_datetime(raw["tresult_created_at"], errors="coerce")
raw["t_run"] = pd.to_datetime(raw["trun_created_at"], errors="coerce")
raw["t_done"] = pd.to_datetime(raw["trun_completed_at"], errors="coerce")

pos = lambda s: s[s.fillna(0) > 0]
run = raw.groupby("test_run_id").agg(
    user=("user_id", "first"), nth=("nth_run", "first"),
    t_run=("t_run", "first"), t_done=("t_done", "first"),
    t_res0=("t_res", "min"), t_res1=("t_res", "max"),
    d_max=("days_between_test_runs", "max"),
    d_nu=("days_between_test_runs", lambda s: pos(s).nunique()),
    p_max=("gameplays_between_test_runs", "max"),
    p_nu=("gameplays_between_test_runs", lambda s: pos(s).nunique()),
).reset_index()

print("\n" + "=" * 66 + "\n  A. HOW LONG A SITTING TAKES (days)\n" + "=" * 66)
for lab, a, b in [("created -> completed", "t_run", "t_done"),
                  ("created -> first result", "t_run", "t_res0"),
                  ("first -> last result", "t_res0", "t_res1")]:
    d = (run[b] - run[a]).dt.total_seconds() / 86400
    print(f"  {lab:24s}: median {d.median():7.3f}  p99 {d.quantile(.99):8.2f}  "
          f"> 1 day {int((d > 1).sum()):>5,}  missing {int(d.isna().sum()):>5,}")

print("\n" + "=" * 66 + "\n  B. AMBIGUITY IN THE STORED BETWEEN-COLUMNS\n" + "=" * 66)
print(f"  sittings with >1 distinct non-zero days_between   : {int((run.d_nu > 1).sum()):,}")
print(f"  sittings with >1 distinct non-zero gameplays      : {int((run.p_nu > 1).sum()):,}")

run = run.sort_values(["user", "nth"])
gu = run.groupby("user")
run["prev_nth"] = gu["nth"].shift()
for c in ["t_run", "t_res0", "t_done"]:
    run[f"cd_{c}"] = (run[c].dt.normalize() - gu[c].shift().dt.normalize()).dt.days
pair = run[run["nth"] - run["prev_nth"] == 1].copy()
pair["d_store"] = pair["d_max"].fillna(0)

print("\n" + "=" * 66 + f"\n  C. CONSECUTIVE SITTINGS: n = {len(pair):,}\n" + "=" * 66)
print(f"  {'interval from':22s} {'= stored max':>13s} {'within 1 d':>11s} {'same-day':>9s} {'missing':>8s}")
for c, lab in [("cd_t_run", "created timestamps"), ("cd_t_res0", "first-result times"),
               ("cd_t_done", "completed timestamps")]:
    x = pair[c]
    print(f"  {lab:22s} {int((x == pair.d_store).sum()):>13,} "
          f"{int(((x - pair.d_store).abs() <= 1).sum()):>11,} "
          f"{int((x == 0).sum()):>9,} {int(x.isna().sum()):>8,}")
print(f"  {'stored max (for ref)':22s} {'':>13s} {'':>11s} {int((pair.d_store == 0).sum()):>9,}")

dis = pair[(pair.cd_t_res0 - pair.d_store).abs() > 1]
print(f"\n  first-result interval disagrees with stored max by > 1 day: {len(dis):,}")
print(dis[["user", "nth", "t_run", "t_res0", "t_done", "d_store", "cd_t_run",
           "cd_t_res0", "cd_t_done", "p_max"]].head(8).to_string(index=False))

print("\n" + "=" * 66 + "\n  D. GAMEPLAYS on consecutive sittings\n" + "=" * 66)
print(f"  stored max gameplays: zero {int((pair.p_max.fillna(0) == 0).sum()):,}   "
      f"positive {int((pair.p_max.fillna(0) > 0).sum()):,}")
sd = pair.cd_t_res0 == 0
print(f"  same-day pairs (first-result times): {int(sd.sum()):,}   "
      f"of which zero gameplays: {int((sd & (pair.p_max.fillna(0) == 0)).sum()):,}")
