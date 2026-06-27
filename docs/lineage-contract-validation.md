# `clearmetric.lineage` Contract Validation

**Source of truth:** [`packages/clearmetric-core/docs/contract.md`](../packages/clearmetric-core/docs/contract.md)

**Enterprise adapter:** reference only — integration lag must not drive OSS design.

## Public API (validated)

```python
from clearmetric.lineage import (
    build_catalog_artifact,
    build_lineage_map,
    build_openlineage_export,
    trace_downstream,
    trace_upstream,
)
```

| Function | Input | Output |
|---|---|---|
| `build_lineage_map(project_input, dialect=...)` | dbt manifest path or SQL folder | `LineageMap` with `.nodes`, `.edges`, `.summary` |
| `build_catalog_artifact(project_input, dialect=...)` | same | `CatalogArtifact` |
| `trace_upstream/downstream(project_input, selection, dialect=...)` | `"model.column"` | `TraversalResult.related_ids` (canonical column IDs) |
| `build_openlineage_export(project_input, dialect=...)` | same | OpenLineage-shaped dict |

## Merge Assumptions for `clearmetric.powerbi`

See core contract for warehouse namespace, alias map, and `match_status` rules.
Lineage emits warehouse `table:` IDs from dbt model names (e.g. `table:orders`).

## Enterprise Drift (integration lag, not OSS gaps)

| Area | ClearMetric Core OSS | Enterprise repo |
|---|---|---|
| Package pin | Published on PyPI as `clearmetric-core` | May lag behind OSS |
| Adapter | N/A | `LineageMapAdapter` with lazy import |
| Tests | Full corpus in ClearMetric Core | Adapter tests lock expected API |

Enterprise should follow OSS contracts when wiring adapters — not the reverse.

## Optional Composition

```
table:orders  --feeds-->  table:<project>.semantic_model.orders
                          match_status: resolved | ambiguous | unresolved
```

Run modules separately; merge via `clearmetric.core.merge()` or `merge_with_warehouse()`.
See [`docs/orchestration.md`](orchestration.md).
