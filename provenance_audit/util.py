"""Shared HTTP helpers: a requests session with optional GitHub auth,
polite retries, small fetch helpers, and an on-disk response cache so that
re-running over a large corpus does not re-fetch every URL (important at N=100,
both for speed and for staying under the GitHub rate limit).

Set PROVENANCE_CACHE=/path to enable caching (or call enable_cache). A cached
GET is keyed by URL; delete the cache dir to force a fresh pull.
"""
from __future__ import annotations
import hashlib
import json
import os
import time
import requests

USER_AGENT = "provenance-audit/0.2 (research software channel/citation audit)"
_CACHE_DIR = os.environ.get("PROVENANCE_CACHE")


def enable_cache(path: str):
    global _CACHE_DIR
    _CACHE_DIR = path
    os.makedirs(path, exist_ok=True)


def _cache_path(url: str):
    if not _CACHE_DIR:
        return None
    os.makedirs(_CACHE_DIR, exist_ok=True)
    key = hashlib.sha256(url.encode()).hexdigest()[:24]
    return os.path.join(_CACHE_DIR, key + ".json")


def _cache_get(url: str):
    p = _cache_path(url)
    if p and os.path.exists(p):
        try:
            with open(p) as f:
                return json.load(f)
        except (ValueError, OSError):
            return None
    return None


def _cache_put(url: str, kind: str, payload):
    p = _cache_path(url)
    if p:
        try:
            with open(p, "w") as f:
                json.dump({"kind": kind, "payload": payload}, f)
        except OSError:
            pass


def make_session() -> requests.Session:
    s = requests.Session()
    s.headers.update({"User-Agent": USER_AGENT, "Accept": "application/vnd.github+json"})
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        s.headers["Authorization"] = f"Bearer {token}"
    return s


def get_json(session: requests.Session, url: str, params: dict | None = None, tries: int = 3):
    """GET JSON. Returns (data, None) on success or (None, error_str) on failure.
    Honors GitHub rate-limit reset on 403 once. Uses the on-disk cache if enabled
    (only successful responses and hard 404s are cached)."""
    if params is None:
        cached = _cache_get(url)
        if cached is not None:
            if cached["kind"] == "json":
                return cached["payload"], None
            if cached["kind"] == "not_found":
                return None, "not_found"
    for attempt in range(tries):
        try:
            r = session.get(url, params=params, timeout=30)
        except requests.RequestException as e:
            if attempt == tries - 1:
                return None, f"request_error: {e}"
            time.sleep(1.5 * (attempt + 1))
            continue
        if r.status_code == 404:
            _cache_put(url, "not_found", None)
            return None, "not_found"
        if r.status_code == 403 and "rate limit" in r.text.lower():
            reset = r.headers.get("X-RateLimit-Reset")
            return None, f"rate_limited (reset epoch {reset}); set GITHUB_TOKEN to raise the limit"
        if r.status_code >= 400:
            return None, f"http_{r.status_code}"
        try:
            data = r.json()
        except ValueError:
            return None, "invalid_json"
        if params is None:
            _cache_put(url, "json", data)
        return data, None
    return None, "exhausted_retries"


def get_text(session: requests.Session, url: str, tries: int = 3):
    """GET raw text (for README, CITATION.cff, codemeta.json via raw.githubusercontent)."""
    cached = _cache_get(url)
    if cached is not None:
        if cached["kind"] == "text":
            return cached["payload"], None
        if cached["kind"] == "not_found":
            return None, "not_found"
    for attempt in range(tries):
        try:
            r = session.get(url, timeout=30, headers={"Accept": "*/*"})
        except requests.RequestException as e:
            if attempt == tries - 1:
                return None, f"request_error: {e}"
            time.sleep(1.5 * (attempt + 1))
            continue
        if r.status_code == 404:
            _cache_put(url, "not_found", None)
            return None, "not_found"
        if r.status_code >= 400:
            return None, f"http_{r.status_code}"
        _cache_put(url, "text", r.text)
        return r.text, None
    return None, "exhausted_retries"
