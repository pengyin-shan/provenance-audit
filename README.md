# provenance-audit

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

## Setup

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

**Set a GitHub token** (strongly recommended — raises the API limit from 60 to
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
plus `_summary.json`. Bad repo slugs show as `ERR(repo:not_found)` — fix them in the
registry YAML and re-run (`--only <name>` to redo just that one).

Scoring writes, into the output dir:
- `matrix.csv` — projects × 4 categories (auto-score 0-1); this is the poster heatmap.
- `manual_checklist.csv` — every `manual` signal still needing human verification.
- `gap_analysis.json` — which framework signals are unique vs. already covered by
  Scorecard / SLSA / Sigstore.
- `<project>.scorecard.json` — per-project signal-by-signal results.

## The manual verification step

Collection and `auto` scoring are automated; `manual` signals are not — and that is
the point of the framework. The subsampled panel is verified by hand against each
project's authoritative sources (repository, releases, documentation site,
README-linked pages; ~10-20 min/project). The verified result of that process for
the SC26 poster is `outputs/verify_worklist_30_CANONICAL.csv`, produced by manual
curation of the subsample output during verification.

## Adding projects

Append to the registry YAML. Minimum is `name` + `repo: owner/name`. Add
`registries:` (e.g. `- {registry: pypi, package: numpy}`) and
`zenodo: {record_id: ...}` when you know them.

## Optional richer parsing

- **cffconvert** (`pip install cffconvert`) validates CITATION.cff and converts to
  BibTeX/APA; swap it into `metadata.parse_cff` for validation, not just parsing.
- **SoMEF** extracts metadata from READMEs with ML; heavier (Java + models). The
  built-in `extract_readme_citation` is the lightweight stand-in.
