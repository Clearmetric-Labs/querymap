# Wedge Jaffle Example

Warehouse-aware lineage using INFORMATION_SCHEMA metadata exports. Connect warehouse metadata, dbt, and SQL into one lineage graph — credential-free walkthrough with the jaffle shop dbt manifest fixture and a warehouse metadata JSON export.

## Prerequisites

```bash
pip install clearmetric-core   # or: pip install -e "packages/clearmetric-core[dev]"
cd examples/wedge-jaffle
```

The example references committed fixtures under `packages/clearmetric-core/tests/fixtures/` for the jaffle manifest, compiled SQL, and warehouse metadata schema.

## Commands

```bash
cm scan
cm compile --format json > graph.json
cm compile --format catalog > catalog.json
cm impact orders.amount --upstream --format json
cm clean
cm contract graph.json
```

To attach local warehouse metadata instead of the shared fixture path:

```bash
cm connect warehouse --information-schema ../../packages/clearmetric-core/tests/fixtures/wedge/jaffle_warehouse_schema.json
```

## What this demonstrates

- Project-first CLI via `clearmetric.yaml` (no positional manifest paths, no `--dialect` flag)
- Warehouse metadata ingestion with physical bindings on table/column nodes
- Optional `aliases` path for mismatched dbt/warehouse table names
- dbt manifest lineage merged with warehouse metadata
- Catalog output (`compile --format catalog`) with table/column/model nodes only
- Report-only `cm clean` (errors fail exit; warnings never fail exit regardless of posture)
- Contract validation against `spec/catalog-artifact.schema.json`

Power BI remains available as `clearmetric.powerbi` but is not part of the warehouse CLI source registry.
