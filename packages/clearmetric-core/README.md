# clearmetric-core

One PyPI package. Column-level lineage and impact from SQL/dbt + warehouse metadata exports.

See the repo [`README.md`](../../README.md) and [`clearmetric-architecture.md`](../../clearmetric-architecture.md) for positioning. Warehouse metadata is a local INFORMATION_SCHEMA JSON export — not a live connector.

## Install

```bash
python -m pip install clearmetric-core
```

## CLI (v1 wedge)

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
| `clearmetric.lineage` | Column lineage (**Module B — wedge**) |
| `clearmetric.compiler` | Build, validate, impact orchestration |
| `clearmetric.adapters` | Warehouse JSON, dbt, SQL ingestion |
| `clearmetric.core` | Artifact, IDs, merge, bindings interop |
| `clearmetric.cleaner` / `clearmetric.policy` / `clearmetric.projection` / `clearmetric.emitters` | Checks, floor, catalog slice, output |
| `clearmetric.query` | Single-statement SQL (**Module A — library only**) |
| `clearmetric.powerbi` | PBIP lineage (not in CLI registry) |

## Imports

```python
from pathlib import Path
from clearmetric.compiler import build_graph, check_graph, compile
from clearmetric.core import attach_warehouse_bindings, merge, parse_column_selection
```

## Contract & example

- [`docs/contract.md`](docs/contract.md)
- [`../../spec/clearmetric-project.schema.json`](../../spec/clearmetric-project.schema.json)
- [`../../examples/wedge-jaffle`](../../examples/wedge-jaffle)
- [`../../docs/v1-boundary.md`](../../docs/v1-boundary.md)

```bash
python -m pip install -e ".[dev,release]"
```
