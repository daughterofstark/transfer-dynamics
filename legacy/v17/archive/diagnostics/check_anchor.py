import numpy as np, pandas as pd
import composite_extract as mnr

raw = mnr._clean_cols(pd.read_csv("data/short_intervals.csv", low_memory=False))
raw["t_run"] = pd.to_datetime(raw["trun_created_at"], errors="coerce")
raw["t_res"] = pd.to_datetime(raw["tresult_created_at"], errors="coerce")
runs = raw.groupby(raw["test_run_id"].astype(str)).agg(t_run=("t_run", "first"), t_res0=("t_res", "min"))
runs["span"] = (runs.t_res0 - runs.t_run).dt.total_seconds() / 86400

print("\n" + "=" * 64 + "\n  A. WHICH TIMESTAMP DO GRAND INDEX INTERVALS USE?\n" + "=" * 64)
gi = mnr._clean_cols(pd.read_csv("data/newsubset.csv", low_memory=False))
gi["test_run_id"] = gi["test_run_id"].astype(str)
gi = gi.sort_values(["user_id", "nth_test"])
gi["gi_d"] = gi.groupby("user_id")["days_since_signup"].diff()
gi["prev_run"] = gi.groupby("user_id")["test_run_id"].shift()
m = (gi.dropna(subset=["prev_run"]).join(runs, on="test_run_id")
       .join(runs.add_suffix("_prev"), on="prev_run").dropna(subset=["t_run", "t_run_prev"]))
cd_run = (m.t_run.dt.normalize() - m.t_run_prev.dt.normalize()).dt.days
cd_res = (m.t_res0.dt.normalize() - m.t_res0_prev.dt.normalize()).dt.days
print(f"  Grand Index intervals whose two sittings are in the composite file: {len(m):,}")
print(f"  GI interval = created-time difference      : {int((cd_run == m.gi_d).sum()):,}")
print(f"  GI interval = first-result-time difference : {int((cd_res == m.gi_d).sum()):,}")
print(f"  GI days_since_signup non-integer values    : {int((gi.days_since_signup % 1 != 0).sum()):,}")

print("\n" + "=" * 64 + "\n  B. FIT-ENTERING COMPOSITE PARTICIPANTS WITH A MULTI-DAY SITTING\n" + "=" * 64)
mg = pd.read_csv("_verify_scratch/merged_cache.csv", low_memory=False)
nic = mg[mg["user_id"].astype(str).str.startswith("NIC_") & (pd.to_numeric(mg["nth_test"]) <= 5)].copy()
nic["span"] = nic["test_run_id"].astype(str).map(runs["span"])
per = nic.groupby("user_id")["span"].max()
print(f"  composite participants in the fit          : {per.size:,}")
print(f"  ...with any sitting taken > 1 day after it was created  : {int((per > 1).sum()):,}")
print(f"  ...with any sitting taken > 7 days after it was created : {int((per > 7).sum()):,}")
t2 = mg[mg["user_id"].astype(str).str.startswith("NIC_") & (mg["nth_test"] == 2)]
print(f"  same-day first intervals among composite participants   : {int((t2.days_since_signup == 0).sum()):,}")
