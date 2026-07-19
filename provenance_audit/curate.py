"""Curate a frame-built registry down to genuine research software.

The frame (topic search especially) drags in curated lists, books, courses, and
example/demo repos. Reviewing 100+ by hand is error-prone and not reproducible; this
filter does the bulk triage mechanically and leaves you only the genuine judgment calls.

It sorts each project into one of three buckets by name/topic/signal heuristics:
  - drop    : almost certainly not research software (awesome-*, *-examples, course, book...)
  - review  : ambiguous — YOU decide (writes a reason so you know why it was flagged)
  - keep    : looks like real software

Usage:
    python -m provenance_audit.curate --registry registry/corpus_100.yaml \
        --summary outputs/corpus_100/_summary.json --out-prefix registry/corpus

Writes:
    registry/corpus_keep.yaml     -> collect/score these
    registry/corpus_review.csv    -> eyeball these (~10-20 rows), move good ones into keep
    registry/corpus_drop.csv      -> what was removed + why (paste into methods section)

Nothing is deleted; you always see and can override every decision.
"""
from __future__ import annotations
import argparse
import csv
import json
import os
import re

import yaml

# Name/substring patterns that indicate NON-software (lists, docs, teaching material).
DROP_NAME_PATTERNS = [
    r"awesome[-_]", r"[-_]examples?$", r"[-_]demos?$", r"[-_]notebooks?$",
    r"^course$", r"[-_]course(s)?$", r"tutorial", r"[-_]book$", r"handbook",
    r"resources?$", r"cheat[-_]?sheet", r"roadmap", r"guide$", r"[-_]guide$",
    r"lecture", r"learning[-_]", r"how[-_]to", r"video[-_]courses?",
]
# Whole-name exact drops (specific known-noise repos seen in the frame).
DROP_EXACT = {
    "cs-video-courses", "Computer-Science-Resources", "quantumcomputingbook",
    "awesome-AI-books", "learning-cloud", "sevendayshpc", "distributed-training-guide",
    "How_to_optimize_in_GPU", "observer-patch-holography", "Quandoom",
}
# Off-topic-but-real software (not HPC/QC research software). Reviewed, not auto-kept.
OFFTOPIC_HINT = {
    "john": "password cracking, not HPC/QC",
    "metaflow": "ML-ops platform, not scientific computing",
    "tf-quant-finance": "quantitative finance, not HPC",
    "iot-master": "IoT platform",
    "wiretap": "security tooling, not HPC",
    "boinc": "volunteer-computing platform (keep only if in scope)",
    "libtommath": "general crypto math library",
    "Hamsters.js": "web worker library",
    "vectorious": "JS linear algebra micro-lib",
    "magnetron": "general tensor lib, unclear research use",
    "QuSimPy": "toy simulator",
    "QuantumComputing": "toy/demo simulator",
    "metal-flash-attention": "largely a writeup/kernel demo",
}


def classify(proj: dict, summ: dict) -> tuple[str, str]:
    name = proj.get("name", "")
    low = name.lower()

    if name in DROP_EXACT:
        return "drop", "known non-software (curated list/book/tutorial)"
    for pat in DROP_NAME_PATTERNS:
        if re.search(pat, low):
            return "drop", f"name matches non-software pattern /{pat}/"
    if name in OFFTOPIC_HINT:
        return "review", f"off-topic? {OFFTOPIC_HINT[name]}"

    # signal heuristic: no citation/security files AND no channels is weak, but not
    # decisive on its own -> flag for review rather than drop.
    files = summ.get("files", []) if summ else []
    channels = summ.get("channels", 0) if summ else 0
    if not files and channels == 0:
        return "review", "no CITATION/codemeta/SECURITY files and no channels detected"

    return "keep", ""


def main(argv=None):
    ap = argparse.ArgumentParser(description="Curate a frame registry into keep/review/drop.")
    ap.add_argument("--registry", required=True)
    ap.add_argument("--summary", help="outputs/<corpus>/_summary.json (optional but recommended)")
    ap.add_argument("--out-prefix", default="registry/corpus")
    args = ap.parse_args(argv)

    with open(args.registry) as f:
        projects = yaml.safe_load(f) or []
    summ_by_name = {}
    if args.summary and os.path.exists(args.summary):
        with open(args.summary) as f:
            for s in json.load(f):
                summ_by_name[s["name"]] = s

    keep, review, drop = [], [], []
    for p in projects:
        bucket, reason = classify(p, summ_by_name.get(p.get("name")))
        if bucket == "keep":
            keep.append(p)
        elif bucket == "review":
            review.append({"name": p.get("name"), "repo": p.get("repo"),
                           "domain": p.get("domain"), "reason": reason})
        else:
            drop.append({"name": p.get("name"), "repo": p.get("repo"),
                         "domain": p.get("domain"), "reason": reason})

    keep_path = f"{args.out_prefix}_keep.yaml"
    with open(keep_path, "w") as f:
        yaml.safe_dump(keep, f, sort_keys=False)
    for rows, suffix in [(review, "review"), (drop, "drop")]:
        with open(f"{args.out_prefix}_{suffix}.csv", "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["name", "repo", "domain", "reason"])
            w.writeheader(); w.writerows(rows)

    def dom_counts(items, key="domain"):
        c = {}
        for it in items:
            d = (it.get(key) if isinstance(it, dict) else None) or "?"
            c[d] = c.get(d, 0) + 1
        return c

    print(f"KEEP   {len(keep):>3}  {dom_counts(keep)}  -> {keep_path}")
    print(f"REVIEW {len(review):>3}  {dom_counts(review)}  -> {args.out_prefix}_review.csv  (eyeball these)")
    print(f"DROP   {len(drop):>3}  {dom_counts(drop)}  -> {args.out_prefix}_drop.csv  (methods-section record)")
    print("\nNext: open the review CSV, and for any project that IS in-scope research")
    print("software, copy its row into corpus_keep.yaml (name/repo/domain/discipline/ecosystem).")


if __name__ == "__main__":
    main()
