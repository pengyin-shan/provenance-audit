"""Archive collector (Zenodo).

NOTE: zenodo.org is not always reachable from restricted networks; this collector
is written to degrade gracefully. If a project declares a Zenodo concept DOI in its
CITATION.cff, prefer resolving that directly. Provide a record_id from the registry
YAML when you know it, or a concept DOI to look up.
"""
from __future__ import annotations
from .util import get_json


def collect_zenodo(session, record_id: str | None = None, doi: str | None = None) -> dict:
    if record_id:
        data, err = get_json(session, f"https://zenodo.org/api/records/{record_id}")
        if err:
            return {"archive": "zenodo", "record_id": record_id, "error": err}
        meta = data.get("metadata", {})
        return {
            "archive": "zenodo",
            "record_id": record_id,
            "title": meta.get("title"),
            "version": meta.get("version"),
            "doi": data.get("doi"),
            "conceptdoi": data.get("conceptdoi"),
            "creators": [c.get("name") for c in meta.get("creators", [])],
        }
    if doi:
        # Zenodo search by DOI
        data, err = get_json(session, "https://zenodo.org/api/records",
                             params={"q": f'doi:"{doi}"'})
        if err:
            return {"archive": "zenodo", "doi": doi, "error": err}
        hits = (data.get("hits") or {}).get("hits") or []
        if not hits:
            return {"archive": "zenodo", "doi": doi, "error": "no_match"}
        rec = hits[0]
        meta = rec.get("metadata", {})
        return {
            "archive": "zenodo",
            "doi": rec.get("doi"),
            "conceptdoi": rec.get("conceptdoi"),
            "title": meta.get("title"),
            "version": meta.get("version"),
            "creators": [c.get("name") for c in meta.get("creators", [])],
        }
    return {"archive": "zenodo", "error": "need record_id or doi"}
