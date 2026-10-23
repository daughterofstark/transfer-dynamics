import numpy as np, pandas as pd
import composite_extract as mnr

NIC = "data/short_intervals.csv"
raw = mnr._clean_cols(pd.read_csv(NIC, low_memory=False))
raw["t_res"] = pd.to_datetime(raw["tresult_created_at"], errors="coerce")
raw["gp"] = pd.to_numeric(raw["gameplays_between_test_runs"], errors="coerce")
info = raw.groupby("test_run_id").agg(ttype=("test_type", "first"), batt=("brainpower_test", "first"),
                                      t0=("t_res", "min"), gp=("gp", "max"))

run = mnr.build_nicole_composite(NIC, 3)
chains, lengths = mnr.build_chains(run)
gi_ids = set(pd.read_csv("data/newsubset.csv", usecols=["user_id"])["user_id"].astype(str))
ch = chains[chains["user_id"].map(lengths) >= 2].copy()
ch = ch[(ch.groupby("user_id")["nth_run"].transform("min") == 1)
        & ~ch["user_id"].astype(str).isin(gi_ids)]
ch = ch[ch["nth_test"] <= 5].join(info, on="test_run_id")

t1 = ch[ch.nth_test == 1].set_index("user_id"); t2 = ch[ch.nth_test == 2].set_index("user_id")
f = pd.DataFrame({"batt": t1["batt"], "types": t1["ttype"] + " -> " + t2["ttype"],
                  "days": (t2["t0"].dt.normalize() - t1["t0"].dt.normalize()).dt.days,
                  "plays": t2["gp"], "change": t2["composite"] - t1["composite"]}).dropna(subset=["days"])

def summ(g):
    return pd.Series({"n": len(g), "median days": g.days.median(), "same-day %": 100 * (g.days == 0).mean(),
                      "median gameplays": g.plays.median(), "mean change": g.change.mean()})

print("\n" + "=" * 70 + f"\n  FIT-ENTERING COMPOSITE PARTICIPANTS: {len(f):,}  (first interval)\n" + "=" * 70)
print("\n  by battery:")
print(f.groupby("batt").apply(summ).sort_values("n", ascending=False).head(15).round(1).to_string())
print("\n  by test types of the first two sittings:")
print(f.groupby("types").apply(summ).sort_values("n", ascending=False).round(1).to_string())
lab = f["batt"].str.lower()
print("\n  share of participants by battery family:")
for name, pat in [("reliability", "reliab"), ("rA/rC pre-post", r"^r[ac]_"), ("wmva", "wmva"),
                  ("subscriber/default", "subscriber|^default")]:
    print(f"    {name:20s}: {int(lab.str.contains(pat).sum()):>5,}")
