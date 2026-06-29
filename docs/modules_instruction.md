# ClearMetric Core: General Instructions for Building a New Module

> Standing template. Every new module follows this. Pair it with the
> module-specific spec for the tool being built.

---

## What ClearMetric Core is

ClearMetric Core is the **public open-source** PyPI package `clearmetric-core`: headless
analytics primitives under the `clearmetric` namespace that share `clearmetric.core`
and emit one mergeable artifact format. There is one PyPI distribution — new
capabilities are added as `clearmetric.*` subpackages in the same repo, not as separate
packages to publish or version independently.

It is deliberately **not** a catalog platform. It is lightweight primitives developers compose
to build their own catalog/lineage layer. The closed hosted product (ClearMetric) is separate
and is NOT part of this OSS work.

---

## The 5 rules every module follows

### 1. Kill-test first
Before building the full module, prototype its core capability and prove it is **meaningfully
better than the obvious off-the-shelf alternative** (e.g. calling a library directly). If it is
not clearly better/easier, **STOP** and either drop the module or pick a different one.

### 2. Rebuild clean — never import proprietary
ClearMetric Core must contain ONLY general-purpose, non-proprietary logic.
- **Never in OSS:** proprietary comparison/fingerprint/verification logic, governance/policy,
  semantic-layer/definition logic, enterprise models, DB-backed context, auth/RLS/RBAC,
  connector-registry/credential code, anything tied to the ClearMetric hosted product.
- The import-boundary test must fail if any module imports enterprise/proprietary namespaces.

### 3. Extract to core only what is GENERAL and SHARED
- Extract a concept into `clearmetric.core` only when it is (a) general-purpose AND (b) genuinely
  shared with another module.
- Module-specific logic stays in the module.

### 4. Mirror the established module patterns
- **Subpackage only:** add `clearmetric.<name>` under `packages/clearmetric-core/src/clearmetric/`.
  Do not add a new PyPI package or top-level `packages/<name>/` publish target.
- Uses `clearmetric.core` **only** — never imports sibling modules at build time.
- Own tests and honest limitations doc under [`docs/reference/contract.md`](reference/contract.md) (module-specific) or adjacent package docs when not wiki-indexed.
- **Recoverable-and-warning-rich**, not hard-fail: on messy real-world input, map what you can
  and emit explicit warnings; hard-fail only on genuinely unprocessable input.
- Public artifact contract stays stable once shipped.

### 5. Stay in scope
The OSS suite is structure/lineage primitives plus the v1 compiler spine (adapters,
emitters, policy floor, cleaner, projection). Semantic execution, live warehouse connectors,
and hosted orchestration remain out of scope.

---

## Shared core contract rules (every module must respect)
- **Canonical IDs** are owned by core and must normalize identically across all modules.
- **`merge()` semantics:** same ID → union evidence; edges dedupe by (kind, source_id,
  target_id).
- **Artifact `version`** = artifact SCHEMA version, decoupled from package version.

---

## Module status (running list)
- `clearmetric.core` — shared contract, IDs, validation, merge, warehouse binding interop. Done.
- `clearmetric.compiler` — wedge orchestration spine (`build_graph`, `check_graph`, `enforce_graph`). Done (v1).
- `clearmetric.adapters` / `clearmetric.emitters` — source ingestion + output formats. Done (v1).
- `clearmetric.policy` / `clearmetric.cleaner` / `clearmetric.projection` — security floor, posture checks, catalog slice. Done (v1).
- `clearmetric.query` — single-statement SQL structure. Done.
- `clearmetric.graph` — `GraphView`, impact traversal, traversal render. Done (Phase 0).
- `clearmetric.lineage` — SQL/dbt artifact build (parse only). Done.
- `clearmetric.powerbi` — PBIP file lineage (shipped; not warehouse CLI registry). Done (V1).

## Wedge phasing

v1 is warehouse-aware lineage using INFORMATION_SCHEMA metadata exports — not the full platform. The CLI reads
`clearmetric.yaml`, ingests warehouse metadata exports + dbt/SQL, merges via
`clearmetric.compiler`, and emits honest warnings for schema drift and partial derivation.
Use `compile --format catalog` for a table/column/model-only catalog slice.

`cm clean` exits non-zero on structural errors only; warnings never fail exit regardless of posture.

Policy, cleaner, and projection are centralized OSS packages (not deferred to enterprise).
Governance rule evaluation is incremental; the security floor is enforced at compile time.
