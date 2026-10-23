import numpy as np, pandas as pd
import composite_extract as mnr

NIC = "data/short_intervals.csv"
raw = mnr._clean_cols(pd.read_csv(NIC, low_memory=False))
raw["t_res"] = pd.to_datetime(raw["tresult_created_at"], errors="coerce")
raw["gp"] = pd.to_numeric(raw["gameplays_between_test_runs"], errors="coerce")
info = raw.groupby("test_run_id").agg(batt=("brainpower_test", "first"), t0=("t_res", "min"), gp=("gp", "max"))
run = mnr.build_nicole_composite(NIC, 3)
chains, lengths = mnr.build_chains(run)
ch = chains[chains["user_id"].map(lengths) >= 2].join(info, on="test_run_id")
t1 = ch[ch.nth_test == 1].set_index("user_id"); t2 = ch[ch.nth_test == 2].set_index("user_id")
true = pd.DataFrame({"batt": t1["batt"],
                     "days": (t2["t0"].dt.normalize() - t1["t0"].dt.normalize()).dt.days,
                     "plays": t2["gp"]})
true.index = "NIC_" + true.index.astype(str)

old = pd.read_csv("out/merged_for_fit.csv", low_memory=False,
                  usecols=["user_id", "nth_test", "days_since_signup", "num_plays_before"])
old = old[old["user_id"].astype(str).str.startswith("NIC_") & (old["nth_test"] == 2)]
old = old.set_index(old["user_id"].astype(str))[["days_since_signup", "num_plays_before"]]
j = true.join(old, how="inner").dropna(subset=["days"])

b = j["batt"].str.lower()
j["family"] = np.select([b.str.contains("reliab"), b.str.contains("subscriber|^default"),
                         b.str.contains("wmva"), b.str.contains("clinic")],
                        ["reliability", "routine", "wmva", "in-clinic"], "other study")
j["true_days"] = pd.cut(j["days"], [-1, 1, 69, 1e5], labels=["<=1 d", "2-69 d", ">=70 d"])

print("\n" + "=" * 68 + f"\n  V16 BUILD vs TRUE FIRST INTERVAL  (n = {len(j):,})\n" + "=" * 68)
print("\n  v16 recorded 0 days, by family and true interval:")
z = j[j["days_since_signup"] == 0]
print(pd.crosstab(z["family"], z["true_days"], margins=True).to_string())
print(f"\n  v16 recorded 0 days but true interval >= 2 days : {int((z['days'] >= 2).sum()):,}")
print(f"  ...of whom v16 also recorded 0 gameplays        : {int(((z['days'] >= 2) & (z['num_plays_before'] == 0)).sum()):,}")
print(f"  ...median true gameplays for that group         : {z.loc[z['days'] >= 2, 'plays'].median():.0f}")
print(f"\n  v16 interval exactly right (same calendar days) : {int((j['days_since_signup'] == j['days']).sum()):,}")
