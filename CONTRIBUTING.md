# Contributing

Thanks for contributing to `querymap`.

## Setup

Create a virtual environment and install the project in editable mode:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev,release]"
```

## Run The Checks

Run the local test suite:

```bash
pytest -v
```

Build and validate the package before release-facing changes:

```bash
python -m build
twine check dist/*
```

## Release Workflow

PyPI Trusted Publishing should point at `.github/workflows/publish.yml`.

- workflow file: `publish.yml`
- GitHub Actions environment: `pypi`
- trigger: GitHub Release publication or manual `workflow_dispatch`

## Contribution Rules

- Keep the public contract narrow and explicit.
- Reuse the centralized public API instead of introducing parallel entrypoints.
- Remove duplicate, dead, or fallback behavior instead of preserving it behind compatibility layers.
- Fail loudly on unsupported input rather than returning partial or ambiguous output.
- Keep docs, tests, and code aligned in the same change.
- Add tests only where they materially protect the public contract or release path.

## Scope Guardrails

This OSS package is intentionally limited. Do not add:

- enterprise adapters
- proprietary comparison logic
- auth, RBAC, or RLS behavior
- route handlers or API wiring
- warehouse-connected enrichment paths

## Pull Requests

Keep pull requests small, direct, and honest about scope. If a change expands the
public contract, update `README.md`, `docs/artifact-schema.md`, and the
relevant tests in the same pull request.
