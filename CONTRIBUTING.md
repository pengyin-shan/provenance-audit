# Contributing

Thank you for your interest in this project. Contributions are welcome, with
the understanding that this is a research artifact maintained by a single
person (see [GOVERNANCE.md](GOVERNANCE.md)); response times reflect that.

## Ways to contribute

- **Corrections to the dataset.** If you maintain one of the assessed projects
  and believe a verified signal is wrong, open an issue titled
  `data correction: <project>` with a link to the authoritative source
  (repository file, release page, or documentation). Confirmed corrections are
  recorded in the changelog and, when releases warrant, in a revised Zenodo
  deposit.
- **Bug reports.** Open a GitHub issue with the command you ran, the full
  error output, and your Python version.
- **Code changes.** Fixes and improvements to the collectors, scoring, or
  figures. For anything larger than a small fix, open an issue first to
  discuss scope; the framework definition in `provenance_audit/framework.py`
  changes only with an accompanying changelog entry.

## Development setup

```bash
git clone https://github.com/pengyin-shan/provenance-audit
cd provenance-audit
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export GITHUB_TOKEN=...   # public_repo scope; needed for collection runs
```

## Pull requests

- Branch from `main`; one logical change per pull request.
- Describe what changed and why, and how you tested it. Collection code
  should be exercised against at least one real project
  (`--only <name>` keeps that cheap).
- Do not commit `.cache/`, virtual environments, or credentials of any kind.
  Tokens are read from the environment only.
- Disclose the use of AI tools in the pull request description; you remain
  responsible for understanding every line you submit.

## Review expectations

All pull requests are reviewed by the maintainer. Expect an initial response
within 5 business days; complex changes may take longer. The maintainer may
ask for revisions, or decline changes that do not fit the project's scope as
a point-in-time research artifact.
