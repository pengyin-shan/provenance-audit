"""Generate poster figures from scored output.

Usage:
    python -m provenance_audit.figures --scored outputs/corpus_b_scored --out outputs/figures

Produces:
    heatmap.png / heatmap.pdf   projects x 4 categories (the poster centerpiece)
    signal_prevalence.csv        per-signal present/absent/unknown counts across the corpus
"""
from __future__ import annotations
import argparse
import csv
import glob
import json
import os
from collections import Counter

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def load_matrix(scored_dir):
    path = os.path.join(scored_dir, "matrix.csv")
    with open(path, newline="") as f:
        rows = list(csv.DictReader(f))
    projects = [r["project"] for r in rows]
    cats = [c for c in rows[0].keys() if c != "project"]
    data = np.array([[float(r[c]) if r[c] not in ("", "None") else np.nan for c in cats] for r in rows])
    return projects, cats, data


def heatmap(projects, cats, data, outdir):
    order = np.argsort(np.nanmean(data, axis=1))[::-1]  # best-scoring on top
    data, projects = data[order], [projects[i] for i in order]
    fig, ax = plt.subplots(figsize=(7.5, 0.42 * len(projects) + 1.6))
    im = ax.imshow(data, cmap="RdYlGn", vmin=0, vmax=1, aspect="auto")
    ax.set_xticks(range(len(cats)))
    labels = [l.replace(" ", "\n", 1) for l in cats]
    ax.set_xticklabels(labels, rotation=0, ha="center", fontsize=8)
    ax.set_yticks(range(len(projects)))
    ax.set_yticklabels(projects, fontsize=9)
    for i in range(len(projects)):
        for j in range(len(cats)):
            v = data[i, j]
            if not np.isnan(v):
                ax.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=8,
                        color="black" if 0.25 < v < 0.85 else "white")
    ax.set_title("Channel-provenance posture (auto-detectable signals), HPC & QC pilot corpus", fontsize=11)
    fig.colorbar(im, ax=ax, shrink=0.7, label="fraction of signals present")
    fig.tight_layout()
    for ext in ("png", "pdf"):
        fig.savefig(os.path.join(outdir, f"heatmap.{ext}"), dpi=200)
    plt.close(fig)


def signal_prevalence(scored_dir, outdir):
    counts: dict[str, Counter] = {}
    meta = {}
    for path in glob.glob(os.path.join(scored_dir, "*.scorecard.json")):
        d = json.load(open(path))
        for cid, cat in d["categories"].items():
            for sid, s in cat["signals"].items():
                counts.setdefault(sid, Counter())[s["status"]] += 1
                meta[sid] = (cid, s["detect"])
    rows = []
    for sid, c in sorted(counts.items()):
        cid, detect = meta[sid]
        rows.append({"signal": sid, "category": cid, "detect": detect,
                     "present": c.get("present", 0), "absent": c.get("absent", 0),
                     "unknown": c.get("unknown_collection_error", 0),
                     "manual_unverified": c.get("manual_unverified", 0)})
    out = os.path.join(outdir, "signal_prevalence.csv")
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys()); w.writeheader(); w.writerows(rows)
    return rows


def _domain_lookup(scored_dir):
    dom = {}
    for path in glob.glob(os.path.join(scored_dir, "*.scorecard.json")):
        d = json.load(open(path))
        dom[d["name"]] = d.get("domain") or "unknown"
    return dom


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--scored", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--split-domain", action="store_true",
                    help="also emit one heatmap per domain (hpc/qc) for the subgroup comparison")
    args = ap.parse_args(argv)
    os.makedirs(args.out, exist_ok=True)
    projects, cats, data = load_matrix(args.scored)
    heatmap(projects, cats, data, args.out)
    rows = signal_prevalence(args.scored, args.out)
    print(f"Wrote heatmap.png/.pdf and signal_prevalence.csv ({len(rows)} signals) to {args.out}")

    if args.split_domain:
        dom = _domain_lookup(args.scored)
        domains = sorted(set(dom.values()))
        for dname in domains:
            keep = [i for i, p in enumerate(projects) if dom.get(p) == dname]
            if len(keep) < 2:
                continue
            sub_p = [projects[i] for i in keep]
            sub_d = data[keep]
            # temporary heatmap writer with a domain-suffixed filename
            order = np.argsort(np.nanmean(sub_d, axis=1))[::-1]
            sub_d, sub_p = sub_d[order], [sub_p[i] for i in order]
            fig, ax = plt.subplots(figsize=(7.5, 0.42 * len(sub_p) + 1.6))
            im = ax.imshow(sub_d, cmap="RdYlGn", vmin=0, vmax=1, aspect="auto")
            ax.set_xticks(range(len(cats)))
            labels = [l.replace(" ", "\n", 1) for l in cats]
            ax.set_xticklabels(labels, rotation=0, ha="center", fontsize=8)
            ax.set_yticks(range(len(sub_p))); ax.set_yticklabels(sub_p, fontsize=9)
            for i in range(len(sub_p)):
                for j in range(len(cats)):
                    v = sub_d[i, j]
                    if not np.isnan(v):
                        ax.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=8,
                                color="black" if 0.25 < v < 0.85 else "white")
            ax.set_title(f"Channel-provenance posture — {dname.upper()} (n={len(sub_p)})", fontsize=11)
            fig.colorbar(im, ax=ax, shrink=0.7, label="fraction of signals present")
            fig.tight_layout()
            fig.savefig(os.path.join(args.out, f"heatmap_{dname}.pdf"), dpi=200)
            fig.savefig(os.path.join(args.out, f"heatmap_{dname}.png"), dpi=200)
            plt.close(fig)
        print(f"Wrote per-domain heatmaps for: {', '.join(domains)}")


if __name__ == "__main__":
    main()
