"""GitHub collector.

Pulls the repository-level facts needed for BOTH corpora:
- Corpus B (channel-provenance): default branch, latest release/version, pushed_at,
  archived flag, topics, license, presence of SECURITY.md.
- Corpus A (citation): raw text of CITATION.cff and codemeta.json for parsing.

Only the public GitHub REST API + raw.githubusercontent.com are used (both reachable
without scraping). Set GITHUB_TOKEN to lift the unauthenticated 60 req/hr limit to 5000.
"""
from __future__ import annotations
from .util import get_json, get_text

API = "https://api.github.com"
RAW = "https://raw.githubusercontent.com"

# Files we look for, in the repo root.
TARGET_FILES = [
    "CITATION.cff", "codemeta.json", "SECURITY.md", "README.md", "README.rst",
    "CONTRIBUTING.md", "GOVERNANCE.md", "CHANGELOG.md",
]


def collect_github(session, owner: str, repo: str) -> dict:
    out: dict = {"owner": owner, "repo": repo, "errors": {}}

    meta, err = get_json(session, f"{API}/repos/{owner}/{repo}")
    if err:
        out["errors"]["repo"] = err
        return out  # nothing else will work without the repo
    out["full_name"] = meta.get("full_name")
    out["description"] = meta.get("description")
    out["homepage"] = meta.get("homepage")
    out["default_branch"] = meta.get("default_branch", "main")
    out["archived"] = meta.get("archived", False)
    out["pushed_at"] = meta.get("pushed_at")
    out["stars"] = meta.get("stargazers_count")
    out["topics"] = meta.get("topics", [])
    lic = meta.get("license") or {}
    out["license"] = lic.get("spdx_id")

    rel, err = get_json(session, f"{API}/repos/{owner}/{repo}/releases/latest")
    if err == "not_found":
        out["latest_release"] = None  # /releases/latest returns 404 when only prereleases (or none) exist
    elif err:
        out["errors"]["latest_release"] = err
    else:
        out["latest_release"] = {
            "tag": rel.get("tag_name"),
            "name": rel.get("name"),
            "published_at": rel.get("published_at"),
        }

    # Distinguish "publishes stable releases" from "prereleases only" from "no releases".
    # /releases/latest excludes prereleases, so a 404 there is ambiguous; check the list.
    rels, rerr = get_json(session, f"{API}/repos/{owner}/{repo}/releases", params={"per_page": 10})
    if rerr:
        out["release_state"] = "unknown" if "repo" not in out["errors"] else "unknown"
        if "latest_release" not in out["errors"]:
            out["errors"].setdefault("releases_list", rerr)
    else:
        any_rel = len(rels) > 0
        any_stable = any(not r.get("prerelease", False) and not r.get("draft", False) for r in rels)
        out["release_state"] = ("release" if any_stable
                                else "prerelease_only" if any_rel
                                else "none")

    branch = out["default_branch"]
    out["files"] = {}
    for fname in TARGET_FILES:
        text, err = get_text(session, f"{RAW}/{owner}/{repo}/{branch}/{fname}")
        if err is None:
            out["files"][fname] = text
        # missing files are simply absent from out["files"]; not an error to record

    # GitHub also recognizes SECURITY.md / CONTRIBUTING.md under .github/ and docs/
    for fname in ("SECURITY.md", "CONTRIBUTING.md"):
        if fname not in out["files"]:
            for prefix in (".github/", "docs/"):
                text, err = get_text(session, f"{RAW}/{owner}/{repo}/{branch}/{prefix}{fname}")
                if err is None:
                    out["files"][fname] = text
                    break

    out["has_security_md"] = "SECURITY.md" in out["files"]
    out["has_citation_cff"] = "CITATION.cff" in out["files"]
    out["has_codemeta"] = "codemeta.json" in out["files"]
    return out
