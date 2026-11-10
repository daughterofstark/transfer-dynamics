import pandas as pd
import composite_extract as mnr

raw = mnr._clean_cols(pd.read_csv("data/short_intervals.csv", low_memory=False))
gi = mnr._clean_cols(pd.read_csv("data/newsubset.csv", low_memory=False))
raw["uid"] = raw["user_id"].astype(str); gi["uid"] = gi["user_id"].astype(str)

print("\n" + "=" * 60 + "\n  A. DUPLICATE (run, subtest) ROWS\n" + "=" * 60)
d = raw[raw.duplicated(["test_run_id", "test_section_id"], keep=False)]
cols = [c for c in ["user_id", "test_run_id", "test_section_id", "nth_run", "index_score",
                    "score", "tresult_created_at"] if c in d.columns]
print(d[cols].sort_values(["test_run_id", "test_section_id"]).to_string(index=False))

run = mnr.build_nicole_composite("data/short_intervals.csv", 3)
chains, lengths = mnr.build_chains(run)
kept = set(lengths[lengths >= 2].index.astype(str))
both_all = set(gi["uid"]) & set(raw["uid"])
both = both_all & kept

print("\n" + "=" * 60 + "\n  B. PARTICIPANTS IN BOTH FILES\n" + "=" * 60)
print(f"  in both files (any composite record) : {len(both_all):,}")
print(f"  ...of whom enter the fit (chain >= 2) : {len(both):,}")
shared = set(gi["test_run_id"].dropna().astype(str)) & set(raw["test_run_id"].dropna().astype(str))
print(f"  test_run_ids present in both files    : {len(shared):,}")

g = gi[gi["uid"].isin(both)].copy()
g["date"] = (pd.to_datetime(g["signup_date"], errors="coerce").dt.tz_localize(None)
             + pd.to_timedelta(pd.to_numeric(g["days_since_signup"], errors="coerce"), unit="D"))
r = raw[raw["uid"].isin(both)].copy()
r["date"] = pd.to_datetime(r["trun_created_at"], errors="coerce").dt.tz_localize(None)

G = g.groupby("uid").agg(signup=("signup_date", "first"), gender=("gender", "first"),
                         age=("age", "first"), first=("date", "min"), last=("date", "max"))
R = r.groupby("uid").agg(signup=("signup_date", "first"), gender=("gender", "first"),
                         age=("age_at_signup", "first"), first=("date", "min"), last=("date", "max"))
M = G.join(R, lsuffix="_gi", rsuffix="_comp")

same_signup = M["signup_gi"].astype(str).str[:10] == M["signup_comp"].astype(str).str[:10]
print(f"  same signup date in both files        : {int(same_signup.sum()):,} of {len(M):,}")
print("  gender, GI file vs composite file:")
print(pd.crosstab(M["gender_gi"].astype(str), M["gender_comp"].astype(str)).to_string())
print(f"  age differs by <= 1 year              : "
      f"{int(((pd.to_numeric(M['age_gi'], errors='coerce') - pd.to_numeric(M['age_comp'], errors='coerce')).abs() <= 1).sum()):,}")

before = M["last_comp"] < M["first_gi"]
after = M["first_comp"] > M["last_gi"]
print("  timing of composite records relative to Grand Index records:")
print(f"    all composite runs BEFORE first GI run : {int(before.sum()):,}")
print(f"    all composite runs AFTER last GI run   : {int(after.sum()):,}")
print(f"    overlapping                            : {int((~before & ~after & M['first_comp'].notna() & M['first_gi'].notna()).sum()):,}")
print(f"    dates missing                          : {int((M['first_comp'].isna() | M['first_gi'].isna()).sum()):,}")
print("\n  first 5 examples:")
print(M.head().to_string())
