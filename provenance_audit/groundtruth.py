"""Derive a canonical ground-truth record from a collected project record.

This is the set of verified facts the channel-provenance assessment relies on.
Every field carries its
source and a `verified` flag defaulting to False: the collector proposes, the
human confirms. Filling in/confirming these fields is the hand-verification
step that turns automated collection into trustworthy ground truth.
"""
from __future__ import annotations


def _first(*vals):
    for v in vals:
        if v:
            return v
    return None


def derive_ground_truth(record: dict) -> dict:
    gh = record.get("github", {})
    cff = record.get("citation_cff") or {}
    cm = record.get("codemeta") or {}
    pypi = next((r for r in record.get("registries", []) if r.get("registry") == "pypi" and not r.get("error")), {})
    rel = gh.get("latest_release") or {}

    def field(value, source):
        return {"value": value, "source": source, "verified": False}

    gt = {
        "project": record.get("name"),
        "repo": gh.get("full_name"),
        "current_version": field(
            _first(rel.get("tag"), cff.get("version"), cm.get("version"), pypi.get("version")),
            "github_release|cff|codemeta|pypi",
        ),
        "maintainers": field(
            _first(cff.get("authors"), cm.get("authors"),
                   [gh.get("owner")] if gh.get("owner") else None),
            "cff_authors|codemeta_authors|github_owner",
        ),
        "official_channels": field(record.get("channels") or {}, "readme/homepage_scan"),
        "security_reporting": field(
            "SECURITY.md present" if gh.get("has_security_md") else None, "github_security_md"
        ),
        "citation_doi": field(
            _first(cff.get("doi"),
                   (cff.get("preferred_citation") or {}).get("doi"),
                   (record.get("zenodo") or {}).get("conceptdoi")),
            "cff_doi|preferred_citation_doi|zenodo_conceptdoi",
        ),
        "homepage": field(_first(gh.get("homepage"), cm.get("codeRepository")), "github_homepage"),
    }
    gt["_needs_human_verification"] = [
        k for k, v in gt.items()
        if isinstance(v, dict) and v.get("verified") is False
    ]
    return gt
