"""Build a domain-tagged registry (HPC + QC) from sampling frames, not a hand-picked list.

The point is defensibility: a reviewer asks "why these 100?" and the answer is a
reproducible frame — GitHub organizations and topics that define the HPC and QC
open-source ecosystems — rather than convenience. This module expands a set of seed
GitHub organizations (and optionally topic searches) into candidate repos, filters by
a minimum popularity/activity threshold, tags each hpc|qc, and writes a registry YAML
that collect.py consumes unchanged.

Usage:
    export GITHUB_TOKEN=...        # required at this scale
    python -m provenance_audit.frame --out registry/corpus_100.yaml --min-stars 40 --per-domain 60

Edit SEED_ORGS / SEED_TOPICS below to adjust the frame. Re-running is deterministic
given the same GitHub state; record the date + thresholds in your methods section.
"""
from __future__ import annotations
import argparse
import time

import yaml

from .util import make_session, get_json

API = "https://api.github.com"

# Sampling frame: organizations that anchor each ecosystem. Extend as needed and
# document the final list — this IS the corpus definition.
SEED_ORGS = {
    "hpc": [
        "spack", "E4S-Project", "kokkos", "trilinos", "LLNL", "hypre-space",
        "mfem", "dealii", "HDFGroup", "ornladios", "darshan-hpc", "flux-framework",
        "Parallel-NetCDF", "hpctoolkit", "GEOSX", "AMReX-Codes", "ECP-VeloC",
        "ECP-WarpX", "sandialabs", "ornl",
    ],
    "qc": [
        "Qiskit", "quantumlib", "PennyLaneAI", "qutip", "rigetti", "QuTech-Delft",
        "quantumsymposium", "unitaryfund", "qiboteam", "CQCL", "amazon-braket",
        "ProjectQ-Framework", "XanaduAI", "google-quantum-ai",
    ],
}

# Optional topic-based expansion (GitHub topic search). Keeps the frame from being
# org-only. Each topic pulls the most-starred repos carrying it.
SEED_TOPICS = {
    "hpc": ["high-performance-computing", "mpi", "exascale"],
    "qc": ["quantum-computing", "quantum-programming-language"],
}


def _org_repos(session, org):
    out, page = [], 1
    while page <= 4:  # cap pages per org
        data, err = get_json(session, f"{API}/orgs/{org}/repos",
                             params={"per_page": 100, "page": page, "type": "public", "sort": "updated"})
        if err or not data:
            break
        out.extend(data)
        if len(data) < 100:
            break
        page += 1
        time.sleep(0.2)
    return out


def _topic_repos(session, topic, cap=50):
    data, err = get_json(session, f"{API}/search/repositories",
                         params={"q": f"topic:{topic}", "sort": "stars", "order": "desc", "per_page": cap})
    if err:
        return []
    return (data or {}).get("items", [])


def build(min_stars: int, per_domain: int, use_topics: bool = True):
    session = make_session()
    seen = set()
    by_domain = {"hpc": [], "qc": []}

    for domain, orgs in SEED_ORGS.items():
        for org in orgs:
            for r in _org_repos(session, org):
                _consider(r, domain, min_stars, seen, by_domain)
        if use_topics:
            for topic in SEED_TOPICS.get(domain, []):
                for r in _topic_repos(session, topic):
                    _consider(r, domain, min_stars, seen, by_domain)

    # rank each domain by stars, take the top per_domain
    projects = []
    for domain, items in by_domain.items():
        items.sort(key=lambda x: x["_stars"], reverse=True)
        projects.extend(items[:per_domain])
    return projects


def _consider(r, domain, min_stars, seen, by_domain):
    if not isinstance(r, dict) or r.get("archived") or r.get("fork"):
        return
    full = r.get("full_name")
    if not full or full in seen:
        return
    stars = r.get("stargazers_count", 0)
    if stars < min_stars:
        return
    seen.add(full)
    by_domain[domain].append({
        "name": r.get("name"),
        "repo": full,
        "domain": domain,
        "discipline": domain,
        "ecosystem": "frame",
        "_stars": stars,
    })


def main(argv=None):
    ap = argparse.ArgumentParser(description="Build a domain-tagged HPC+QC registry from sampling frames.")
    ap.add_argument("--out", required=True)
    ap.add_argument("--min-stars", type=int, default=40, help="popularity threshold for inclusion")
    ap.add_argument("--per-domain", type=int, default=60, help="max projects kept per domain after ranking")
    ap.add_argument("--no-topics", action="store_true", help="use seed orgs only, skip topic search")
    args = ap.parse_args(argv)

    projects = build(args.min_stars, args.per_domain, use_topics=not args.no_topics)
    # strip the private _stars sort key before writing
    for p in projects:
        p.pop("_stars", None)
    with open(args.out, "w") as f:
        yaml.safe_dump(projects, f, sort_keys=False)
    n_hpc = sum(1 for p in projects if p["domain"] == "hpc")
    n_qc = sum(1 for p in projects if p["domain"] == "qc")
    print(f"Wrote {len(projects)} projects to {args.out}  (hpc={n_hpc}, qc={n_qc}; min_stars={args.min_stars})")
    print("Review the YAML by hand before collecting: drop mirrors/duplicates/non-software repos.")


if __name__ == "__main__":
    main()
