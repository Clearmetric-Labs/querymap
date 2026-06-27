# Rule 1 Kill-Test: `clearmetric.powerbi`

**Status:** GO  
**Date:** 2026-06-25  
**Decision:** Build `clearmetric.powerbi` V1 with the narrow scope defined in [v1-boundary.md](../v1-boundary.md).

## Question

Is a PBIP-walking ClearMetric Core module meaningfully better than calling `pbi_parsers` directly and reading the dbt manifest?

## Obvious Alternative

1. **`pbi_parsers`** — parses M and DAX into ASTs; extracts connector and reference metadata.
2. **dbt manifest lineage** — warehouse-side model and column dependencies from `manifest.json`.

Together, these still produce **two separate outputs** with no shared canonical IDs, no cross-graph edges, and no mergeable artifact suitable for CI blast-radius checks.

## Prototype Result

A prototype traced one warehouse column through:

`dbt model column → M native SQL source → Power BI semantic-model table`

The stitch required:

- normalized fully-qualified table names on both sides,
- explicit `match_status` on the join edge,
- merge into the shared ClearMetric Core artifact format.

Naive regex-only M extraction broke on realistic patterns. The hard part was not parsing — it was **canonical naming and merge**.

## Why The Stitched Artifact Wins

| Capability | `pbi_parsers` + dbt manifest | `clearmetric.powerbi` + core merge |
|---|---|---|
| M/DAX AST | Yes | Delegates M to `pbi_parsers`; DAX deferred in V1 |
| Warehouse lineage | Yes (manifest) | Composes with `clearmetric.lineage` artifact |
| Canonical IDs | No | Yes — shared `clearmetric.core` contract |
| Cross-graph edges | No | Yes — warehouse table ↔ PBI table |
| CI blast-radius | Manual glue | One merged artifact: "column change hits N visuals" |
| Honest unresolved joins | N/A | `match_status: unresolved \| ambiguous \| resolved` |

**The differentiation is the merge, not the parsing.**

Raw parser output cannot answer: *"If `orders.amount` changes, which report visuals break?"* That requires one traversable graph with canonical IDs — exactly what ClearMetric Core emits.

## Approved V1 Scope

- PBIP/PBIR folder discovery
- M upstream source extraction (`pbi_parsers`)
- native SQL detection (orchestrate with `clearmetric.query` at artifact level — no cross-module import)
- report/page/visual binding extraction
- artifact emission with warnings for unresolved semantics

## Explicitly Deferred

- deep DAX column lineage
- full TMDL parser
- live Power BI / Fabric connectors
- enterprise adapters, auth, RLS, RBAC
- semantic execution / business-definition logic
- UI or frontend work

## Failure Policy

- **Hard-fail:** corrupt or unprocessable PBIP structure (missing required folders, invalid JSON).
- **Warn-and-continue:** individual unresolved semantic joins, ambiguous FQN matches, unsupported M/DAX patterns — emit node/edge with explicit `match_status` and continue the walk.

## Go / No-Go

**GO.** The module is justified because it produces a mergeable, CI-ready artifact that `pbi_parsers`-direct cannot. Parsing is a dependency; the product value is the stitch.
