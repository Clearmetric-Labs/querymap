# Artifact-Level Orchestration (Optional)

Each ClearMetric Core module is **standalone and headless**. Use `cm compile` or
the Python APIs directly; each module emits a valid artifact on its own.

Composition is **optional**. When you want warehouse + BI in one graph, merge
artifacts in Python via `clearmetric.core.merge()` — nothing more.

Full contract: [`packages/clearmetric-core/docs/contract.md`](../packages/clearmetric-core/docs/contract.md)

## Standalone usage

```bash
pip install clearmetric-core
cm compile ./target/manifest.json --dialect postgres
```

Power BI PBIP lineage via Python API:

```python
from clearmetric.powerbi import build_catalog_artifact

artifact = build_catalog_artifact("./MyReport.pbip")
```

## Optional composition

```python
from clearmetric.core import load_table_alias_map, merge
from clearmetric.lineage import build_catalog_artifact as build_warehouse
from clearmetric.powerbi import build_catalog_artifact as build_powerbi, merge_with_warehouse

warehouse = build_warehouse("./target/manifest.json", dialect="postgres")
powerbi = build_powerbi("./MyReport.pbip")

alias_map = load_table_alias_map("./aliases.yaml")  # optional
merged = merge_with_warehouse(powerbi, warehouse, alias_map=alias_map)
```

Native SQL inside M is extracted by `clearmetric.powerbi`. For deeper SQL lineage,
run `clearmetric.query` separately on the SQL text and merge that artifact too.

## Rules

1. Each module uses **`clearmetric.core` only** — never imports from sibling modules at build time.
2. One merge contract — `clearmetric.core.merge()` and core interop helpers only.
3. Cross-graph join quality is visible via `match_status` on edges.

## Future

`cm contract` may wrap artifact validation as a CI gate. It is not shipped yet.
