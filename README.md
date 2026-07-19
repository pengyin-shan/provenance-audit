# provenance-audit

Shared data-collection harness for the channel-provenance and citation-consistency
audits. One registry + collectors + ground-truth derivation feed every artifact:
RDA27, the Trusted CI plenary, the SC26 poster, EAGER, and CICI. See the project
plan for how the corpora map to artifacts; this README is how to run it.

```
provenance-audit/
  registry/        corpus_a_projects.yaml (citation), corpus_b_projects.yaml (HPC channels)
  provenance_audit/
    collect.py     CLI entry point
    github.py      repo metadata, latest release, key files
    metadata.py    CITATION.cff / codemeta.json / README-citation / channel parsers
    registries.py  PyPI (done); conda/npm/CRAN stubs
    archives.py    Zenodo (best-effort)
    groundtruth.py canonical facts with source + verified flags
    util.py        HTTP session, optional GitHub auth, graceful errors
  docs/SCHEMA.md   ground-truth field definitions + verification workflow
  outputs/         generated per-project JSON
```

## Setup

```bash
cd provenance-audit
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

**Set a GitHub token** (strongly recommended — raises the API limit from 60 to 5,000
requests/hour; without it a 16-project run will rate-limit):

```bash
export GITHUB_TOKEN=ghp_your_token_here   # a classic token with public_repo scope is enough
```

## Run

```bash
# Corpus B — HPC channel-provenance (Trusted CI / SC26 / EAGER ground truth)
python -m provenance_audit.collect --registry registry/corpus_b_projects.yaml --out outputs/corpus_b

# Corpus A — citation consistency (RDA / Sloan)
python -m provenance_audit.collect --registry registry/corpus_a_projects.yaml --out outputs/corpus_a

# One project at a time while iterating:
python -m provenance_audit.collect --registry registry/corpus_b_projects.yaml --out outputs/corpus_b --only kokkos
```

Each run prints a line per project and writes `outputs/<corpus>/<project>.json`
plus `_summary.json`. Bad repo slugs show as `ERR(repo:not_found)` — fix them in
the registry YAML and re-run (`--only <name>` to redo just that one).

## Score (channel-provenance, 4-category framework)

After collecting, score the records against the four-category framework:

```bash
python -m provenance_audit.score --in outputs/corpus_b --out outputs/corpus_b_scored
```

This writes, into the output dir:
- `matrix.csv` — projects x 4 categories (auto-score 0-1). This is the **poster heatmap**.
- `manual_checklist.csv` — every "manual" signal still needing human verification.
- `gap_analysis.json` — which framework signals are unique vs. already covered by Scorecard/SLSA/Sigstore (the **"covers vs. misses" gap figure**).
- `<project>.scorecard.json` — per-project signal-by-signal results.

The framework is defined in `provenance_audit/framework.py`: four categories
(identity & access, communication channels, knowledge infrastructure, distribution
metadata), each signal tagged `auto`/`manual` and with the existing tool that covers
it (if any). Edit that one file to adjust the rubric.

## The actual research step

Collection and `auto` scoring are automated; **`manual` signals are not** — and that
is the point. `manual_checklist.csv` is your verification worklist (MFA on channel
admins, official-channel statements, signed releases, SBOM, etc.). Confirm each
against the project's authoritative sources during ground-truth verification
(≈10-20 min/project); these verified facts are simultaneously the channel-provenance
assessment and the Corpus C (AI comprehension) answer key.

## Adding projects

Append to the registry YAML. Minimum is `name` + `repo: owner/name`. Add
`registries:` (e.g. `- {registry: pypi, package: numpy}`) and `zenodo: {record_id: ...}`
when you know them — more channels means a richer consistency comparison.

## Optional richer parsing

- **cffconvert** (`pip install cffconvert`) validates CITATION.cff and converts to
  BibTeX/APA; swap it into `metadata.parse_cff` if you want validation, not just parsing.
- **SoMEF** extracts metadata from READMEs with ML; heavier (Java + models). The
  built-in `extract_readme_citation` is the lightweight stand-in to start with.

## Not yet built (next stages, intentionally)

The other two scoring heads (`citation_consistency` for Corpus A, and `ai_response`
for Corpus C) and the model runner are deliberately not here yet — they plug into
these JSON records once collection is flowing. The channel-provenance scoring head
(`score.py`) IS built, since it is what the SC26 poster and the Trusted CI plenary
pilot need first.
