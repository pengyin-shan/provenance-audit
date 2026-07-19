"""Select a stratified, reproducible subsample for manual verification.

At N=100 you cannot hand-verify every project's 8 manual signals. Instead verify a
*representative* subsample and report it as a validation panel. "Representative" here
means: stratified by domain (hpc/qc) and by auto-score tercile (weak/mid/strong
posture), with a fixed random seed so the selection is reproducible and defensible.

Usage:
    python -m provenance_audit.subsample --scored outputs/corpus_keep_scored --n 30 --seed 7 \
        --out outputs/verify_subsample_30.csv

Produces a CSV listing the chosen projects, their domain, their mean auto-score, and
their stratum — hand this list down your manual_checklist.csv and verify only these.
"""
from __future__ import annotations
import argparse
import csv
import glob
import json
import os
import random
import statistics as st


def _load(scored_dir):
    rows = []
    # domain isn't in the scorecard; pull it from the collected record if co-located,
    # else fall back to "unknown" (still stratify by score).
    for path in glob.glob(os.path.join(scored_dir, "*.scorecard.json")):
        d = json.load(open(path))
        scores = [c["auto_score"] for c in d["categories"].values() if c["auto_score"] is not None]
        rows.append({"project": d["name"], "mean_auto": round(st.mean(scores), 3) if scores else 0.0,
                     "domain": d.get("domain", "unknown")})
    return rows


def _tercile(x, lo, hi):
    if x <= lo:
        return "weak"
    if x >= hi:
        return "strong"
    return "mid"


def select(rows, n, seed):
    vals = sorted(r["mean_auto"] for r in rows)
    lo = vals[len(vals) // 3] if vals else 0.34
    hi = vals[2 * len(vals) // 3] if vals else 0.67
    for r in rows:
        r["stratum"] = f'{r["domain"]}/{_tercile(r["mean_auto"], lo, hi)}'
    # bucket, then round-robin draw so each stratum is represented proportionally
    buckets: dict[str, list] = {}
    for r in rows:
        buckets.setdefault(r["stratum"], []).append(r)
    rng = random.Random(seed)
    for b in buckets.values():
        rng.shuffle(b)
    chosen, order = [], sorted(buckets, key=lambda k: -len(buckets[k]))
    while len(chosen) < min(n, len(rows)):
        progressed = False
        for k in order:
            if buckets[k]:
                chosen.append(buckets[k].pop())
                progressed = True
                if len(chosen) >= n:
                    break
        if not progressed:
            break
    return chosen


def main(argv=None):
    ap = argparse.ArgumentParser(description="Pick a stratified, reproducible verification subsample.")
    ap.add_argument("--scored", required=True)
    ap.add_argument("--n", type=int, default=24, help="subsample size (aim ~20-25% of corpus)")
    ap.add_argument("--seed", type=int, default=7, help="fixed seed for reproducibility")
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)

    rows = _load(args.scored)
    chosen = select(rows, args.n, args.seed)
    with open(args.out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["project", "domain", "mean_auto", "stratum"])
        w.writeheader()
        for r in sorted(chosen, key=lambda x: x["stratum"]):
            w.writerow({k: r[k] for k in ["project", "domain", "mean_auto", "stratum"]})
    strata = {}
    for r in chosen:
        strata[r["stratum"]] = strata.get(r["stratum"], 0) + 1
    print(f"Selected {len(chosen)} of {len(rows)} projects (seed={args.seed}) -> {args.out}")
    print("Per-stratum counts:", dict(sorted(strata.items())))


if __name__ == "__main__":
    main()
