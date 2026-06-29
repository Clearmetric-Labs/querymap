# Adoption gate

The adoption gate blocks **public product claims and production positioning**. It does
**not** block internal, tested, backbone-tied primitives built in the core (see
[backbone-lab.md](backbone-lab.md)).

## Status

**Gate: NOT PASSED**

## What the gate blocks (public only)

Until external evidence exists, do **not**:

- Expand [README.md](https://github.com/ClearMetric-Labs/ClearMetric-Core/blob/main/README.md) shipped capabilities beyond the wedge promise
- Expand [v1-boundary.md](v1-boundary.md) in-scope tables with metrics/runtime/governance
- Market production governance, cloud, live warehouse connectors, or native RLS deployment
- Present lab primitives as shipped product (README / v1-boundary / marketing)

## What the gate does not block

- Building backbone lab primitives in code (contracts, intent, gate, consumer catalog,
  frontend contract, runtime harness)
- Pipeline wiring and end-to-end tests (`CM_EXPERIMENTAL=1`)
- `examples/backbone-lab/` and [backbone-lab.md](backbone-lab.md)
- Backbone lab QA finish line in `0.6.1` (gated path, atomic compile contracts, runtime
  harness, boundary tests — still experimental, not README promise)

## Requirements (public unlock)

Pass **all** of:

- [x] Wedge v1 checklist green in CI
- [ ] Wedge used by at least one **real user who is not the implementer**
- [ ] **External pull on record** below with named asker, verbatim quote, and link

## External pull record

| Field | Value |
|-------|-------|
| **Asker** | _TBD — person, team, or paying org_ |
| **Verbatim quote** | _TBD — what they asked for (metrics? gated export? runtime?)_ |
| **Link** | _TBD — GitHub issue, email thread, or customer ticket_ |
| **Date recorded** | _TBD_ |

## What fails the gate

- "The plan looks good"
- "Internal decision"
- "We'll need this eventually"
- Momentum without a named external asker

## Public wedge promise (frozen until gate passes)

> ClearMetric Core compiles dbt, SQL, and warehouse metadata exports into one graph for
> lineage, impact analysis, schema drift findings, and catalog output.
