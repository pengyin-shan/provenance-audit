"""Collection CLI.

Usage:
    python -m provenance_audit.collect --registry registry/corpus_keep.yaml --out outputs/corpus_keep
    python -m provenance_audit.collect --registry registry/corpus_keep.yaml --out outputs/corpus_keep --only kokkos

Reads a registry YAML (list of projects), runs the GitHub + metadata + registry
+ archive collectors for each, derives a draft ground-truth record, and writes
one JSON per project plus a run summary. Re-running is safe; it overwrites.
"""
from __future__ import annotations
import argparse
import json
import os
import sys
import time
import yaml

from .util import make_session
from .github import collect_github
from .metadata import parse_cff, parse_codemeta, extract_readme_citation, extract_channels
from .registries import collect_registry
from .archives import collect_zenodo
from .groundtruth import derive_ground_truth


def collect_project(session, proj: dict) -> dict:
    """proj keys: name, repo ('owner/name'), registries [{registry,package}],
    zenodo {record_id|doi}, discipline, ecosystem."""
    rec: dict = {
        "name": proj.get("name"),
        "domain": proj.get("domain"),
        "discipline": proj.get("discipline"),
        "ecosystem": proj.get("ecosystem"),
        "collected_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "errors": {},
    }

    repo = proj.get("repo", "")
    if "/" in repo:
        owner, name = repo.split("/", 1)
        gh = collect_github(session, owner, name)
        gh["owner"] = owner
        rec["github"] = gh
        files = gh.get("files", {})

        if "CITATION.cff" in files:
            rec["citation_cff"] = parse_cff(files["CITATION.cff"])
        if "codemeta.json" in files:
            rec["codemeta"] = parse_codemeta(files["codemeta.json"])
        readme = files.get("README.md") or files.get("README.rst") or ""
        rec["readme_citation"] = extract_readme_citation(readme)
        rec["channels"] = extract_channels(readme, gh.get("homepage") or "")
    else:
        rec["errors"]["repo"] = "missing or malformed 'repo' (expected owner/name)"

    rec["registries"] = []
    for r in proj.get("registries", []) or []:
        rec["registries"].append(collect_registry(session, r.get("registry"), r.get("package")))

    z = proj.get("zenodo")
    if z:
        rec["zenodo"] = collect_zenodo(session, record_id=z.get("record_id"), doi=z.get("doi"))

    rec["ground_truth"] = derive_ground_truth(rec)
    return rec


def main(argv=None):
    ap = argparse.ArgumentParser(description="Collect channel/citation provenance data per project.")
    ap.add_argument("--registry", required=True, help="path to a registry YAML")
    ap.add_argument("--out", required=True, help="output directory for per-project JSON")
    ap.add_argument("--only", help="collect a single project by name (substring match)")
    args = ap.parse_args(argv)

    with open(args.registry) as f:
        projects = yaml.safe_load(f) or []
    if args.only:
        projects = [p for p in projects if args.only.lower() in (p.get("name", "").lower())]

    os.makedirs(args.out, exist_ok=True)
    session = make_session()
    if "GITHUB_TOKEN" not in os.environ:
        print("[warn] GITHUB_TOKEN not set: GitHub API limited to ~60 requests/hour.", file=sys.stderr)

    summary = []
    for i, proj in enumerate(projects, 1):
        name = proj.get("name", f"project_{i}")
        rec = collect_project(session, proj)
        safe = name.replace("/", "_").replace(" ", "_")
        path = os.path.join(args.out, f"{safe}.json")
        with open(path, "w") as f:
            json.dump(rec, f, indent=2, ensure_ascii=False)

        gh = rec.get("github", {})
        flags = []
        if gh.get("has_citation_cff"):
            flags.append("cff")
        if gh.get("has_codemeta"):
            flags.append("codemeta")
        if gh.get("has_security_md"):
            flags.append("security")
        n_chan = len(rec.get("channels", {}) or {})
        errs = "; ".join(f"{k}:{v}" for k, v in gh.get("errors", {}).items()) or rec["errors"].get("repo", "")
        line = f"[{i:>2}/{len(projects)}] {name:<22} files=[{','.join(flags) or '-'}] channels={n_chan}"
        if errs:
            line += f"  ERR({errs})"
        print(line)
        summary.append({"name": name, "files": flags, "channels": n_chan, "error": errs or None})

    with open(os.path.join(args.out, "_summary.json"), "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nWrote {len(projects)} records + _summary.json to {args.out}")


if __name__ == "__main__":
    main()
