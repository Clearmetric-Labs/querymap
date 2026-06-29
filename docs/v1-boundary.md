# ClearMetric Core Boundaries

Scope guardrails for what is shipped in open source vs deferred. This file covers **both**
the warehouse wedge CLI and the Power BI module.

## Warehouse wedge (v1 — shipped CLI)

Warehouse-aware lineage using INFORMATION_SCHEMA **metadata exports** only. No live warehouse
connector, query execution, or credential-based ingestion in v1.

### In scope

| Capability | Module | Notes |
|---|---|---|
| Project config | `clearmetric.core.project` | `clearmetric.yaml`, posture, policy path, optional aliases |
| Source ingestion | `clearmetric.adapters` | `information_schema` JSON, dbt manifest, SQL folders |
| Build + bind | `clearmetric.compiler` | ingest → merge → `attach_warehouse_bindings` |
| Validation | `clearmetric.compiler.validate` | `check_graph`, `enforce_graph` |
| Checks | `clearmetric.cleaner` | Structural checks + merge/drift warnings via posture |
| Security floor | `clearmetric.policy` | Enforced at compile/contract; not a full policy compiler |
| Graph traversal | `clearmetric.graph` | Impact trace, selectors, traversal render; lineage builds artifacts only |
| Catalog slice | `clearmetric.projection` + emitters | `compile --format catalog` (table/column/model only) |
| OpenLineage export | `clearmetric.emitters` | `compile --format openlineage` (ungated admin export) |
| CLI | `clearmetric.cli` | `init`, `connect warehouse`, `scan`, `compile`, `impact`, `clean`, `contract` |

### Out of scope (v1 wedge)

- Live Snowflake or other warehouse connectors
- `serve`, `cm query`, query endpoint, metrics/query YAML / intent adapter in CLI
- `compile --format consumer-catalog`, `frontend-contract`, `ai-context` (identity-gated exports)
- `cm impact --identity` governance preview
- `cm catalog` as a separate command (use `compile --format catalog`)
- User-defined cleaner checks and graph query API
- Policy compiler to warehouse RLS / OPA
- Full RBAC completeness checks (owner/classification required on every node)

### Success criteria

```bash
cm init
cm connect warehouse --information-schema ./warehouse_schema.json
cm scan
cm compile --format json > graph.json
cm compile --format catalog > catalog.json
cm impact orders.amount --upstream
cm clean          # exit 1 on errors only; warnings never fail exit
cm contract graph.json
```

See [`examples/lineage-demo/README.md`](https://github.com/ClearMetric-Labs/ClearMetric-Core/blob/main/examples/lineage-demo/README.md).

Gated post-wedge work (metrics/queries, runtime, policy-gated exports) is documented in [`future-roadmap-gated.md`](future-roadmap-gated.md) and requires [`adoption-gate.md`](adoption-gate.md) evidence before shipping. Internal lab primitives are built and tested in [`backbone-lab.md`](backbone-lab.md) (`CM_EXPERIMENTAL=1` only). Backbone Phase 0 (GraphView consolidation) is complete in 0.5.1; see [`backbone-v2-roadmap.md`](backbone-v2-roadmap.md) for sequencing.

---

## Power BI module (V1 — Python API, not CLI registry)

Foundational, open-source-worthy scope only. Anything not listed here is deferred.

### In scope

| Capability | Module | Notes |
|---|---|---|
| PBIP/PBIR discovery | `clearmetric.powerbi` | Walk repo-resident Power BI project folders |
| M upstream source extraction | `clearmetric.powerbi` | `pbi_parsers` as authoritative M parser |
| Native SQL detection | `clearmetric.powerbi` | Detect `Value.NativeQuery`; orchestrate with `clearmetric.query` externally |
| Report/page/visual bindings | `clearmetric.powerbi` | PBIR JSON binding extraction |
| Canonical FQN normalization | `clearmetric.core` | Single source of truth for cross-graph matching |
| Alias map contract | `clearmetric.core` | `load_table_alias_map()` for version-1 YAML overrides |
| `match_status` on cross-graph edges | `clearmetric.core` | `resolved \| ambiguous \| unresolved` |
| Artifact merge | `clearmetric.core` | Warehouse + BI graphs merge by canonical ID |
| Lineage composition | orchestration | `clearmetric.lineage` artifact + `clearmetric.powerbi` artifact → `merge()` |

### Out of scope (Power BI V1)

- Deep DAX measure → column lineage
- Full TMDL semantic model parser
- Live Power BI / Fabric Scanner API or service-principal sync
- Enterprise adapters (`PowerBIMapAdapter`, etc.)
- Auth, RLS, RBAC, or full governance rule compiler
- Semantic execution or business-definition projection
- Frontend / UI
- Cross-module imports (`clearmetric.powerbi` must not import `clearmetric.query`)

### Error policy

1. **Structural failure → loud error.** Missing PBIP root, corrupt JSON, unprocessable folder layout.
2. **Semantic gap → warning + continue.** Unresolved warehouse↔BI join, ambiguous alias, unsupported connector — emit explicit state in artifact; do not fail the whole walk.

Power BI composition with the warehouse wedge is optional via Python merge (not part of the
warehouse CLI source registry):

```python
from clearmetric.core import merge
from clearmetric.powerbi import build_catalog_artifact, merge_with_warehouse
# merge in Python via clearmetric.core.merge() / merge_with_warehouse()
```

…producing one graph where warehouse columns connect to PBI tables and visuals, with honest
`match_status` on every cross-graph edge.
