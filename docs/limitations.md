# Limitations (v1)

ClearMetric Core v1 is a **local compiler**, not a live metadata platform.

## Resolution

- Column lineage depends on parseable compiled SQL and known upstream schemas.
- Bare `SELECT *` expands only when exactly one resolvable source has known columns; joins and unknown schemas suppress expansion.
- Star expansion requires a declared upstream column set (seed, source, warehouse metadata, or dbt `columns:`), not columns inferred from upstream SQL-folder models.
- UNION branches and some set operations emit `unresolved_lineage` rather than inventing positional merges.
- Warehouse binding uses qualified names and suffix matching; ambiguous unqualified names refuse to bind.

## Identity

- dbt ↔ warehouse binding is **partial**: database/schema/name alignment with ambiguity refusal.
- Two tables with the same unqualified name in different databases must not cross-impact via suffix bridge alone.

## Scope

- No live warehouse or dbt Cloud connector — local JSON and artifacts only.
- Intent/metrics ingestion requires `CM_EXPERIMENTAL=1`.
- Lab formats (`consumer-catalog`, `frontend-contract`, `ai-context`, `cm query`, `cm serve`) are experimental.

Detailed SQL patterns: [`reference/lineage-limitations.md`](reference/lineage-limitations.md).
