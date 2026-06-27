# ClearMetric Core

**Build a data catalog from your code, not a platform.** ClearMetric Core is an open-source compiler and graph engine that derives lineage, structure, and a mergeable catalog graph from the dbt projects and SQL you already have — locally, no warehouse, no platform to stand up.

```bash
pip install clearmetric-core
cm impact orders.credit_card_amount ./manifest.json --dialect postgres --upstream
```

```
upstream: orders.credit_card_amount
selection_id: column:orders.credit_card_amount
tree:
  - column:orders.credit_card_amount
    - column:stg_payments.amount
      - column:raw_payments.amount
```

Ask any column *"what feeds this?"* or *"what breaks if I change it?"* and get a real answer, traced from your code.

> **Status:** early development (0.x), release 0.2.0. Pin your versions.

## Why it's different

Most catalogs are heavy platforms you log into and maintain by hand — and they drift out of sync with the code. ClearMetric Core is the opposite: a single package that derives the catalog *from* the code, so it stays fresh, lives in your repo, and runs in CI. When it can't resolve something, it flags it instead of guessing.

## Quickstart

```bash
pip install clearmetric-core
cm compile ./manifest.json --dialect postgres
cm impact orders.amount ./manifest.json --dialect postgres --upstream
```

If another program already occupies `cm` on your PATH, use the module entry instead:

```bash
python -m clearmetric.cli impact orders.amount ./manifest.json --dialect postgres --upstream
```

## Compile a catalog

Every module emits the same mergeable artifact, so independent outputs combine into one catalog graph — assets, columns, lineage — that you can serialize or hand to other tools via OpenLineage.

```python
from clearmetric.lineage import build_catalog_artifact, build_openlineage_export

catalog = build_catalog_artifact("./manifest.json", dialect="postgres")
open_lineage = build_openlineage_export(catalog)  # standard format others can ingest
```

## Modules

One install (`pip install clearmetric-core`) gives you every module below. These are
Python subpackages, not separate PyPI packages.

| Module | What it does | Status |
|--------|--------------|--------|
| **`clearmetric.lineage`** | Column-level lineage, impact, catalog graph, OpenLineage export | Shipped |
| **`clearmetric.query`** | Maps a single SQL statement into its tables and dependencies | Shipped |
| **`clearmetric.powerbi`** | PBIP lineage: M sources, report visuals, warehouse merge | V1 |
| **`clearmetric.core`** | Shared artifact, canonical IDs, merge, cross-graph interop | Shipped |

## Roadmap

Growing toward a catalog that lives in your repo and is enforced in CI — all derived from your code, no new format to adopt:

- `cm init` — scaffold a ClearMetric project
- `cm scan` — discover analyzable inputs in a repo
- `cm clean` — remove stale generated artifacts
- `cm contract` — validate artifact contract in CI
- CI gate: fail a PR when a change breaks something downstream
- Duplicate and near-duplicate model detection
- Catalog site generation from your repo

[Open an issue](https://github.com/ClearMetric-Labs/ClearMetric-Core/issues) if there's a primitive you wish existed.

## Limits

Static analysis only — no warehouse connection. On star-heavy SQL (`SELECT *` without schema), it flags what it can't resolve rather than guessing. Correct where it can be, explicit where it can't. [Full limitations →](packages/clearmetric-core/docs/lineage/limitations.md)

## Feedback & contact

Built in the open, and feedback shapes the roadmap.

- **Bugs / features:** [open an issue](https://github.com/ClearMetric-Labs/ClearMetric-Core/issues)
- **Questions / ideas:** [Discussions](https://github.com/ClearMetric-Labs/ClearMetric-Core/discussions)
- **Using it or want to talk?** Reach out on [LinkedIn](https://www.linkedin.com/in/kim-jon).

## License

Apache 2.0.

---

<details>
<summary><strong>Architecture & contributing</strong></summary>

ClearMetric Core is a single Python package at `packages/clearmetric-core` with submodules under the `clearmetric` namespace. Each module composes through `clearmetric.core` and emits artifacts that merge into one graph.

**Modules**
- `clearmetric.core` — shared artifact models, canonical IDs, serialization, merge, validation
- `clearmetric.query` — single-statement SQL structure mapping
- `clearmetric.lineage` — project-level lineage, catalog artifact, and OpenLineage export for dbt manifests and SQL folders
- `clearmetric.powerbi` — PBIP file lineage: M upstream sources, report visual bindings, cross-graph merge metadata
- `clearmetric.cli` — `cm` command router

```python
from clearmetric.core import Node, Edge, Evidence
from clearmetric.query import build_query_map
from clearmetric.lineage import build_lineage_map
```

**Core rules**
- `version` = shared artifact *schema* version, owned by `clearmetric.core`.
- Canonical IDs and merge semantics defined once in `clearmetric.core`.
- No duplicate shared models or fallback code paths.

**Local development**
```bash
python -m pip install -e "packages/clearmetric-core[dev,release]"
python -m pytest -v
```

**Docs:** [contract](packages/clearmetric-core/docs/contract.md) · [query limits](packages/clearmetric-core/docs/limitations/query/limitations.md) · [lineage limits](packages/clearmetric-core/docs/lineage/limitations.md) · [powerbi limits](packages/clearmetric-core/docs/limitations/powerbi/limitations.md) · [architecture](clearmetric-architecture.md) · [orchestration](docs/orchestration.md)

Contributions require agreeing to the [CLA](CLA.md). See [CONTRIBUTING.md](CONTRIBUTING.md).

</details>
