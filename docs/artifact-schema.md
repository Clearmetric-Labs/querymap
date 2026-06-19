# QueryMap Schema

`QueryMap` is the canonical public artifact produced by `querymap`.

## Stable Shape

```text
QueryMap
  version
  summary
  relations
  relation_usages
  edges
  outputs
  warnings
```

Every successful invocation returns this shape.

## Summary Semantics

`summary` currently contains:

- `dialect`
- `statement_type`
- `has_ctes`
- `relation_count`
- `cte_count`
- `output_count`

`statement_type` reflects the original supported statement kind:

- `select`
- `insert`
- `create`

For `INSERT ... SELECT` and `CREATE ... AS SELECT`, relation mapping is still
performed from the query body.

## Populated In The MVP

The MVP populates:

- `version`
- `summary`
- `relations`
- `relation_usages`
- `edges` with `depends_on` only
- `warnings`

The MVP keeps these fields intentionally forward-compatible:

- `outputs`
- `joins` edge kind

## Design Rules

- Relations are canonical entities only.
- `query:root` is an edge endpoint, not a relation.
- Warnings are part of the contract, not an afterthought.
- The schema is stable before the implementation is feature-complete.
- Unsupported statement shapes fail loudly instead of degrading into partial
  output.
