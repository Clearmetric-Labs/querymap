# CatalogKit

CatalogKit is a lightweight Python monorepo for headless catalog and lineage
tools. Shared graph rules live in `catalog-core`, and packages compose through
that core without duplicating shared logic or shared validation behavior.

## Packages

- `packages/catalog-core`: shared artifact models, canonical ID normalization,
  JSON serialization, merge semantics, and validation rules
- `packages/query-map`: SQL structure mapping for one statement at a time, with
  its existing public `QueryMap` contract preserved

Tools depend on `catalog-core`. Tools do not depend on each other.

## Repository Layout

```text
CatalogKit/
  packages/
    catalog-core/
    query-map/
  docs/
  .github/workflows/
```

## Core Rules

- `version` means shared artifact schema version only.
- Artifact schema versioning is owned by `catalog-core`, not package versions.
- Canonical IDs are normalized once in `catalog-core` and reused everywhere.
- Artifact merge semantics are defined once in `catalog-core`.
- Duplicate shared models or fallback code paths are not allowed.

## Local Development

Install both current packages in editable mode:

```bash
python -m pip install -e packages/catalog-core
python -m pip install -e "packages/query-map[dev,release]"
```

Run tests:

```bash
pytest -v
```

Build a package locally:

```bash
python -m build packages/catalog-core
python -m build packages/query-map
```

## Contract Docs

- [`packages/catalog-core/docs/contract.md`](packages/catalog-core/docs/contract.md)
- [`packages/query-map/docs/limitations.md`](packages/query-map/docs/limitations.md)

## License

CatalogKit is licensed under Apache 2.0. See [`LICENSE`](LICENSE).
