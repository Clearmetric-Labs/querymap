# clearmetric-core

One PyPI package for the ClearMetric analytics backbone: a canonical, queryable graph
compiled from SQL, dbt, and warehouse metadata exports.

See the repo [`README.md`](../../README.md) and [`clearmetric-architecture.md`](../../clearmetric-architecture.md) for positioning. Warehouse metadata is a local INFORMATION_SCHEMA JSON export — not a live connector.

## Install

```bash
python -m pip install clearmetric-core
```

## CLI

```bash
cm init
cm connect warehouse --information-schema ./warehouse_schema.json
cm scan
cm compile --format json > graph.json
cm compile --format catalog > catalog.json
cm impact column.fct_orders.net_revenue --upstream
cm clean
cm contract graph.json
```

If `cm` is occupied: `python -m clearmetric.cli --project-dir . compile --format json`

## Modules

| Module | Purpose |
|--------|---------|
| `clearmetric.lineage` | SQL/dbt artifact build |
| `clearmetric.graph` | `GraphView`, impact trace, traversal render, graph slices |
| `clearmetric.compiler` | Build, validate, impact orchestration |
| `clearmetric.adapters` | Warehouse JSON, dbt, SQL ingestion |
| `clearmetric.core` | Artifact, IDs, merge, bindings interop |
| `clearmetric.cleaner` / `clearmetric.policy` / `clearmetric.projection` / `clearmetric.emitters` | Checks, security floor, projections, output formats |
| `clearmetric.query` | Single-statement SQL structure and contract support |
| `clearmetric.powerbi` | PBIP lineage (not in CLI registry) |

## Imports

```python
from pathlib import Path
from clearmetric.compiler import build_graph, check_graph, compile
from clearmetric.core import attach_warehouse_bindings, merge, parse_column_selection
```

## Contract & example

- [`../../docs/reference/contract.md`](../../docs/reference/contract.md)
- [`src/clearmetric/spec/clearmetric-project.schema.json`](src/clearmetric/spec/clearmetric-project.schema.json)

```bash
python -m pip install -e ".[dev,runtime,release]"
```
