# clearmetric-core

One PyPI package. All ClearMetric Core modules (`clearmetric.core`, `.lineage`,
`.query`, `.powerbi`, `.cli`) ship inside this distribution.

## Install

```bash
python -m pip install clearmetric-core
```

## CLI

```bash
cm compile ./manifest.json --dialect postgres
cm impact orders.amount ./manifest.json --dialect postgres --upstream
```

If `cm` is occupied on your PATH:

```bash
python -m clearmetric.cli compile ./manifest.json --dialect postgres
```

## Modules

| Module | Purpose |
|--------|---------|
| `clearmetric.core` | Artifact schema, canonical IDs, merge, cross-graph interop |
| `clearmetric.lineage` | Project-level SQL lineage from dbt manifests and SQL folders |
| `clearmetric.query` | Single-statement SQL structure mapping |
| `clearmetric.powerbi` | PBIP file lineage and warehouse merge |
| `clearmetric.cli` | `cm` command router |

## Imports

```python
from clearmetric.core import (
    CatalogArtifact,
    Edge,
    Evidence,
    Node,
    Warning,
    load_table_alias_map,
    merge,
    resolve_table_match,
)
from clearmetric.lineage import build_catalog_artifact, trace_upstream
```

For local development:

```bash
python -m pip install -e ".[dev,release]"
```

## Contract

The source of truth for the shared artifact contract is
[`docs/contract.md`](docs/contract.md).
