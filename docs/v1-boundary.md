# ClearMetric Core Power BI V1 Boundary

Foundational, open-source-worthy scope only. Anything not listed here is deferred.

## In V1

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

## Out of V1

- Deep DAX measure → column lineage
- Full TMDL semantic model parser
- Live Power BI / Fabric Scanner API or service-principal sync
- Enterprise adapters (`PowerBIMapAdapter`, etc.)
- Auth, RLS, RBAC, policy, or governance
- Semantic execution or business-definition projection
- Frontend / UI
- Cross-module imports (`clearmetric.powerbi` must not import `clearmetric.query`)

## Error Policy

1. **Structural failure → loud error.** Missing PBIP root, corrupt JSON, unprocessable folder layout.
2. **Semantic gap → warning + continue.** Unresolved warehouse↔BI join, ambiguous alias, unsupported connector — emit explicit state in artifact; do not fail the whole walk.

## Success Criteria

A developer can run:

```bash
cm compile ./manifest.json --dialect postgres > warehouse.json
python -c "from clearmetric.powerbi import build_catalog_artifact; ..."  # powerbi artifact
# merge in Python via clearmetric.core.merge()
```

…and get one graph where warehouse columns connect to PBI tables and visuals, with honest `match_status` on every cross-graph edge.
