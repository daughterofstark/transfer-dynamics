import pandas as pd
import composite_extract as mnr

NICOLE = "data/short_intervals.csv"
GI = "data/newsubset.csv"

raw = mnr._clean_cols(pd.read_csv(NICOLE))
raw["nth_run"] = pd.to_numeric(raw["nth_run"], errors="coerce")

run = mnr.build_nicole_composite(NICOLE, 3)
chains, lengths = mnr.build_chains(run)
kept = lengths[lengths >= 2].index
first_chain = (chains[(chains["nth_test"] == 1) & chains["user_id"].isin(kept)]
               .set_index("user_id")["nth_run"])
first_any = raw.groupby("user_id")["nth_run"].min()
late = first_chain > first_any.reindex(first_chain.index)

gi = pd.read_csv(GI, usecols=["user_id"])
both = set(gi["user_id"].astype(str)) & set(raw["user_id"].astype(str))

print("\n" + "=" * 60)
print("  DATA CHECK RESULTS")
print("=" * 60)
print(f"  duplicate (run, subtest) rows            : "
      f"{int(raw.duplicated(['test_run_id', 'test_section_id']).sum()):,}")
print(f"  kept chains (>=2 runs)                   : {len(first_chain):,}")
print(f"  ...starting after the first run in file  : {int(late.sum()):,}")
print(f"  ...whose first run has nth_run > 1       : {int((first_chain > 1).sum()):,}")
print(f"  participants in both files               : {len(both):,}")
