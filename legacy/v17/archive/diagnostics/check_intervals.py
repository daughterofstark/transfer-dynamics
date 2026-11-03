import os
import numpy as np, pandas as pd
import composite_extract as mnr

raw = mnr._clean_cols(pd.read_csv("data/short_intervals.csv", low_memory=False))
for c in ["days_between_test_runs", "gameplays_between_test_runs", "nth_run"]:
    raw[c] = pd.to_numeric(raw[c], errors="coerce")

print("\n" + "=" * 64 + "\n  A. FIELDS THAT SHOULD BE CONSTANT WITHIN A SITTING\n" + "=" * 64)
g = raw.groupby("test_run_id")
for c in ["user_id", "brainpower_test_id", "nth_run", "days_between_test_runs",
          "gameplays_between_test_runs", "trun_created_at", "prev_trun_created_at"]:
    if c in raw.columns:
        nu = g[c].nunique(dropna=False)
        print(f"  {c:30s}: {int((nu > 1).sum()):>6,} of {len(nu):,} runs have >1 distinct value")

print("\n  days_between_test_runs values:")
print(raw["days_between_test_runs"].describe().to_string())
var = g["days_between_test_runs"].nunique(dropna=False)
ex = var[var > 1].index[:3]
cols = [c for c in ["test_run_id", "test_section_id", "tresult_created_at", "trun_created_at",
                    "prev_trun_created_at", "days_between_test_runs", "gameplays_between_test_runs"]
        if c in raw.columns]
if len(ex):
    print("\n  example sittings where days_between varies:")
    print(raw[raw["test_run_id"].isin(ex)][cols].sort_values(cols[:3]).to_string(index=False))

print("\n" + "=" * 64 + "\n  B. STORED DAYS vs RUN TIMESTAMPS\n" + "=" * 64)
r = g.agg(trun=("trun_created_at", "first"), prev=("prev_trun_created_at", "first"),
          dmin=("days_between_test_runs", "min"), dmax=("days_between_test_runs", "max"))
r["ts_days"] = (pd.to_datetime(r["trun"], errors="coerce")
                - pd.to_datetime(r["prev"], errors="coerce")).dt.total_seconds() / 86400
ok = r["ts_days"].notna()
print(f"  runs with both timestamps             : {int(ok.sum()):,}")
print(f"  stored min  == floor(timestamp diff)  : {int((r.loc[ok,'dmin'] == np.floor(r.loc[ok,'ts_days'])).sum()):,}")
print(f"  stored max  == floor(timestamp diff)  : {int((r.loc[ok,'dmax'] == np.floor(r.loc[ok,'ts_days'])).sum()):,}")
print(f"  timestamp diff < 1 day                : {int((r.loc[ok,'ts_days'] < 1).sum()):,}")
print(f"  stored min == 0                       : {int((r['dmin'] == 0).sum()):,}")
print(f"  stored max == 0                       : {int((r['dmax'] == 0).sum()):,}")

print("\n" + "=" * 64 + "\n  C. OLD vs NEW FIRST INTERVAL, composite participants kept in both\n" + "=" * 64)
old_p, new_p = "out/merged_for_fit.csv", "_verify_scratch/merged_cache.csv"
if os.path.exists(old_p) and os.path.exists(new_p):
    def t2(p):
        d = pd.read_csv(p, low_memory=False, usecols=["user_id", "nth_test", "days_since_signup"])
        d = d[d["user_id"].astype(str).str.startswith("NIC_") & (d["nth_test"] == 2)]
        return d.set_index(d["user_id"].astype(str))["days_since_signup"]
    o, n = t2(old_p), t2(new_p)
    j = pd.concat([o.rename("old"), n.rename("new")], axis=1, join="inner")
    print(f"  participants in both builds : {len(j):,}")
    print(f"  first interval changed      : {int((j.old != j.new).sum()):,}")
    print("  same-day (old) x same-day (new):")
    print(pd.crosstab(j.old == 0, j.new == 0, rownames=["old 0 d"], colnames=["new 0 d"]).to_string())
    print("\n  examples of changed intervals:")
    print(j[j.old != j.new].head(8).to_string())
else:
    print(f"  missing file(s): {[p for p in (old_p, new_p) if not os.path.exists(p)]}")
