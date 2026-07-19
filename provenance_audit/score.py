"""Channel-provenance scoring head.

Reads the per-project JSON records produced by collect.py, evaluates each against
the four-category framework, and writes:
  - <project>.scorecard.json   per-project signal results + per-category auto-score
  - matrix.csv                 projects x 4 categories (auto-score 0-1) -> the poster heatmap
  - manual_checklist.csv       every "manual" signal still needing human verification
  - gap_analysis.json          signals unique to this framework vs. covered by existing tools

Usage:
    python -m provenance_audit.score --in outputs/corpus_keep --out outputs/corpus_keep_scored

"auto" signals are computed here. "manual" signals are emitted as checklist items
(value null) for you to fill during ground-truth verification; rerun any time.
"""
from __future__ import annotations
import argparse
import csv
import glob
import json
import os

from .framework import FRAMEWORK, all_signals


# ---- auto signal detectors: each takes the collected record, returns True/False/None ----

def _files(rec):
    return (rec.get("github") or {}).get("files", {})

def _gt(rec, field):
    g = (rec.get("ground_truth") or {}).get(field) or {}
    return g.get("value")

def _has_stable_release(rec):
    gh = rec.get("github") or {}
    state = gh.get("release_state")
    if state is not None:
        return state == "release"          # prerelease_only / none both count as absent
    return bool(gh.get("latest_release"))  # fallback for records collected before this field

DETECTORS = {
    "multi_maintainer":  lambda r: bool(_gt(r, "maintainers")) and len(_gt(r, "maintainers") or []) >= 2,
    "contributing_doc":  lambda r: "CONTRIBUTING.md" in _files(r),
    "governance_doc":    lambda r: "GOVERNANCE.md" in _files(r),
    "channels_declared": lambda r: len((r.get("channels") or {})) > 0,
    "channels_documented": lambda r: len((r.get("channels") or {})) > 0,  # scanned from README/homepage
    "security_policy":   lambda r: bool((r.get("github") or {}).get("has_security_md")),
    "changelog":         lambda r: "CHANGELOG.md" in _files(r),
    "release_notes":     lambda r: _has_stable_release(r),
    "has_release":       lambda r: _has_stable_release(r),
    "archival_doi":      lambda r: bool(_gt(r, "citation_doi")),
}


# Signals whose truth depends on a specific collection step. If that step recorded
# an error, the signal is UNKNOWN (excluded from scoring), not absent.
RELEASE_DEPENDENT = {"has_release", "release_notes"}


def _collection_failed(rec, sig_id: str) -> bool:
    errs = (rec.get("github") or {}).get("errors", {}) or {}
    if "repo" in errs:
        return True  # nothing GitHub-derived is trustworthy
    if sig_id in RELEASE_DEPENDENT and "latest_release" in errs:
        return True
    return False


def score_record(rec: dict) -> dict:
    name = rec.get("name")
    cats = {}
    for cat_id, cat in FRAMEWORK.items():
        signals = {}
        auto_present = auto_total = 0
        for sig_id, sig in cat["signals"].items():
            if sig["detect"] == "auto":
                if _collection_failed(rec, sig_id):
                    signals[sig_id] = {"status": "unknown_collection_error", "detect": "auto"}
                    continue  # excluded from numerator AND denominator
                det = DETECTORS.get(sig_id)
                val = bool(det(rec)) if det else None
                signals[sig_id] = {"status": "present" if val else "absent", "detect": "auto"}
                auto_total += 1
                auto_present += 1 if val else 0
            else:
                signals[sig_id] = {"status": "manual_unverified", "detect": "manual",
                                   "covered_by": sig["covered_by"]}
        cats[cat_id] = {
            "label": cat["label"],
            "auto_score": round(auto_present / auto_total, 2) if auto_total else None,
            "auto_present": auto_present,
            "auto_total": auto_total,
            "signals": signals,
        }
    return {"name": name, "domain": rec.get("domain"), "categories": cats}


def gap_analysis() -> dict:
    unique, covered = [], []
    for cat_id, sig_id, sig in all_signals():
        entry = {"category": cat_id, "signal": sig_id, "covered_by": sig["covered_by"]}
        (covered if sig["covered_by"] else unique).append(entry)
    return {
        "unique_to_channel_framework": unique,
        "covered_by_existing_tools": covered,
        "summary": (f"{len(unique)} of {len(unique)+len(covered)} framework signals are not "
                    f"assessed by any existing tool (Scorecard/SLSA/Sigstore); these are the "
                    f"channel framework's unique contribution."),
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description="Score collected records against the channel-provenance framework.")
    ap.add_argument("--in", dest="indir", required=True, help="dir of collected <project>.json")
    ap.add_argument("--out", dest="outdir", required=True, help="output dir for scorecards + matrix")
    args = ap.parse_args(argv)
    os.makedirs(args.outdir, exist_ok=True)

    records = []
    for path in sorted(glob.glob(os.path.join(args.indir, "*.json"))):
        if os.path.basename(path).startswith("_"):
            continue
        with open(path) as f:
            records.append(json.load(f))

    cat_ids = list(FRAMEWORK.keys())
    matrix_rows, checklist_rows = [], []
    for rec in records:
        sc = score_record(rec)
        with open(os.path.join(args.outdir, f"{(sc['name'] or 'unknown').replace('/', '_')}.scorecard.json"), "w") as f:
            json.dump(sc, f, indent=2)
        row = {"project": sc["name"]}
        for cid in cat_ids:
            row[FRAMEWORK[cid]["label"]] = sc["categories"][cid]["auto_score"]
        matrix_rows.append(row)
        for cid in cat_ids:
            for sig_id, s in sc["categories"][cid]["signals"].items():
                if s["detect"] == "manual":
                    checklist_rows.append({"project": sc["name"], "category": FRAMEWORK[cid]["label"],
                                           "signal": sig_id, "covered_by": s.get("covered_by", ""),
                                           "verified_value": ""})

    with open(os.path.join(args.outdir, "matrix.csv"), "w", newline="") as f:
        cols = ["project"] + [FRAMEWORK[c]["label"] for c in cat_ids]
        w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(matrix_rows)

    with open(os.path.join(args.outdir, "manual_checklist.csv"), "w", newline="") as f:
        cols = ["project", "category", "signal", "covered_by", "verified_value"]
        w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(checklist_rows)

    gaps = gap_analysis()
    with open(os.path.join(args.outdir, "gap_analysis.json"), "w") as f:
        json.dump(gaps, f, indent=2)

    print(f"Scored {len(records)} projects -> {args.outdir}")
    print(f"  matrix.csv          ({len(matrix_rows)} rows, {len(cat_ids)} categories) = poster heatmap")
    print(f"  manual_checklist.csv ({len(checklist_rows)} items still need human verification)")
    print(f"  gap_analysis.json    {gaps['summary']}")


if __name__ == "__main__":
    main()
