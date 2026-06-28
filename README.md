# ClearMetric Core

**Column-level lineage and impact analysis from your existing SQL/dbt — free, local, one command.**

Point ClearMetric at your warehouse metadata export and/or dbt project. It compiles lineage and structure into **one canonical graph** with physical bindings, derivation state, and honest warnings when something cannot be resolved.

The sharp question the wedge answers: *what breaks if I rename this column?*

```bash
pip install clearmetric-core
cd my-dbt-project
cm init
cm connect warehouse --information-schema ./warehouse_schema.json
cm scan
cm compile --format json > graph.json
cm compile --format catalog > catalog.json
cm impact column.fct_orders.net_revenue --upstream
cm clean
cm contract graph.json
```

Warehouse metadata is a **local INFORMATION_SCHEMA JSON export** — not a live connector.

If `cm` is occupied on your PATH: `python -m clearmetric.cli --project-dir . …`

> **Status:** early development (0.x). Pin your versions. Full architecture: [`clearmetric-architecture.md`](clearmetric-architecture.md)

## What you get today (v1 wedge)

- **Lineage + impact** — upstream/downstream column traversal from dbt manifests, SQL folders, and warehouse metadata
- **One graph** — warehouse metadata, dbt, and SQL merged via adapters; physical bindings attached on lineage nodes
- **Honest derivation** — partial or unresolved lineage is stamped with confidence and surfaced as findings, not guessed
- **Catalog slice** — `compile --format catalog` emits table/column/model nodes only
- **Cleaner + security floor** — structural checks, schema drift warnings, and a non-bypassable security floor at compile time

**Deferred** (foundation accretes around the wedge): live query endpoint, metrics/query YAML, `serve`, user-defined checks, live warehouse connectors, full policy compiler. See [`docs/v1-boundary.md`](docs/v1-boundary.md).

## Why it's different

Most catalogs are platforms you log into and maintain by hand — and they drift out of sync with the code. ClearMetric Core is the opposite: a compiler that derives structure *from* your code and metadata exports, keeps the graph in your repo, and runs in CI. When it cannot resolve something, it flags it instead of guessing.

Four design phrases (full detail in [`clearmetric-architecture.md`](clearmetric-architecture.md)):

- **Open-source core, paid managed history.**
- **Logical IDs with physical bindings.**
- **Contracts, not dashboards.**
- **Derived metadata with confidence, not magic.**

## Quickstart

See [`examples/wedge-jaffle/README.md`](examples/wedge-jaffle/README.md) for a walkthrough with committed fixtures.

```bash
pip install clearmetric-core
cm init
cm connect warehouse --information-schema ./warehouse_schema.json
cm scan
cm compile --format json > graph.json
cm impact orders.amount --upstream
cm clean
cm contract graph.json
```

Column selections accept `orders.amount`, `column:orders.amount`, or `column.fct_orders.net_revenue` (normalized via `clearmetric.core.ids.parse_column_selection`).

## Compile the graph

Adapters normalize sources in; the core merges and binds; validation runs through the cleaner and security floor; emitters shape output.

```python
from pathlib import Path
from clearmetric.compiler import build_graph, check_graph, compile

compiled = compile(Path("./my-project"))          # build + enforce
built = build_graph(Path("./my-project"))           # ingest + merge + bind only
report = check_graph(built.artifact, posture=built.project.posture)  # report-only (same path as cm clean)
```

## Modules

One install (`pip install clearmetric-core`) — Python subpackages, not separate PyPI packages.

| Module | Role | Wedge |
|--------|------|-------|
| **`clearmetric.lineage`** | Column-level lineage from dbt + SQL (**Module B — the wedge**) | Shipped |
| **`clearmetric.compiler`** | `build_graph`, `check_graph`, `enforce_graph`, CLI orchestration | Shipped |
| **`clearmetric.adapters`** | INFORMATION_SCHEMA JSON, dbt manifest, SQL folders | Shipped |
| **`clearmetric.core`** | Artifact, canonical IDs, merge, bindings interop | Shipped |
| **`clearmetric.cleaner`** | Posture-aware checks | Shipped |
| **`clearmetric.policy`** | Security floor (+ evaluation shell) | Shipped (floor) |
| **`clearmetric.projection`** / **`clearmetric.emitters`** | Catalog slice + output formats | Shipped |
| **`clearmetric.query`** | Single-statement SQL structure (**Module A — accretes later**) | Library only |
| **`clearmetric.powerbi`** | PBIP lineage | Shipped (not in CLI registry) |

## CLI

| Command | Purpose |
|---------|---------|
| `cm init` | Scaffold `clearmetric.yaml` + `policy/rules.yaml` |
| `cm connect warehouse --information-schema PATH` | Attach local metadata export |
| `cm scan` | List configured sources (warehouse, dbt, sql, optional aliases) |
| `cm compile --format json\|text\|openlineage\|catalog` | Build + enforce graph to stdout |
| `cm impact SELECTION --upstream\|--downstream` | Column lineage (enforced graph) |
| `cm clean` | Report findings; exit 1 on **errors only** |
| `cm contract ARTIFACT.json` | Schema validate + strict enforce (CI) |

## Limits

Static analysis for SQL/dbt lineage; warehouse **metadata exports** only in v1 (no query execution). On star-heavy SQL (`SELECT *` without schema), ClearMetric flags what it cannot resolve. [Lineage limitations →](packages/clearmetric-core/docs/lineage/limitations.md)

## Feedback

- **Bugs / features:** [Issues](https://github.com/ClearMetric-Labs/ClearMetric-Core/issues)
- **Questions:** [Discussions](https://github.com/ClearMetric-Labs/ClearMetric-Core/discussions)

## License

Apache 2.0.

---

<details>
<summary><strong>Architecture & contributing</strong></summary>

ClearMetric Core is one package at `packages/clearmetric-core`. Modules compose through `clearmetric.core` and emit mergeable artifacts. The architecture doc describes the full foundation; **the shipped product is the wedge** — lineage and impact first, everything else accretes.

**Docs:** [architecture](clearmetric-architecture.md) · [v1 boundary](docs/v1-boundary.md) · [contract](packages/clearmetric-core/docs/contract.md) · [orchestration](docs/orchestration.md) · [contributing](CONTRIBUTING.md)

**Local development**

```bash
python -m pip install -e "packages/clearmetric-core[dev,release]"
python -m pytest -v packages/clearmetric-core/tests tests/
```

Contributions require the [CLA](CLA.md).

</details>
