# Backbone Lab (Experimental / Internal)

> **Experimental / internal architecture proof / not a shipped capability / no stability guarantee.**

This document describes **Backbone Lab** flows used to prove scaffold primitives
(contracts, intent, policy gate, format registry, consumer projections, runtime harness)
work on the same graph as the wedge. These flows are **not** part of the public product
promise in [README.md](https://github.com/ClearMetric-Labs/ClearMetric-Core/blob/main/README.md) or [v1-boundary.md](v1-boundary.md).

## Public vs lab split

| Public wedge (always) | Lab (experimental only) |
|-----------------------|-------------------------|
| Lineage, impact, cleaner | Intent YAML ingest |
| Admin catalog (raw JSON) | Consumer catalog (enveloped JSON) |
| OpenLineage export (ungated) | Frontend contract, ai-context emitters |
| | `cm query`, `cm serve` (localhost debug harness) |
| | `cm impact --identity` (governance preview) |

**Adoption gate** blocks expanding README / marketing / production claims — not building
these primitives in code and tests.

## Plumbing vs resolver correctness

Lab demos that show the same canonical ID across catalog, consumer-catalog, contracts,
impact, query, and serve validate **pipeline composability** on fixtures. They do **not**
prove the resolver is correct on messy SQL. Treat resolver corpus / ugly-project validation
as a separate post-scaffold track.

## Enable lab CLI

Lab commands and compile formats require:

```bash
export CM_EXPERIMENTAL=1
```

Normal `cm --help` does not advertise lab formats. With `CM_EXPERIMENTAL=1`, help marks
them as experimental.

## Demo project

See [examples/backbone-lab/README.md](https://github.com/ClearMetric-Labs/ClearMetric-Core/blob/main/examples/backbone-lab/README.md). The example
uses shared jaffle fixtures from `packages/clearmetric-core/tests/fixtures/`.

```bash
export CM_EXPERIMENTAL=1
cd examples/backbone-lab
cm compile --format json > graph.json
cm compile --format catalog > catalog.json
cm compile --format consumer-catalog --identity analyst > consumer_catalog.json
cm compile --format frontend-contract --identity analyst > contracts.json
cm compile --format ai-context --identity analyst > ai_context.json
cm impact orders.amount --upstream
cm query --identity analyst query:executive_revenue
cm serve --identity analyst graph.json
```

Consumer JSON formats (`consumer-catalog`, `frontend-contract`, `ai-context`) wrap output
in an envelope `{format, version, identity, node_count, edge_count, payload}`. Admin wedge
formats (`json`, `catalog`, `openlineage`) remain raw.

## Architecture (lab code)

| Concern | Module / entry |
|---------|----------------|
| Graph slice | `graph.select`, `graph.select_kinds` |
| Identity + rules load | `policy.load.gated_context` (compile dispatch only), `require_gated_identity` |
| Consumer authz | `policy.gate.gate`, `require_allow` (sole node authz entry) |
| Policy projection | `projection.apply_policy` |
| Compile dispatch | `emitters.registry.emit_compile` (sole `gated_context` caller for emits) |
| Serializers | `emitters/*.serialize_*` (artifact in → dict/string out) |
| SQL compile onto graph | `compiler.compile_contracts.compile_query_contracts` |
| Query execution | `runtime.execute_project_query` (load_rules → require_allow → DuckDB) |
| Local HTTP harness | `runtime.serve.serve_project` (127.0.0.1 only; not an auth server) |

Wedge compile formats (`json`, `text`, `catalog`, `openlineage`) never require `--identity`.

## Invariants (lab code)

- `policy.gate`, `policy.require_allow`, and `policy.filter_allow_only_ids` are the authz surface (RBAC/RLS/masking decisions)
- `projection.apply_policy` is the sole consumer node preparation path (strip governance aspects, filter warnings via `core.filter_warnings_for_ids`)
- `gated_context` is only used by compile-time consumer emit dispatch in `emitters.registry`
- Runtime query execution uses `require_gated_identity` + `load_rules` + `require_allow` at the runtime boundary (not `gated_context`)
- Emitters serialize only — no policy, no aspect stripping, no projection in serializers
- Missing `compiled_sql` → loud error at runtime (no raw SQL fallback)
- Missing fixture seed → loud `QueryExecutionError`
- Policy exceptions → deny; empty rules → deny
- `cm impact --identity` requires `require_gated_identity`; gates the selection node with `require_allow` (loud deny) and filters related ids to `allow` only
- Admin `catalog` and `openlineage` remain ungated and raw JSON
- `cm serve` binds loopback only; single identity at startup is a local debug shortcut, not the production auth model
- Lab CLI and formats are hidden unless `CM_EXPERIMENTAL=1`

## Not in lab scope

Live warehouse connector, cloud, catalog UI, dashboard renderer, AI agent product, docs
emitter, native RLS deployment, custom user checks, per-request identity on serve.
