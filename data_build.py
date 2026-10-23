"""
data_build.py - build, or reuse, the merged analysis dataset (cached in _verify_scratch/).
The cache is not keyed to the inputs: pass --rebuild after changing inputs or data-building code.
"""
from __future__ import annotations
import os
import pandas as pd
import paper_pipeline as pp

SCRATCH = "_verify_scratch"


def build_merged_once(args):
    """Return (grand_index_frame, merged_frame). args: data, composite, min_valid_subtests, uid_prefix, rebuild."""
    os.makedirs(SCRATCH, exist_ok=True)
    cache, orig = os.path.join(SCRATCH, "merged_cache.csv"), os.path.join(SCRATCH, "orig_cache.csv")
    if os.path.exists(cache) and os.path.exists(orig) and not args.rebuild:
        print("  (using cached merged data; pass --rebuild to force)")
        return pd.read_csv(orig, low_memory=False), pd.read_csv(cache, low_memory=False)
    newsub, merged = pp.build_merged(args.data, args.composite, args.min_valid_subtests, args.uid_prefix, cache)
    newsub.to_csv(orig, index=False)
    return newsub, merged
