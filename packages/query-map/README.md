# query-map

`query-map` maps one supported SQL statement into a deterministic `QueryMap`
artifact so you can answer "what feeds what in this query?" fast.

It is a narrow static-analysis tool:

- input: exactly one SQL statement from one SQL file
- output: canonical relations, relation usages, dependency edges, and warnings
- no warehouse credentials
- no dbt project
- no AI key

## Install

```bash
python -m pip install query-map
```

For local development:

```bash
python -m pip install -e ../catalog-core
python -m pip install -e ".[dev,release]"
```

## Quickstart

```bash
query-map --dialect postgres ./examples/ugly_real_world.sql
query-map --dialect postgres --format json ./examples/ugly_real_world.sql
```

## Output Contract

`query-map` preserves its public `QueryMap` shape:

- `summary`
- `relations`
- `relation_usages`
- `edges`
- `outputs`
- `warnings`

For CatalogKit composition, the package also exposes a shared
`CatalogArtifact` builder backed by `catalog-core`.

The shared core artifact contains:

- `version`
- `nodes`
- `edges`
- `warnings`

## Supported Statements

`query-map` accepts exactly one supported statement per invocation:

- `SELECT ...`
- `INSERT ... SELECT ...`
- `CREATE ... AS SELECT ...`

Unsupported statement shapes fail loudly.

## Contract Docs

- [`../catalog-core/docs/contract.md`](../catalog-core/docs/contract.md)
- [`docs/limitations.md`](docs/limitations.md)
