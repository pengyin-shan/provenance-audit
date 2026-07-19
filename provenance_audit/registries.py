"""Package-registry collector. PyPI is implemented (reachable, no auth).
conda-forge / npm / CRAN are stubbed with the same return shape so you can
fill them in as the corpus demands. Each returns a dict or {"error": ...}.
"""
from __future__ import annotations
from .util import get_json


def collect_pypi(session, package: str) -> dict:
    data, err = get_json(session, f"https://pypi.org/pypi/{package}/json")
    if err:
        return {"registry": "pypi", "package": package, "error": err}
    info = data.get("info", {})
    return {
        "registry": "pypi",
        "package": package,
        "version": info.get("version"),
        "author": info.get("author"),
        "maintainer": info.get("maintainer"),
        "license": info.get("license"),
        "home_page": info.get("home_page"),
        "project_urls": info.get("project_urls") or {},
    }


def collect_conda(session, package: str) -> dict:
    # TODO: anaconda.org API (https://api.anaconda.org/package/conda-forge/<pkg>)
    return {"registry": "conda", "package": package, "error": "not_implemented"}


def collect_npm(session, package: str) -> dict:
    data, err = get_json(session, f"https://registry.npmjs.org/{package}")
    if err:
        return {"registry": "npm", "package": package, "error": err}
    latest = (data.get("dist-tags") or {}).get("latest")
    ver = (data.get("versions") or {}).get(latest, {})
    return {
        "registry": "npm",
        "package": package,
        "version": latest,
        "author": (ver.get("author") or {}).get("name") if isinstance(ver.get("author"), dict) else ver.get("author"),
        "license": ver.get("license"),
        "homepage": data.get("homepage"),
    }


def collect_cran(session, package: str) -> dict:
    # TODO: https://crandb.r-pkg.org/<pkg>
    return {"registry": "cran", "package": package, "error": "not_implemented"}


COLLECTORS = {
    "pypi": collect_pypi,
    "conda": collect_conda,
    "npm": collect_npm,
    "cran": collect_cran,
}


def collect_registry(session, registry: str, package: str) -> dict:
    fn = COLLECTORS.get(registry)
    if not fn:
        return {"registry": registry, "package": package, "error": "unknown_registry"}
    return fn(session, package)
