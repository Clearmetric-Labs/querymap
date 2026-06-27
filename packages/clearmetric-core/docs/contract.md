# clearmetric-core Contract

`clearmetric-core` is the sole PyPI distribution for ClearMetric Core. It owns the
serialized artifact contract used by all `clearmetric.*` modules and downstream
consumers.

This artifact schema is pre-1.0 and may change. Breaking changes will bump the
schema `version` field and the package minor version while in 0.x. The contract
will stabilize at 1.0.

## Artifact Version

- `version` means artifact schema version only.
- `version` is owned by `clearmetric.core`.
- `version` is decoupled from the `clearmetric-core` PyPI package version.
- New capabilities ship as `clearmetric.*` subpackages inside `clearmetric-core`, not
  as separate PyPI distributions.
- Bump `version` only for breaking changes to the serialized artifact contract.
- Non-breaking additions must not bump `version`.

Current artifact schema version: `1`

## Artifact Shape

Every serialized artifact has this shape:

```text
CatalogArtifact
  version
  nodes
  edges
  warnings
```

## Node Contract

Every node has:

- `id`
- `kind`
- `name`
- `qualified_name`
- `schema`
- `evidence`

`kind` is one of:

- `table`
- `cte`
- `column`
- `model`
- `report`
- `visual`
- `page`
- `measure`

## Edge Contract

Every edge has:

- `kind`
- `source_id`
- `target_id`
- `label`
- `confidence`
- `match_status` (optional; `resolved`, `ambiguous`, or `unresolved` for cross-graph joins)
- `evidence`

`kind` is one of:

- `depends_on`
- `feeds`
- `derives_from`
- `references`
- `joins`

## Evidence Contract

Evidence is where tools attach supporting observations without changing entity
identity.

Every evidence entry has:

- `file`
- `location`
- `expression`
- `confidence`

Multiple tools may attach evidence to the same node or edge. That is the normal
composition path.

## Merge Semantics

`merge()` is a contract feature of `clearmetric-core`, not a tool-local policy.

### Nodes

- Nodes merge by canonical `id`.
- Same `id` means the two nodes claim to describe the same entity.
- Evidence is unioned across matching nodes.
- Non-evidence attributes are merged field by field.
- If one side provides a value and the other side leaves that field empty, the
  populated value wins.
- If both sides provide non-empty different values for the same non-evidence
  field, merge fails with a typed error. There is no last-write-wins behavior.

### Edges

- Edges dedupe by `(kind, source_id, target_id)`.
- Evidence is unioned across matching edges.
- For other edge fields such as `label`, `confidence`, and `match_status`, a populated value may
  fill an empty value.
- Conflicting non-empty edge attributes fail with a typed error.

### Warnings

- Warnings dedupe by their stable structural fields: `code`, `message`, and
  `location`.
- Warnings may optionally include `subject_id` when they are scoped to a
  specific canonical entity such as a `column:` node.
- When present, `subject_id` participates in warning dedupe alongside `code`,
  `message`, and `location`.

## Canonical ID Rules

Canonical IDs are the highest-risk correctness surface in ClearMetric Core. If tools
normalize identifiers differently, graphs do not merge.

### Normalization Rules

- Identifier normalization is defined once in `clearmetric-core`.
- Tools must reuse `clearmetric-core` normalization helpers and must not implement
  local copies.
- Identifier parts are trimmed, unquoted, and lowercased before ID generation.
- Equivalent names such as `Analytics.Orders`, `analytics.orders`, and
  `"analytics"."orders"` must normalize to the same canonical name:
  `analytics.orders`.
- Empty identifier parts are invalid and must fail loudly.

### Canonical ID Forms

- table: `table:<normalized qualified name>`
- cte: `cte:<normalized name>`
- column: `column:<normalized qualified parent>.<normalized column name>`
- model: `model:<normalized qualified name>`
- report: `report:<normalized qualified name>`
- visual: `visual:<normalized report>.<normalized page>.<normalized visual>`
- page: `page:<normalized report>.<normalized page>`
- measure: `measure:<normalized table>.<normalized measure>`

If a tool cannot emit a valid canonical ID under these rules, it must fail
loudly instead of emitting a divergent ID.

## Cross-Graph Interop

Cross-graph matching lives in `clearmetric.core.interop`. Modules extract upstream
references from source files; core normalizes, applies aliases, and resolves matches.

### Warehouse join namespace (V1)

When merging warehouse lineage with BI artifacts, cross-graph `feeds` edges join:

- **source:** warehouse-side `table:` node from the lineage artifact
- **target:** BI semantic-model `table:` node from the powerbi artifact

In V1, warehouse `table:` IDs use the **dbt model namespace** (e.g. `table:orders`,
`table:stg_orders`), not physical warehouse FQNs. Physical names from M sources
are matched against that namespace via candidate expansion and optional aliases.

### Core interop helpers

- `normalize_fqn_for_matching()` — case-insensitive comparison form
- `warehouse_table_fqn_candidates()` — ordered candidates from database/schema/table parts
- `warehouse_table_fqn_candidates_from_name()` — rebuild candidates from a normalized dotted name
- `apply_alias_map()` — resolve user-supplied aliases
- `resolve_table_match()` — match source candidates to `table:` node IDs with status
- `load_table_alias_map()` — load a versioned alias file into `AliasMap`

### Match status

Every cross-graph `feeds` edge carries `match_status`:

- `resolved` — exactly one warehouse `table:` match
- `ambiguous` — multiple warehouse matches; first sorted match kept, status flagged
- `unresolved` — no match; edge retained with best-guess `source_id`, not dropped

### Alias map contract

Optional overrides for name mismatches only. Not a full mapping layer.

**Python:** `AliasMap = dict[str, str]` — keys are external reference forms (normalized
on load); values are warehouse table canonical names without the `table:` prefix.

**File format (version 1):**

```yaml
version: 1
table_aliases:
  salesmart.dbo.orders: orders
  dbo.stg_orders: stg_orders
```

Load with `load_table_alias_map(path)`. Invalid files fail with `AliasMapError`.

Parser-local alias resolution inside a module (e.g. PBIR source refs) is extraction
detail only and is not the cross-graph alias contract.

## Failure Policy

| Situation | Behavior |
|---|---|
| Invalid identifier, alias file, or merge version mismatch | Loud typed error |
| Unparseable project input (corrupt PBIP, invalid manifest) | Loud error in module |
| Ambiguous or unmatched cross-graph names | Warning + `match_status` on edge |
| Standalone module run without warehouse context | Expected unresolved joins |

Warnings represent honest uncertainty in user source files. Errors represent
broken contract inputs or unsupported states.

## V1 Non-Goals

- Fuzzy or heuristic name matching
- Module-local normalization or cross-graph matching copies
- Parser logic in `clearmetric.core.interop`
- Column-level warehouse→visual lineage through DAX
- Auth, RLS, RBAC, live connectors, or hosted orchestration in OSS modules

## Examples

- `table:analytics.orders`
- `table:orders` (dbt model name)
- `column:orders.amount`
- `visual:minimal.sales.chart1`
