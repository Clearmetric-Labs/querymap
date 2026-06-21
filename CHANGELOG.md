# Changelog

All notable changes to this project will be documented in this file.

## 0.1.7 - 2026-06-21

### Changed

- refreshed the root README to lead with the code-derived catalog positioning, a verified compile snippet, and accurate tool descriptions
- `build_openlineage_export` now accepts a pre-built `CatalogArtifact`, so OpenLineage export can chain after `build_catalog_artifact` without reloading the project

## 0.1.2 - 2026-06-20

### Changed

- aligned `catalogkit-lineage` package exports, README examples, and local development instructions with the existing CatalogKit module conventions
- grouped OpenLineage export inputs by output column instead of emitting one export row per lineage edge
- made lineage traversal selections and manifest compiled-path handling fail loudly on invalid input
- tightened release metadata so the coordinated `0.1.2` package set resolves to the freshly published module versions
- added publish-time version checks so package tags cannot drift from source versions

### Added

- first PyPI release of `catalogkit-lineage` for project-level SQL lineage from dbt manifests and SQL folders
- focused lineage regression coverage for grouped OpenLineage export, unknown traversal selections, manifest path escapes, and duplicate SQL-folder dataset names

### Supported

- `SELECT ...`
- `INSERT ... SELECT ...`
- `CREATE ... AS SELECT ...`

### Deferred

- output column lineage
- join semantics beyond dependency mapping
- wrapper target outputs
- warehouse-aware `SELECT *` expansion
