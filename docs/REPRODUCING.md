# Reproducing the SC26 dataset

This document gives the exact commands behind the published dataset. Read the
point-in-time note first; it determines what "reproducing" can mean here. You should be able to find all codes/doc in https://github.com/pengyin-shan/provenance-audit.

## Point-in-time note

The corpus is a snapshot of 87 projects collected and scored in **July 2026**
(frozen scored set: `outputs/corpus_keep_scored_FROZEN_20260706/`). The
measured projects change continuously: they add security policies, publish
releases, and reorganize channels. Re-running collection today reproduces the
*pipeline*, not the *numbers*. To analyze the published dataset, use the
frozen outputs in this repository or the Zenodo deposit
(DOI: [10.5281/zenodo.21443211](https://doi.org/10.5281/zenodo.21443211));
do not re-collect.

## Requirements

- Python 3.11 with the pinned dependencies (`pip install -r requirements.txt`).
- A GitHub token in the environment. Collection makes thousands of API calls;
  the unauthenticated limit of 60 requests/hour will not complete a corpus run.

```bash
export GITHUB_TOKEN=...   # classic token, public_repo scope is enough
```

The token is read from the environment only and never written to the cache or
the outputs. HTTP responses are cached in `.cache/`, so re-runs are cheap and
interrupted runs resume without repeating completed requests.

## Pipeline

```bash
# 1. Sampling frame: GitHub organizations + ecosystem topics, star threshold
python -m provenance_audit.frame --out registry/corpus_100.yaml --min-stars 40 --per-domain 60

# 2. Collect the frame, then curate it down to genuine research software
python -m provenance_audit.collect --registry registry/corpus_100.yaml --out outputs/corpus_100
python -m provenance_audit.curate --registry registry/corpus_100.yaml \
    --summary outputs/corpus_100/_summary.json --out-prefix registry/corpus
# Curation writes registry/corpus_keep.yaml (87 projects for the published run),
# registry/corpus_review.csv (judgment calls), and registry/corpus_drop.csv.

# 3. Collect the curated corpus
python -m provenance_audit.collect --registry registry/corpus_keep.yaml --out outputs/corpus_keep

# 4. Score all 87 projects against the 18-signal framework
python -m provenance_audit.score --in outputs/corpus_keep --out outputs/corpus_keep_scored

# 5. Draw the manual-verification panel (stratified by domain and posture tier)
python -m provenance_audit.subsample --scored outputs/corpus_keep_scored --n 30 --seed 7 \
    --out outputs/verify_subsample_30.csv

# 6. Figures (heatmaps + signal-prevalence table, overall and per domain)
python -m provenance_audit.figures --scored outputs/corpus_keep_scored --out outputs/figures --split-domain
```

Steps 1, 2, and 5 are deterministic given the same API responses (the frame is
star-thresholded and the subsample is seeded); steps 3 and 4 are deterministic
given the same responses as well, which is why the frozen outputs, not a
re-collection, are the dataset of record.

## The manual verification layer

The nine `manual` signals cannot be reproduced by re-running code; they were
verified by hand (approximately 10 to 20 minutes per project) against each
project's repository, releases, documentation site, and README-linked pages.
The published result is `outputs/verify_worklist_30_CANONICAL.csv`, produced
by manual curation of the subsample output during verification (finalized
July 19, 2026). MFA on channel administrators was unobservable for all 30
projects and is recorded as unknown.

## Dataset of record

| Artifact | Location |
|---|---|
| Curated registry (87 projects) | `registry/corpus_keep.yaml` |
| Collected records | `outputs/corpus_keep/` |
| Frozen scored set | `outputs/corpus_keep_scored_FROZEN_20260706/` |
| Hand-verified 30-project panel | `outputs/verify_worklist_30_CANONICAL.csv` |
| Figures | `outputs/figures/` |
| Archived deposit | Zenodo, DOI: [10.5281/zenodo.21443211](https://doi.org/10.5281/zenodo.21443211) |
