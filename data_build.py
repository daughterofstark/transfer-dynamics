"""Build analysis inputs; reuse only a cache matching inputs, policy and builder code."""
from __future__ import annotations
import os
import hashlib
import json
from pathlib import Path
import pandas as pd
import paper_pipeline as pp

SCRATCH = "_verify_scratch"


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def build_identity(args):
    root = Path(__file__).resolve().parent
    return dict(schema=1,
                inputs={"grand_index": sha256(args.data), "composite": sha256(args.composite)},
                settings=dict(min_valid_subtests=args.min_valid_subtests, uid_prefix=args.uid_prefix,
                              gi_battery_policy=getattr(args, "gi_battery_policy", "same-battery")),
                code={name: sha256(root / name) for name in
                      ("data_build.py", "paper_pipeline.py", "composite_extract.py")})


def build_merged_once(args):
    """Return (grand_index_frame, merged_frame). args: data, composite, min_valid_subtests, uid_prefix, rebuild."""
    os.makedirs(SCRATCH, exist_ok=True)
    cache, orig = os.path.join(SCRATCH, "merged_cache.csv"), os.path.join(SCRATCH, "orig_cache.csv")
    manifest = Path(SCRATCH) / "manifest.json"
    identity = build_identity(args)
    if os.path.exists(cache) and os.path.exists(orig) and manifest.exists() and not args.rebuild:
        try:
            saved = json.loads(manifest.read_text())
        except (ValueError, OSError):
            saved = {}
        if (saved.get("identity") == identity and
                saved.get("outputs") == {"merged": sha256(cache), "grand_index": sha256(orig)}):
            print("  (using verified cache: inputs, policy and builder code match)")
            return pd.read_csv(orig, low_memory=False), pd.read_csv(cache, low_memory=False)
    newsub, merged = pp.build_merged(args.data, args.composite, args.min_valid_subtests,
                                    args.uid_prefix, cache,
                                    gi_battery_policy=identity["settings"]["gi_battery_policy"])
    newsub.to_csv(orig, index=False)
    payload = dict(identity=identity, outputs={"merged": sha256(cache), "grand_index": sha256(orig)})
    tmp = manifest.with_suffix(".tmp")
    tmp.write_text(json.dumps(payload, indent=2) + "\n")
    tmp.replace(manifest)
    return newsub, merged
