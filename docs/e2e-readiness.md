# E2E Readiness Checkpoint

This document defines when backbone **primitives** are ready for deep e2e testing and example consumer applications. It does not expand the public product promise — see [adoption-gate.md](adoption-gate.md).

## Checkpoint criteria (0.7.1)

All must be true:

- Boundary leaks closed: impact `--identity` validates identity and gates selection loudly; `apply_policy` filters warnings and strips governance aspects; compile batches malformed contract aspects; runtime validates identity at API boundary
- Centralized surfaces enforced (see table below)
- Boundary tests green: projection, policy, impact identity, compile contracts, runtime, emitters, CLI lab hiding
- Regression green: `test_mvp_demo.py`, `test_wedge_e2e.py`, repository boundary suite
- No new public README / v1-boundary claims for lab formats

## Centralized surface contract

| Concern | Sole owner | Callers |
|---------|-----------|---------|
| Warning visibility | `core.models.filter_warnings_for_ids` | `graph.select`, `projection.apply_policy` |
| Node authz | `policy.gate` | `projection.apply_policy`, `require_allow`, `filter_allow_only_ids` |
| Execute authz (loud) | `policy.require_allow` | `runtime.execute_project_query`, `compiler.impact` (selection) |
| Allow-only ID filter | `policy.filter_allow_only_ids` | `compiler.impact` (related_ids) |
| Identity validation | `policy.require_gated_identity` | CLI experimental, `compiler.impact`, runtime, `gated_context` |
| Consumer node prep | `projection.apply_policy` | `emitters.registry` (consumer lane) |
| Governance aspect strip | `policy.models.strip_sensitive_aspects` | `projection.apply_policy` only |
| Compile dispatch | `emitters.registry.emit_compile` | CLI `_run_compile` |
| Rules load (emit) | `policy.gated_context` | `emitters.registry` only |
| Rules load (runtime/impact) | `policy.load_rules` | runtime, impact |

Pipeline shape for every consumer:

```text
select → gate → apply_policy → emit
```

## Consumer MVP Bundle (0.8.x)

Implemented under [`examples/consumers/`](https://github.com/ClearMetric-Labs/ClearMetric-Core/tree/main/examples/consumers):

- Versioned **bundle contract** (`bundle.manifest.json` + JSON schemas)
- Scenario registry + `scripts/consumers/build_bundle.py`
- Committed **minimal** admin-lane bundle (`lineage-demo` fixture) — catalog viewer default
- Committed **lineage-demo** admin-lane bundle (sql_folder fixture) — lineage explorer default; non-empty column impact trace
- Vanilla **catalog-viewer** and **lineage-explorer** (no build step, no browser policy)
- **Corpus checks** via `checks.yaml` + `tests/consumers/checks_runner.py` (Track C instrument)

Apps bind to the manifest and declared lanes — not to jaffle, GitLab, or any scenario id in code.

## Deferred: robust e2e matrix

Build when example apps exist to drive scenarios:

- Cross-format canonical ID parity (graph → consumer-catalog → frontend-contract → impact → query)
- Negative paths per surface (deny, mask, missing compiled_sql, missing seed)
- Serve HTTP contract tests beyond existing MVP demo block

Run lab tests with `CM_EXPERIMENTAL=1`. Keep wedge regression without experimental env.

## Deferred: additional consumer apps

| App | Status |
|-----|--------|
| `catalog-viewer` | **Shipped** — admin `catalog` bundle |
| `lineage-explorer` | **Shipped** — manifest impact keys, flat list v0 |
| `bi-minimal` | Deferred — query execution / runtime trust |
| `ai-host` | Deferred — lab `ai-context`, adoption gate |
| docs emitter | Deferred |

Lab consumer bundles (`consumer-catalog`, `frontend-contract`, `ai-context`) remain
`CM_EXPERIMENTAL=1` scenario recipes — not public README promise.

## Deferred: resolver corpus

Graph correctness on messy real SQL is a **parallel track**, not gated by this checkpoint. See [reference/lineage-limitations.md](reference/lineage-limitations.md).

## Stop condition

After Consumer MVP Bundle: use **prebuilt external scenarios** + `checks.yaml` for
resolver/track-C work — not more substrate rewrites unless a missing primitive is exposed.
