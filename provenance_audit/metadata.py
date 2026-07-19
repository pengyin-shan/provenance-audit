"""Parsers that turn raw file text into structured citation + channel fields.

Kept dependency-light on purpose (PyYAML + stdlib). cffconvert and SoMEF are
optional richer alternatives noted in the README; the functions here are enough
to start scoring this week.
"""
from __future__ import annotations
import json
import re
import yaml


def _sstr(x):
    """Coerce a codemeta/CFF field to a string; join lists (some projects store
    givenName as a list of tokens). Returns '' for missing/None."""
    if x is None:
        return ""
    if isinstance(x, list):
        return " ".join(str(i) for i in x if i is not None)
    return str(x)


# ---------- CITATION.cff ----------

def parse_cff(text: str) -> dict:
    """Return a normalized subset of a CITATION.cff file."""
    try:
        data = yaml.safe_load(text) or {}
    except yaml.YAMLError as e:
        return {"error": f"cff_yaml_error: {e}"}
    if not isinstance(data, dict):
        return {"error": "cff_not_mapping"}

    def author_names(lst):
        names = []
        for a in lst or []:
            if not isinstance(a, dict):
                continue
            if a.get("name"):  # entity author
                names.append(_sstr(a["name"]))
            else:
                full = (_sstr(a.get("given-names")) + " " + _sstr(a.get("family-names"))).strip()
                if full:
                    names.append(full)
        return names

    out = {
        "title": data.get("title"),
        "version": data.get("version"),
        "doi": data.get("doi"),
        "authors": author_names(data.get("authors")),
        "preferred_citation": None,
    }
    pc = data.get("preferred-citation")
    if isinstance(pc, dict):
        out["preferred_citation"] = {
            "title": pc.get("title"),
            "doi": pc.get("doi"),
            "year": pc.get("year"),
            "authors": author_names(pc.get("authors")),
        }
    ids = data.get("identifiers") or []
    out["identifiers"] = [
        {"type": i.get("type"), "value": i.get("value")}
        for i in ids if isinstance(i, dict)
    ]
    return out


# ---------- codemeta.json ----------

def parse_codemeta(text: str) -> dict:
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        return {"error": f"codemeta_json_error: {e}"}
    if not isinstance(data, dict):
        return {"error": "codemeta_not_object"}

    def author_names(val):
        names = []
        if isinstance(val, dict):
            val = [val]
        for a in val or []:
            if not isinstance(a, dict):
                if a:
                    names.append(_sstr(a))
                continue
            if a.get("name"):
                names.append(_sstr(a.get("name")))
            else:
                full = (_sstr(a.get("givenName")) + " " + _sstr(a.get("familyName"))).strip()
                if full:
                    names.append(full)
        return names

    return {
        "name": data.get("name"),
        "version": data.get("version") or data.get("softwareVersion"),
        "identifier": data.get("identifier"),
        "license": data.get("license"),
        "codeRepository": data.get("codeRepository"),
        "authors": author_names(data.get("author")),
    }


# ---------- README citation section ----------

_CITE_HEADING = re.compile(
    r"^#{1,6}\s*.*\b(citation|cite|how to cite|citing)\b.*$",
    re.IGNORECASE | re.MULTILINE,
)


def extract_readme_citation(text: str) -> dict:
    """Heuristically locate a 'Citation/How to cite' section and return its text plus
    any DOI found inside it. Good enough for cross-channel comparison; flag for human check."""
    if not text:
        return {"found": False}
    m = _CITE_HEADING.search(text)
    if not m:
        doi = _find_doi(text)
        return {"found": False, "any_doi_in_readme": doi}
    start = m.start()
    rest = text[m.end():]
    nxt = re.search(r"^#{1,6}\s", rest, re.MULTILINE)
    section = text[start: m.end() + (nxt.start() if nxt else len(rest))]
    return {
        "found": True,
        "section_text": section.strip()[:4000],
        "doi": _find_doi(section),
    }


_DOI_RE = re.compile(r"\b10\.\d{4,9}/[-._;()/:A-Z0-9]+", re.IGNORECASE)


def _find_doi(text: str):
    if not text:
        return None
    m = _DOI_RE.search(text)
    return m.group(0).rstrip(".)") if m else None


# ---------- communication channels ----------

CHANNEL_PATTERNS = {
    "discord": re.compile(r"https?://(?:discord\.gg|discord\.com/invite)/\S+", re.I),
    "slack": re.compile(r"https?://[\w.-]*slack\.com(?:/\S*)?|https?://join\.slack\.com/\S+", re.I),
    "matrix": re.compile(r"https?://matrix\.to/#/\S+|#[\w.-]+:[\w.-]+", re.I),
    "zulip": re.compile(r"https?://[\w.-]+\.zulipchat\.com\S*", re.I),
    "gitter": re.compile(r"https?://gitter\.im/\S+", re.I),
    "discourse_forum": re.compile(r"https?://(?:discourse|forum|discuss)\.[\w.-]+\S*|https?://[\w.-]+\.discourse\.group\S*", re.I),
    "gh_discussions": re.compile(r"https?://github\.com/[\w.-]+/[\w.-]+/discussions\S*", re.I),
    "bluesky": re.compile(r"https?://bsky\.app/profile/\S+", re.I),
    "mastodon": re.compile(r"https?://[\w.-]+/@[\w]+|@[\w]+@[\w.-]+\.\w+", re.I),
    "twitter_x": re.compile(r"https?://(?:twitter\.com|x\.com)/\S+", re.I),
    "google_group": re.compile(r"https?://groups\.google\.com/\S+", re.I),
    "groups_io": re.compile(r"https?://[\w.-]+\.groups\.io/\S+", re.I),
    "mailing_list": re.compile(r"https?://lists?\.[\w.-]+/\S+|[\w.-]+-users@[\w.-]+|[\w.-]+-dev(?:el)?@[\w.-]+", re.I),
    "readthedocs": re.compile(r"https?://[\w.-]+\.readthedocs\.io\S*", re.I),
    "gh_pages": re.compile(r"https?://[\w.-]+\.github\.io\S*", re.I),
}


def extract_channels(*texts: str) -> dict:
    """Scan README/homepage text for declared communication channels.
    Returns {channel_type: [urls]} with de-duplication. Heuristic — verify by hand."""
    found: dict[str, list[str]] = {}
    blob = "\n".join(t for t in texts if t)
    for kind, pat in CHANNEL_PATTERNS.items():
        hits = []
        for m in pat.finditer(blob):
            val = m.group(0).rstrip(".,);>`_*\"'<")
            if val not in hits:
                hits.append(val)
        if hits:
            found[kind] = hits[:5]
    return found