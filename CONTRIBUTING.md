# Contributing

Thanks for contributing to `CatalogKit`.

## Setup

Create a virtual environment and install the packages you need in editable mode:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e packages/catalog-core
python -m pip install -e "packages/query-map[dev,release]"
```

## Run The Checks

Run the local test suite:

```bash
pytest -v
```

Build and validate packages before release-facing changes:

```bash
python -m build packages/catalog-core
python -m build packages/query-map
twine check packages/catalog-core/dist/*
twine check packages/query-map/dist/*
```

## Release Workflow

PyPI Trusted Publishing should point at `.github/workflows/publish.yml`.

- workflow file: `publish.yml`
- GitHub Actions environment: `pypi`
- trigger: package tag push or manual `workflow_dispatch`

## Contribution Rules

- Keep the public contract narrow and explicit.
- Reuse the centralized public API instead of introducing parallel entrypoints.
- Remove duplicate, dead, or fallback behavior instead of preserving it behind compatibility layers.
- Fail loudly on unsupported input rather than returning partial or ambiguous output.
- Keep docs, tests, and code aligned in the same change.
- Add tests only where they materially protect the public contract or release path.

## Scope Guardrails

This OSS monorepo is intentionally limited. Do not add:

- enterprise adapters
- proprietary comparison logic
- auth, RBAC, or RLS behavior
- route handlers or API wiring
- warehouse-connected enrichment paths

## Pull Requests

Keep pull requests small, direct, and honest about scope. If a change expands the
public contract, update `README.md`,
`packages/catalog-core/docs/contract.md`, and the relevant tests in the same
pull request.
