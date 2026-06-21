# CatalogKit

**CatalogKit** is a lightweight, modular toolkit for building data catalog and
lineage systems.

**Status:** CatalogKit is in early development (0.x). Current release: **0.1.4**.
Pin versions for anything you depend on.

Many catalog tools are expensive, platform-heavy, or more than a small team
needs. CatalogKit takes a simpler approach: headless, deterministic primitives
that extract structure from the SQL and analytics code you already have, then
emit it as a clean, mergeable artifact. Install only what you need, compose the
pieces yourself, and build the catalog or lineage layer your team actually
wants without standing up a full platform.

**Launch claim:** correct where resolvable, explicit where not, no credentials.
Not universal dbt column lineage.

Start with one query. `catalogkit-query` maps a single SQL statement into its
relations and dependencies, so you can understand inherited SQL fast.

`catalogkit-lineage` maps project-level column impact across dbt manifests or SQL
folders for pre-merge change analysis.

## How It Works

CatalogKit is a Python monorepo of independently installable packages. Shared
graph models, canonical IDs, serialization, merge semantics, and validation
rules live in `catalogkit-core`. Each tool composes through that core and never
depends on another tool, so independent tools can produce graphs that merge
cleanly.

## Packages

- `catalogkit-core` - shared artifact models, canonical IDs, serialization,
  merge, and validation
- `catalogkit-query` - single-statement SQL structure mapping that preserves the
  `QueryMap` contract
- `catalogkit-lineage` - project-level SQL lineage for dbt manifests and SQL
  folders
- `catalogkit` - thin meta-package for convenience installs

## Install

Install individual CatalogKit modules directly when you only want a subset of
the suite.

Install the current CatalogKit module set:

```bash
python -m pip install catalogkit
```

Import from the shared namespace:

```python
from catalogkit.core import Node, Edge, Evidence
from catalogkit.query import build_query_map
from catalogkit.lineage import build_lineage_map
```

## Repository Layout

```text
CatalogKit/
  packages/
    catalogkit-core/
    catalogkit-query/
    catalogkit-lineage/
    catalogkit/
  docs/
  .github/workflows/
```

## Namespace Rules

- `catalogkit` is a native PEP 420 namespace package.
- No package in this repo may ship `catalogkit/__init__.py`.
- The `catalogkit` meta-package provides dependency metadata only. It must not
  provide an importable `catalogkit` Python package on disk.

## Core Rules

- `version` means shared artifact schema version only.
- Artifact schema versioning is owned by `catalogkit-core`, not package versions.
- Canonical IDs are normalized once in `catalogkit-core` and reused everywhere.
- Artifact merge semantics are defined once in `catalogkit-core`.
- Duplicate shared models or fallback code paths are not allowed.

## Local Development

Install the current packages in editable mode:

```bash
python -m pip install -e packages/catalogkit-core
python -m pip install -e "packages/catalogkit-query[dev,release]"
python -m pip install -e "packages/catalogkit-lineage[dev,release]"
```

Build the meta-package when you want to validate the convenience install path:

```bash
python -m build packages/catalogkit
```

Run tests:

```bash
python -m pytest -v
```

Build a package locally:

```bash
python -m build packages/catalogkit-core
python -m build packages/catalogkit-query
python -m build packages/catalogkit-lineage
python -m build packages/catalogkit
```

## Contract Docs

- [`packages/catalogkit-core/docs/contract.md`](packages/catalogkit-core/docs/contract.md)
- [`packages/catalogkit-query/docs/limitations.md`](packages/catalogkit-query/docs/limitations.md)
- [`packages/catalogkit-lineage/docs/limitations.md`](packages/catalogkit-lineage/docs/limitations.md)

## License

CatalogKit is licensed under Apache 2.0. See [`LICENSE`](LICENSE).
