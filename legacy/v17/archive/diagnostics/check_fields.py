import numpy as np, pandas as pd
import composite_extract as mnr

raw = mnr._clean_cols(pd.read_csv("data/short_intervals.csv", low_memory=False))
raw["nth_run"] = pd.to_numeric(raw["nth_run"], errors="coerce")
raw["nth_run_specific"] = pd.to_numeric(raw["nth_run_specific"], errors="coerce")
run = raw.groupby("test_run_id").agg(user=("user_id", "first"), ttype=("test_type", "first"),
                                     batt=("brainpower_test", "first"), bid=("brainpower_test_id", "first"),
                                     nth=("nth_run", "first"), nths=("nth_run_specific", "first"))

print("\n" + "=" * 64 + "\n  A. TEST TYPES AND BATTERIES (per sitting)\n" + "=" * 64)
print(run["ttype"].value_counts(dropna=False).to_string())
print("\n  test type by position in participant's sequence (NTH_RUN, 5 = 5+):")
print(pd.crosstab(run["nth"].clip(upper=5), run["ttype"]).to_string())
print(f"\n  participants with more than one test type: {int((run.groupby('user').ttype.nunique() > 1).sum()):,}")
print("\n  most common batteries:")
print(run["batt"].value_counts().head(12).to_string())

print("\n" + "=" * 64 + "\n  B. NTH_RUN vs NTH_RUN_SPECIFIC\n" + "=" * 64)
print(f"  sittings where they are equal: {int((run.nth == run.nths).sum()):,} of {len(run):,}")
r = run.sort_values(["user", "nth"])
r["nths_expected"] = r.groupby(["user", "bid"]).cumcount() + 1
print(f"  NTH_RUN_SPECIFIC = count within battery : {int((r.nths == r.nths_expected).sum()):,}")
r["nth_expected"] = r.groupby("user").cumcount() + 1
print(f"  NTH_RUN = count across all sittings      : {int((r.nth == r.nth_expected).sum()):,}")

print("\n" + "=" * 64 + "\n  C. GAMEPLAY ANCHOR (participants in both files)\n" + "=" * 64)
gi = mnr._clean_cols(pd.read_csv("data/newsubset.csv", low_memory=False))
gi["num_plays_before"] = pd.to_numeric(gi["num_plays_before"], errors="coerce")
gi = gi.sort_values(["user_id", "nth_test"])
gi["test_run_id"] = gi["test_run_id"].astype(str)
gi["prev_run"] = gi.groupby("user_id")["test_run_id"].shift()
gi["gi_plays"] = gi.groupby("user_id")["num_plays_before"].diff()
raw["gp"] = pd.to_numeric(raw["gameplays_between_test_runs"], errors="coerce")
gp = raw.groupby(raw["test_run_id"].astype(str))["gp"].max()
m = gi.dropna(subset=["prev_run", "gi_plays"]).copy()
m["comp_plays"] = m["test_run_id"].map(gp)
m = m.dropna(subset=["comp_plays"])
d = (m.comp_plays - m.gi_plays).abs()
print(f"  sitting pairs in both files  : {len(m):,}")
print(f"  identical gameplay counts    : {int((d == 0).sum()):,}")
print(f"  within 5 gameplays           : {int((d <= 5).sum()):,}")
print(f"  correlation                  : {m.comp_plays.corr(m.gi_plays):.3f}")
print("\n  Grand Index created_at, first 5 values as stored:", gi["created_at"].head().tolist())
