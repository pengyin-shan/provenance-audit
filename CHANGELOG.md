# Changelog

All notable changes to this project are documented in this file. The format
follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the
project uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

The project predates its version control history; entries before the first
release are reconstructed from file timestamps and the maintainer's records.

## [1.0.0] - 2026-07-19

First public release, accompanying the SC26 poster "The Unassessed Attack
Surface: Channel-Based Provenance in HPC and Quantum-Computing Open-Source
Software" and the Zenodo dataset deposit.

### Added

- 18-signal, 4-category channel-provenance framework
  (`provenance_audit/framework.py`).
- Collection pipeline: sampling-frame builder (`frame.py`), curation triage
  (`curate.py`), collectors for GitHub, packaging registries, and Zenodo
  (`collect.py`, `github.py`, `registries.py`, `archives.py`, `metadata.py`),
  with a local response cache (early July 2026).
- Scoring head (`score.py`): per-project scorecards, category matrix, manual
  verification checklist, and tool-coverage gap analysis.
- Seeded stratified subsampling for the manual verification panel
  (`subsample.py`; the canonical 30-project panel uses seed 7).
- Figures: overall and per-domain heatmaps and signal-prevalence table
  (`figures.py`).
- Dataset of record: 87-project corpus (44 HPC, 43 quantum computing) collected
  and scored July 2026 (`outputs/corpus_keep/`,
  `outputs/corpus_keep_scored_FROZEN_20260706/`), and the hand-verified
  30-project panel (`outputs/verify_worklist_30_CANONICAL.csv`, finalized
  July 19, 2026, by manual curation of the subsample output).
- Community and provenance documentation: README with official channels,
  CONTRIBUTING.md, GOVERNANCE.md, SECURITY.md (disclosure and impersonation
  reporting), CITATION.cff, Apache-2.0 LICENSE, pinned dependencies, and a
  release workflow producing checksums, an SPDX SBOM, and SLSA provenance.

### Removed

- Superseded pre-curation corpus outputs, starter registries, and interim
  verification worklists (recoverable from the repository's baseline commit).
