# Security Policy

## Reporting a vulnerability

If you find a security problem in this toolkit, in its release artifacts, or
in the published dataset, report it privately through either channel:

- Email: <pengyins@illinois.edu> (subject line starting with `[SECURITY]`)
- GitHub private vulnerability reporting:
  <https://github.com/pengyin-shan/provenance-audit/security/advisories/new>

You will receive an acknowledgment within **5 business days**. After triage,
you will get an assessment of the report and, if the issue is confirmed, an
expected timeline for a fix. Please do not disclose the issue publicly before
a fix is released or 90 days have passed, whichever comes first. Credit is
given in the release notes unless you ask otherwise.

### Scope

- The `provenance_audit` Python package and its CLI entry points.
- Release artifacts published from this repository (sdist, wheel, SBOM,
  checksums, provenance attestation).
- Integrity of the published dataset files under `outputs/`.

Vulnerabilities in the third-party projects that this toolkit *measures* are
out of scope here; report those to the affected project.

## Reporting impersonation

The official channels of this project are listed in the
[README](README.md#official-channels). Any other account, package, or channel
claiming to represent this project is not official.

If you encounter a fake maintainer account, a spoofed or typosquatted package
(for example on PyPI), or a lookalike repository or communication channel:

1. Email <pengyins@illinois.edu> with subject `[IMPERSONATION]`, including the
   URL of the fake account, package, or channel.
2. If the impersonation is on a platform with its own reporting path, please
   also report it there (GitHub: report abuse; PyPI: <security@pypi.org>).

Reports are acknowledged within the same 5-business-day window.

## Account security

The maintainer account for this repository and its distribution channels
requires multi-factor authentication.
