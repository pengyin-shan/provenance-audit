# Governance

## Project

provenance-audit is a research software project of Pengyin Shan (National Center
for Supercomputing Applications, University of Illinois Urbana-Champaign;
ORCID [0009-0009-6309-380X](https://orcid.org/0009-0009-6309-380X)), developed
under the author's 2025-2026 Trusted CI Fellowship.

## Solo maintainer

This project has a single maintainer: Pengyin Shan. We state this plainly
rather than presenting an inflated picture of the project's redundancy. The
channel-provenance framework this repository implements scores observability:
a documented solo-maintainer status with mitigations is more trustworthy than
an undocumented one, and this document is that record.

Mitigations in place:

- **Branch protection.** The `main` branch is protected; changes land through
  pull requests, and history is never force-pushed.
- **Multi-factor authentication.** The maintainer's GitHub account, which
  controls this repository and its distribution channels, requires MFA. See
  [SECURITY.md](SECURITY.md).
- **Organizational backup contact.** If the maintainer is unreachable,
  contact the Software Directory, NCSA, University of Illinois
  Urbana-Champaign, via <https://www.ncsa.illinois.edu/about/contact>. NCSA
  can confirm the maintainer's status and affiliation.
- **Succession.** If the maintainer becomes permanently unreachable, control
  of the repository follows GitHub's account-succession mechanism (a
  [pre-designated successor](https://docs.github.com/en/account-and-profile/setting-up-and-managing-your-personal-account-on-github/managing-access-to-your-personal-repositories/maintaining-ownership-continuity-of-your-personal-accounts-repositories)
  for the maintainer's personal account). The archived releases and the
  Zenodo deposit remain citable and verifiable independently of the GitHub
  account.

## Decision making

The maintainer decides on releases, scope, and merges. Substantive changes to
the 18-signal framework (`provenance_audit/framework.py`) are documented in
[CHANGELOG.md](CHANGELOG.md) so that scores from different versions are not
silently mixed.

## Changes to this document

Changes to governance are made by pull request and take effect when merged to
`main`.
