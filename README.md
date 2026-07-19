# provenance-audit

[![Dataset DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.21443211.svg)](https://doi.org/10.5281/zenodo.21443211)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Release](https://img.shields.io/github/v/release/pengyin-shan/provenance-audit)](https://github.com/pengyin-shan/provenance-audit/releases)
[![SLSA 3](https://slsa.dev/images/gh-badge-level3.svg)](https://github.com/pengyin-shan/provenance-audit/blob/main/.github/workflows/release.yml)

Toolkit and dataset for **channel-based provenance** assessment of open-source
research software: the 18-signal framework, collectors, scoring, and figures
behind the SC26 poster *"The Unassessed Attack Surface: Channel-Based Provenance
in HPC and Quantum-Computing Open-Source Software"* (Pengyin Shan, NCSA,
University of Illinois Urbana-Champaign).

The framework asks four questions about the channels where software trust is
negotiated: who controls a project's voice (identity and access), which voice is
authoritative (communication channels), how the channel corrects itself
(knowledge infrastructure), and whether its assertions are machine-checkable
(distribution metadata). Nine signals are scored automatically for all 87
projects (44 HPC, 43 quantum computing); nine judgment-dependent signals were
hand-verified on a stratified 30-project panel.

```
provenance-audit/
  registry/
    corpus_100.yaml        popularity-thresholded sampling frame (frame.py output)
    corpus_keep.yaml       curated 87-project corpus (collect/score these)
    corpus_review.csv      curation judgment calls, with reasons
    corpus_drop.csv        what curation removed, and why
  provenance_audit/
    frame.py       build the sampling frame from GitHub orgs + ecosystem topics
    curate.py      triage the frame down to genuine research software
    collect.py     CLI entry point: repo metadata, releases, key files, registries
    github.py      GitHub collectors
    metadata.py    CITATION.cff / codemeta.json / README-citation / channel parsers
    registries.py  PyPI (implemented); conda/npm/CRAN stubs
    archives.py    Zenodo (best-effort)
    groundtruth.py canonical facts with source + verified flags
    framework.py   the 18-signal, 4-category rubric (edit this to adjust)
    score.py       score collected records against the framework
    subsample.py   seeded stratified subsample for manual verification
    figures.py     heatmaps + signal-prevalence table
    util.py        HTTP session, optional GitHub auth, response cache, graceful errors
  outputs/
    corpus_keep/                          collected per-project JSON (87 + _summary.json)
    corpus_keep_scored_FROZEN_20260706/   canonical scored set (matrix, checklists, scorecards)
    verify_worklist_30_CANONICAL.csv      hand-verified 30-project panel (dataset of record)
    figures/                              generated heatmaps + prevalence table
```

## Official channels

The official channels of this project are, exhaustively:

- **[GitHub Issues](https://github.com/pengyin-shan/provenance-audit/issues)**:
  bug reports, dataset corrections, and feature requests.
- **[GitHub Discussions](https://github.com/pengyin-shan/provenance-audit/discussions)**:
  questions about the framework, methodology, and use of the dataset.
- **Email <pengyins@illinois.edu>**: private contact with the maintainer,
  including security reports and impersonation reports (see
  [SECURITY.md](SECURITY.md)).

Any other account, package, or channel claiming to represent this project is
not official. If you encounter one, please report it as described in
[SECURITY.md](SECURITY.md#reporting-impersonation).

## Setup

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

**Set a GitHub token** (strongly recommended; it raises the API limit from 60 to
5,000 requests/hour; a full corpus run will rate-limit without it):

```bash
export GITHUB_TOKEN=...   # a classic token with public_repo scope is enough
```

The token is read from the environment only; it is never written to the cache
or outputs.

## Pipeline

```bash
# 1. Build the sampling frame (GitHub orgs + ecosystem topics, star threshold)
python -m provenance_audit.frame --out registry/corpus_100.yaml --min-stars 40 --per-domain 60

# 2. Curate the frame down to genuine research software
python -m provenance_audit.collect --registry registry/corpus_100.yaml --out outputs/corpus_100
python -m provenance_audit.curate --registry registry/corpus_100.yaml \
    --summary outputs/corpus_100/_summary.json --out-prefix registry/corpus

# 3. Collect the curated corpus
python -m provenance_audit.collect --registry registry/corpus_keep.yaml --out outputs/corpus_keep

# 4. Score against the 18-signal framework
python -m provenance_audit.score --in outputs/corpus_keep --out outputs/corpus_keep_scored

# 5. Draw a seeded stratified panel for manual verification
python -m provenance_audit.subsample --scored outputs/corpus_keep_scored --n 30 --seed 7 \
    --out outputs/verify_subsample_30.csv

# 6. Figures
python -m provenance_audit.figures --scored outputs/corpus_keep_scored --out outputs/figures --split-domain
```

Each collect run prints a line per project and writes `outputs/<corpus>/<project>.json`
plus `_summary.json`. Bad repo slugs show as `ERR(repo:not_found)`; fix them in the
registry YAML and re-run (`--only <name>` to redo just that one).

Scoring writes, into the output dir:
- `matrix.csv`: projects x 4 categories (auto-score 0-1); this is the poster heatmap.
- `manual_checklist.csv`: every `manual` signal still needing human verification.
- `gap_analysis.json`: which framework signals are unique vs. already covered by
  Scorecard / SLSA / Sigstore.
- `<project>.scorecard.json`: per-project signal-by-signal results.

## The manual verification step

Collection and `auto` scoring are automated; `manual` signals are not, and that is
the point of the framework. The subsampled panel is verified by hand against each
project's authoritative sources (repository, releases, documentation site,
README-linked pages; ~10-20 min/project). The verified result of that process for
the SC26 poster is `outputs/verify_worklist_30_CANONICAL.csv`, produced by manual
curation of the subsample output during verification.

## Adding projects

Append to the registry YAML. Minimum is `name` + `repo: owner/name`. Add
`registries:` (e.g. `- {registry: pypi, package: numpy}`) and
`zenodo: {record_id: ...}` when you know them.

## This repository scores itself

A framework for assessing channel-based provenance should withstand its own
assessment. The table below applies all 18 signals of
`provenance_audit/framework.py` to this repository. One signal,
`multi_maintainer`, is honestly "no": this is a solo-maintainer project, and we
document that status and its mitigations rather than presenting redundancy the
project does not have. Signals tied to the release process take effect when the
v1.0.0 tag is pushed; they are marked accordingly.

| Signal | Status | Satisfied by | How to do this in your project |
|---|---|---|---|
| **C1: Identity and access** | | | |
| `multi_maintainer` | No, with documented mitigation | [GOVERNANCE.md](GOVERNANCE.md) | If you are a solo maintainer, say so in a governance file and list your mitigations: branch protection, MFA, an organizational backup contact, and a succession plan. A documented single point of failure is assessable; an undocumented one is not. |
| `contributing_doc` | Yes | [CONTRIBUTING.md](CONTRIBUTING.md) | Add a CONTRIBUTING.md stating how to submit changes and what response time to expect. State the review expectations you can actually keep. |
| `governance_doc` | Yes | [GOVERNANCE.md](GOVERNANCE.md) | Write down who decides what, in a file named GOVERNANCE.md at the repository root so tools and agents can find it. |
| `mfa_on_channel_admins` | Yes, stated | [SECURITY.md](SECURITY.md#account-security) | Enable MFA on every account that controls the repository or a distribution channel, then state that fact in SECURITY.md. External assessors cannot observe MFA; the statement is the observable signal. |
| `channel_admin_transfer` | Yes | [GOVERNANCE.md](GOVERNANCE.md#solo-maintainer) | Document what happens if a maintainer leaves or becomes unreachable. For personal accounts, designate a GitHub account successor and name an organizational backup contact. |
| **C2: Communication channels** | | | |
| `channels_declared` | Yes | [README](#official-channels) | List every official channel in the README. |
| `channels_documented` | Yes | [README](#official-channels) | State each channel's purpose, so users know where a given kind of message belongs. |
| `official_channel_statement` | Yes | [README](#official-channels) | Add one sentence: any account, package, or channel not on this list is not official. This is the sentence an AI agent can check a claimed channel against. |
| `impersonation_reporting` | Yes | [SECURITY.md](SECURITY.md#reporting-impersonation) | Tell people how to report fake accounts, spoofed packages, and lookalike channels, and where to escalate on the hosting platform. |
| **C3: Knowledge infrastructure** | | | |
| `security_policy` | Yes | [SECURITY.md](SECURITY.md) | Add a SECURITY.md at the repository root. GitHub surfaces it automatically. |
| `changelog` | Yes | [CHANGELOG.md](CHANGELOG.md) | Keep a changelog in Keep a Changelog format. If the project predates version control, reconstruct honestly and say so. |
| `release_notes` | Yes (at v1.0.0 tag) | [.github/RELEASE_NOTES_v1.0.0.md](.github/RELEASE_NOTES_v1.0.0.md) | Write release notes per release describing what is in the artifacts and how to verify them. |
| `disclosure_depth` | Yes | [SECURITY.md](SECURITY.md#reporting-a-vulnerability) | Beyond a contact address, state the process: acknowledgment window, triage, disclosure timeline, and scope. |
| **C4: Distribution metadata** | | | |
| `has_release` | Yes (at v1.0.0 tag) | [Releases](https://github.com/pengyin-shan/provenance-audit/releases) | Publish tagged, versioned releases rather than pointing users at the default branch. |
| `archival_doi` | Yes, dataset DOI [10.5281/zenodo.21443211](https://doi.org/10.5281/zenodo.21443211) | [CITATION.cff](CITATION.cff) | Deposit the dataset (or link the repository) on Zenodo and record the DOI in CITATION.cff so the archived copy is discoverable from the repository. |
| `signed_releases` | Yes (at v1.0.0 tag) | [release.yml](.github/workflows/release.yml) | Publish checksums and a provenance attestation with every release. Signing that assessors can verify beats signing that they cannot. |
| `sbom` | Yes (at v1.0.0 tag) | [release.yml](.github/workflows/release.yml) | Generate an SPDX or CycloneDX SBOM in CI and attach it to the release. One workflow step (for example anchore/sbom-action) is sufficient. |
| `provenance_attestation` | Yes (at v1.0.0 tag) | [release.yml](.github/workflows/release.yml) | Generate SLSA build provenance in CI (slsa-github-generator or GitHub artifact attestations) so consumers can verify artifacts came from your repository's CI, not from a hijacked account. |

## Citing

See [CITATION.cff](CITATION.cff). The dataset is archived on Zenodo,
DOI [10.5281/zenodo.21443211](https://doi.org/10.5281/zenodo.21443211);
the corpus is a point-in-time snapshot collected in July 2026.

## Acknowledgments

Portions of the code and documentation were drafted with assistance from Claude (Anthropic); this assistance is recorded via `Co-Authored-By` trailers in the commit history. All content, code, and data were reviewed and verified by the maintainer, who is the sole author of this work.

## License, security, governance

Apache-2.0 ([LICENSE](LICENSE)). Vulnerability disclosure and impersonation
reporting: [SECURITY.md](SECURITY.md). Maintainership, including an honest
account of the project's solo-maintainer status and its mitigations:
[GOVERNANCE.md](GOVERNANCE.md). Contributions: [CONTRIBUTING.md](CONTRIBUTING.md).

## Optional richer parsing

- **cffconvert** (`pip install cffconvert`) validates CITATION.cff and converts to
  BibTeX/APA; swap it into `metadata.parse_cff` for validation, not just parsing.
- **SoMEF** extracts metadata from READMEs with ML; heavier (Java + models). The
  built-in `extract_readme_citation` is the lightweight stand-in.
