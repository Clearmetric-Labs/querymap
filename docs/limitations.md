# Limitations

`querymap` is intentionally deterministic and narrow.

## Supported Input

`querymap` accepts exactly one supported statement per invocation:

- `SELECT ...`
- `INSERT ... SELECT ...`
- `CREATE ... AS SELECT ...`

The package maps the relation structure of the query body. In the MVP, target
objects created or written by wrapper statements are not emitted as outputs.

## MVP Guarantees

The MVP guarantees:

- one supported SQL statement per invocation
- dialect-aware parsing through `sqlglot`
- canonical table and CTE relations
- relation usages with alias/context evidence
- `depends_on` edges between `query:root`, CTEs, and relations
- deterministic JSON and text output shapes
- warning-rich output when the relation structure remains mappable

The MVP does **not** yet guarantee:

- output column mapping
- output-source attribution
- first-class join edges
- Mermaid rendering
- semantic equivalence across query rewrites
- warehouse-aware expansion of `SELECT *`
- modeling wrapper targets as outputs

## Loud Failure Behavior

`querymap` fails loudly when:

- the SQL input is empty
- the SQL cannot be parsed
- more than one statement is provided
- the statement shape is unsupported
- no relations can be extracted from the statement

## Warning-Based Behavior

`querymap` warns instead of failing when the relation structure is still clear
enough to model honestly.

Current warning cases include:

- `UNION`, `INTERSECT`, and `EXCEPT` are mapped at the relation level only
- `SELECT *` and `table.*` are detected, but output mapping remains deferred
- recursive CTE references are not modeled explicitly
- non-equality joins preserve relation dependencies but not join semantics
- joins without `ON` or `USING` are not modeled beyond dependency extraction

## What Stays Out Of This Package

This package must not contain:

- enterprise adapters
- auth, RBAC, or RLS behavior
- proprietary comparison logic
- workspace-aware or database-backed enrichment
- route handlers or API wiring
- private fixtures or tests that reveal internal business logic
