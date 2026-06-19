# querymap

`querymap` maps one supported SQL statement into deterministic relation
dependencies so you can answer "what feeds what in this query?" fast.

It is a narrow static-analysis tool:

- input: exactly one SQL statement from one SQL file
- output: canonical relations, relation usages, dependency edges, and warnings
- no warehouse credentials
- no dbt project
- no AI key

`querymap` is not related to [`sqlmap`](https://sqlmap.org/), the SQL injection
tool.

## What It Does

`querymap` extracts the relation structure of a query and returns a stable
`QueryMap` artifact with:

- `summary`
- `relations`
- `relation_usages`
- `edges`
- `outputs`
- `warnings`

The current MVP populates:

- `summary`
- `relations`
- `relation_usages`
- `edges` with `depends_on`
- `warnings`

The `outputs` field is intentionally present but currently returns `[]` until
output mapping is robust enough to ship honestly.

## What It Does Not Do

`querymap` does **not** try to be a full lineage engine. It does not yet model:

- output column lineage
- output-source attribution
- first-class join edges
- warehouse-aware `SELECT *` expansion
- Mermaid rendering

## Supported Statements

`querymap` accepts exactly one supported statement per invocation:

- `SELECT ...`
- `INSERT ... SELECT ...`
- `CREATE ... AS SELECT ...`

Wrapper statements are mapped through their query body. In the MVP, the source
relations and dependency structure are modeled; target tables or views are not
yet emitted as outputs.

Unsupported statement shapes fail loudly.

## Install

Install from source:

```bash
python -m pip install .
```

Once the first PyPI release is published:

```bash
python -m pip install querymap
```

For development and release validation:

```bash
python -m pip install -e ".[dev,release]"
```

## Quickstart

Run the bundled example:

```bash
querymap --dialect postgres ./examples/ugly_real_world.sql
```

The module entrypoint works too:

```bash
python -m querymap --dialect postgres ./examples/ugly_real_world.sql
```

JSON output:

```bash
querymap --dialect postgres --format json ./examples/ugly_real_world.sql
```

Example text output:

```text
querymap
dialect: postgres
statement_type: select
has_ctes: True

relations:
  - [cte] base_orders
  - [cte] customer_rollup
  - [cte] ranked_customers
  - [table] analytics.customers
  - [table] analytics.orders

relation_usages:
  - cte_body: table:analytics.orders alias=o :: analytics.orders AS o
  - cte_body: cte:base_orders alias=bo :: base_orders AS bo
  - cte_body: table:analytics.customers alias=c :: analytics.customers AS c
  - join: cte:customer_rollup alias=cr :: customer_rollup AS cr
  - from: cte:ranked_customers :: ranked_customers

dependencies:
  - cte:base_orders -> table:analytics.orders
  - cte:customer_rollup -> cte:base_orders
  - cte:ranked_customers -> table:analytics.customers
  - cte:ranked_customers -> cte:customer_rollup
  - query:root -> cte:ranked_customers

warnings:
  - select_star: SELECT * was detected; output mapping is deferred in the MVP. [*]
```

Example JSON output:

```json
{
  "version": "1",
  "summary": {
    "dialect": "postgres",
    "statement_type": "select",
    "has_ctes": true,
    "relation_count": 5,
    "cte_count": 3,
    "output_count": 0
  },
  "relations": [
    {
      "id": "cte:base_orders",
      "kind": "cte",
      "name": "base_orders",
      "qualified_name": null,
      "schema": null
    }
  ],
  "relation_usages": [
    {
      "relation_id": "table:analytics.orders",
      "alias": "o",
      "context": "cte_body",
      "sql": "analytics.orders AS o",
      "normalized_sql": "analytics.orders AS o"
    }
  ],
  "edges": [
    {
      "kind": "depends_on",
      "source_id": "cte:base_orders",
      "target_id": "table:analytics.orders",
      "label": "depends_on",
      "confidence": "high",
      "sql": "analytics.orders AS o",
      "normalized_sql": "analytics.orders AS o"
    }
  ],
  "outputs": [],
  "warnings": [
    {
      "code": "select_star",
      "message": "SELECT * was detected; output mapping is deferred in the MVP.",
      "location": "*"
    }
  ]
}
```

## Loud Failure Behavior

`querymap` fails with a non-zero exit code when:

- the SQL is empty
- the SQL cannot be parsed for the chosen dialect
- more than one statement is provided
- the statement is not one of the supported query shapes
- no relations can be extracted from the statement

Some constructs are warning-based rather than fatal. See
[`docs/limitations.md`](docs/limitations.md) for the full warning model.

## Python API

```python
from querymap import build_query_map, render_json

sql = """
WITH active_customers AS (
    SELECT id
    FROM public.customers
    WHERE is_active = true
)
SELECT *
FROM active_customers
"""

query_map = build_query_map(sql, dialect="postgres")
payload = render_json(query_map)
print(payload["summary"])
```

## Contract Docs

- [`docs/artifact-schema.md`](docs/artifact-schema.md)
- [`docs/limitations.md`](docs/limitations.md)
- [`docs/release_checklist.md`](docs/release_checklist.md)

## Development

Run tests:

```bash
pytest -v
```

Build the package locally:

```bash
python -m build
twine check dist/*
```

## Scope

`querymap` is the public OSS artifact only. It must not include:

- enterprise adapters
- proprietary comparison or governance logic
- route handlers or API wiring
- auth, RLS, or RBAC logic

## License

`querymap` is licensed under Apache 2.0. See [`LICENSE`](LICENSE).

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md).
