# clearmetric.powerbi Limitations (V1)

## Supported

- PBIP project discovery (`.pbip` file or project folder)
- TMDL table `source =` M expression extraction
- M upstream source extraction via `pbi_parsers`
- `Sql.Database` and `Value.NativeQuery` patterns (native SQL table refs extracted in-module)
- PBIR visual measure/column bindings
- Cross-graph merge metadata via `match_status`

## Deferred

- Deep DAX measure → column lineage
- Full TMDL semantic model parsing beyond table `source` blocks
- Live Power BI / Fabric API sync
- All M connector types (file, web, SharePoint) — may parse but are not V1-validated

## Failure Policy

- **Structural errors** (missing folders, invalid JSON) fail loudly.
- **Semantic gaps** (unresolved warehouse join, unsupported M pattern) emit warnings and continue with explicit `match_status`.

## Composition

`clearmetric.powerbi` depends on `clearmetric.core` only. Build warehouse and BI artifacts separately, then merge via `clearmetric.core.merge()` or `merge_with_warehouse()` — see repo [`docs/orchestration.md`](../../../../docs/orchestration.md).

Example:

```bash
cm compile ./target/manifest.json --dialect postgres
```

```python
from clearmetric.powerbi import build_catalog_artifact, merge_with_warehouse
from clearmetric.lineage import build_catalog_artifact as build_warehouse

warehouse = build_warehouse("./target/manifest.json", dialect="postgres")
powerbi = build_catalog_artifact("./MyReport.pbip")
merged = merge_with_warehouse(powerbi, warehouse)
```
