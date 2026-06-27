# ClearMetric — Core Architecture

## What it does (in one breath)

You point ClearMetric at your **warehouse and/or dbt project**. It compiles your entire
analytics layer — metrics, queries, lineage, metadata, and access rules — into **one
canonical graph**. Then your BI dashboards, your catalog, your lineage explorer, your AI
agent's context, and your security policy are all **generated from that one graph**,
instead of being defined separately in five different tools where they silently drift
apart.

Concretely, a developer runs it and gets:

- **one source of truth** for what every metric means and where every column comes from,
  derived from their SQL — not re-typed by hand;
- **live, governed query primitives** their own frontend (React, Streamlit, Evidence, an
  internal app, an AI agent) binds to, so they control the presentation and ClearMetric
  controls the correctness;
- **a built-in cleaner** that catches duplicate metrics, dead dashboards, ungoverned
  sensitive data, and broken lineage before they ship — and that they can extend with
  their own checks;
- **one place to define access** (who and which AI agent may see what) that compiles down
  to real warehouse policies.

The problem it removes: today, "what revenue means," "where it comes from," "who can see
it," and "what the dashboard shows" live in four different systems that drift. ClearMetric
makes them four views of **one graph that cannot disagree with itself.**

## What it is (precisely)

A code-first analytics control plane that compiles code-defined metrics, queries,
lineage, metadata, and policy intent into one canonical graph of queryable nodes and
bindable contracts that BI frontends, catalogs, and AI agents safely build on.

It is **not** a transformation tool (leverage dbt / existing OSS). It is **not** a renderer
(it supplies the contract, query, and result; the frontend renders). It owns the layer
between the model and the consumer.

Four phrases carry the architecture:

- **Open formats, free engine, paid history.**
- **Logical IDs with physical bindings.**
- **Contracts, not dashboards.**
- **Derived metadata with confidence, not magic.**

---

## The central design tension this document resolves

Two requirements that sound opposed:

- **Opinionated** — force best practice, no redundancy, no duplicates, no ungoverned
  sprawl, so an inexperienced user cannot unknowingly wreck their infra.
- **Flexible** — users define their own permissions, metrics, checks, node and projection
  types; the tool dictates almost no content.

The resolution is a single principle that runs through the whole architecture:

> **The system is rigid about STRUCTURE and lenient about CONTENT.**
> It enforces *how things must be shaped and related* (identity, provenance,
> completeness, non-duplication) and stays out of *what things mean and who may see
> them* (metric logic, classifications, policy rules, personas, custom checks).

Opinionation lives in the **shape and integrity of the graph**. Flexibility lives in the
**content the user pours into that shape** — including the checks they run against it.
They do not conflict because they operate on different layers: you cannot violate the
structure, but within the structure you define everything.

---

## The security floor — extensible, but never into a hole

The "rigid structure / flexible content" principle has a dangerous gap if left alone:
**security is content**, so unrestricted flexibility would let a user — especially an
inexperienced one — extend the system straight into an insecure state. They could expose
PII to an AI agent, wipe the deny-by-default seed, disable a security check, or carry
sensitive data in an unclassified aspect. That is exactly the "unknowingly wreck their
infra" failure this product exists to prevent.

So security is **not** ordinary content. A small set of **security invariants lives in the
structural tier** — the same impossible-to-violate floor as canonical identity. Posture
cannot lower them. User checks cannot disable them. Wiping the policy seeds cannot remove
them. Everything *above* the floor stays fully extensible; the floor itself is
non-negotiable underneath.

### The security floor (structural — always on, every posture)

```
1. NO UNCLASSIFIED EXPOSURE
   A node reachable by an AI-permission or export rule MUST carry a classification.
   Unclassified data cannot be exposed. (You may classify it "public" — explicitly —
   but you cannot leave it blank and expose it.)

2. NO PII WITHOUT A GOVERNING POLICY
   A node classified PII/confidential MUST have a policy reference before any projection,
   AI pack, or export can include it. Sensitive + ungoverned = compile fails, every
   posture.

3. POLICY CANNOT FAIL OPEN
   If policy evaluation errors, is missing, or is undetermined for a node, the decision
   is DENY. Never allow-on-error. (Mirrors the false-negative discipline: an undetermined
   check fails closed, not open.)

4. SECURITY CHECKS CANNOT BE DISABLED, ONLY OVERRIDDEN-WITH-RECORD
   Built-in checks tagged `security` cannot be set to `off`. They can be explicitly
   overridden for a specific node only with a recorded, owned, expiring justification
   (an authored override node) — never silently switched off.

5. DENY-BY-DEFAULT IS THE FLOOR, NOT A SEED
   The seed RULES are wipeable; the deny-by-default POSTURE is not. With zero rules, a
   node is invisible, not public. Users open access explicitly; they cannot accidentally
   leave it open.

6. USER EXTENSIONS INHERIT THE FLOOR
   A user-defined aspect that holds data is subject to classification rules. A
   user-defined projection still routes through policy. A user-defined check runs in the
   sandbox and cannot grant access. Extensibility never escapes the floor — new kinds
   enter the system already governed.
```

### Why this keeps extensibility total *above* the floor

The floor constrains exactly six things, all of them about *not leaking data*. It does
not touch what metrics mean, who your roles are, what checks you write, what aspects you
invent, or how you present anything. A user can extend the system in every direction the
four axes allow — and every extension lands **already governed**, because the floor is
structural and new kinds inherit it. You get "define whatever you want" and "cannot open a
hole" at the same time, because the hole-opening moves are the only moves removed.

The distinction in one line: **posture is a dial on opinion; the security floor is a dial
that does not exist.** You can tell ClearMetric to stop nagging about style. You cannot tell
it to expose ungoverned PII, because that capability was never built.

---

## The five layers

```
SOURCES
  warehouse INFORMATION_SCHEMA · dbt manifest · raw SQL ·
  query logs · authored intent (YAML)
                │
1. COMPILER  (opinionated · strict · teaching)
  ingest → resolve LOGICAL identity (+ physical bindings) → build graph →
  derive (with state) → run CLEANER (built-in + user checks) →
  validate by rule-tier → emit outputs
                │
2. GRAPH  (truth — stores ownership refs, makes no authz decisions)
  typed nodes + typed edges + contracts ·
  logical canonical IDs + physical bindings · small core + appendable aspects ·
  provenance + derivation state on every fact
                │
3. POLICY  (intent — one engine, user-authored rules, three enforcement modes)
  (identity, node) → allow | deny | mask | filter
                │
4. PROJECTION  (lenses — computed per identity)
  view = contract/query over graph + persona lens, filtered by (3)
                │
5. CONSUMERS  (you do not own these)
  BI frontend · AI agent context · catalog · lineage explorer ·
  compiled policy artifacts (Snowflake / BigQuery / Postgres RLS · OPA bundle)
```

One sentence: the compiler turns sources into one canonical graph of typed nodes and
**contracts**, runs the **cleaner** over it, and every consumer reaches it only through
the projection layer, which serves the graph filtered by the policy layer for the asking
identity.

---

## Layer 2 — The graph (where structure is rigid)

### Identity: logical node, physical bindings

"One canonical ID per real thing" is correct as a goal but becomes a philosophical
argument unless you separate the *logical* concept from its *physical* locations. The
stable node is **logical**. Where it lives is a list of **bindings**.

```yaml
id: column.fct_orders.net_revenue
kind: column
identity_scope: physical | logical | semantic | runtime
bindings:
  - warehouse: snowflake
    database: analytics_prod
    schema: marts
    table: fct_orders
    column: net_revenue
  - warehouse: snowflake
    database: analytics_dev
    schema: marts_dev
    table: fct_orders
    column: net_revenue
```

Policy, lineage, BI, and AI all attach to the stable **logical** node; the bindings tell
the system *where it physically lives* (dev vs prod, dbt-model vs warehouse-table). This
is what makes canonical identity implementable rather than aspirational, and it is the
single hardest technical piece — the identity resolver is built and stress-tested first,
before any module leans on it.

### Node base (stable, small)

```yaml
id: metric.finance.net_revenue        # canonical logical ID — required, unique
type: metric
name: Net Revenue
domain: finance
provenance: authored | derived        # which half produced this
lifecycle: draft | certified | deprecated
owner: team.finance_analytics         # a reference, NOT an authz decision
source_path: metrics/revenue.yml
```

The graph **stores ownership and identity references** (`owner: team.finance_analytics`)
but **makes no authorization decisions**. The graph may know who owns a thing; it never
decides who may *see* it. That decision belongs to policy (layer 3).

### Aspects (where content is flexible)

Independently attachable typed metadata; adding `usage` does not touch
`metric_definition`. Users may define new aspect types — the core only requires that an
aspect attach to a node by canonical ID. **Flexibility axis #1.**

```
metric_definition · lineage · usage · ai_behavior ·
quality · glossary · runtime_binding · <user-defined>
```

### Contracts (the primitive that makes the graph buildable)

A node *describes*. A contract makes it *bindable / executable*. This is the difference
between a metadata graph and infrastructure. A frontend, an AI agent, and a test bind to
the **contract**, never the raw node. **Contracts, not dashboards.**

```yaml
id: query.executive.revenue_by_month
type: query
inputs:
  parameters:
    start_date: date
    end_date: date
outputs:
  columns:
    month: date
    net_revenue: number
depends_on:
  - metric.finance.net_revenue
policy:
  required_projection: aggregate_only
runtime:
  compiled_sql: generated
```

### Derivation state (honesty — "with confidence, not magic")

Derived facts can be missing, partial, ambiguous, or wrong. sqlglot degrades on dynamic
SQL, macros, temp tables, UDFs, ambiguous aliases, cross-database refs. The graph records
the gap instead of pretending. Every derived fact carries:

```yaml
derivation:
  status: complete | partial | failed | skipped
  confidence: high | medium | low
  source: sqlglot | dbt_manifest | information_schema | query_logs
  errors: []
```

A known gap is safe; a silent wrong answer is fatal. The compiler requires authored
intent only where human judgment is needed; derived metadata is computed when possible,
stamped, and when derivation fails the gap is recorded — not hidden.

---

## The derived / authored line (lightweight governance)

| Derived (computed, stamped, never hand-typed) | Authored (intent — no artifact holds it) |
|---|---|
| column lineage + value-semantics (sqlglot) | metric meaning + canonical name |
| dependencies, data types, structure | ownership |
| grain (where inferable) | classification (PII / confidential) |
| usage / dead-asset detection | access policy |
| duplicate-formula detection (AST) | AI permissions |
| freshness | lifecycle decisions |
| impact analysis | glossary / synonyms |

---

## Layer: the Cleaner (built-in checks + user-defined checks — ONE mechanism)

The cleaner is **not a separate tool and not a new axis.** A check is just a function
that reads the graph and emits findings. Built-in checks and user checks run through the
**same check engine** in the compiler, declare the **same rule-tiers**, and read the
**same graph by canonical ID**. That is what keeps it one architecture: a duplicate check
and a user's custom test are the *same kind of thing* — `(graph) -> findings`.

### The check contract (what every check is)

```yaml
id: check.no_orphan_metrics
kind: check
scope: node | edge | graph          # what it traverses
selector: type == "metric"          # which nodes it applies to
tier: structural | error | warn | off
message: "metric {id} has no certified lineage to a source column"
fix_hint: "add depends_on or run `clearmetric lineage --repair {id}`"
provenance: builtin | user
```

A check returns findings:

```yaml
finding:
  check: check.no_orphan_metrics
  node: metric.sales.pipeline_value
  severity: error
  message: "..."
  fix_hint: "..."
```

### Built-in checks (ship by default)

```
identity:        no two logical nodes share a binding (structural)
                 every edge resolves to existing nodes (structural)
completeness:    every asset has an owner / classification / policy ref (error*)
non-duplication: duplicate-formula (warn by default — see below)
hygiene:         dead assets (unused / unviewed), orphan nodes,
                 undocumented columns, deprecated-metric still referenced
freshness:       stale derivations, low-confidence facts surfaced
```

`*` at strict posture; relaxes by posture (see Opinionation).

### User-defined checks (the extensibility you asked for)

Users write their own checks the same way built-ins are written — as a check node with a
selector and a tier, or as code against the graph query API. They run in the same pass,
emit the same findings, honor the same posture. Examples a team might add:

```yaml
- id: check.revenue_metrics_must_have_currency
  selector: type == "metric" and domain == "finance"
  tier: error
  message: "finance metric {id} missing currency aspect"

- id: check.no_pii_in_ai_context
  selector: aspect.ai_behavior.allowed == true
  tier: error
  message: "{id} exposed to AI but has PII classification"
```

Because user checks are nodes on the graph, they are themselves versioned, owned,
testable, and visible — not hidden scripts. **Flexibility axis #4: users define their own
cleaning, duplication, and test logic without leaving the architecture.**

**User checks inherit the security floor (they cannot open a hole):** a user check runs in
a read-only sandbox over the graph. It can *report* findings at any tier, but it cannot
grant access, mutate the graph, or set a `security`-tagged built-in check to `off` (floor
item 4). Users can make the cleaner *stricter* freely; they can only make it *less strict*
on non-security checks, and only with a recorded override. So the worst an inexperienced
user can do with a custom check is add noise — never remove a guardrail.

### Why the cleaner is not a fourth pipeline

It reads the graph (layer 2) and reports through the rule-tier system (the compiler's
existing enforcement). It writes nothing new and decides no access. So it is the compiler
*using* the graph, not a parallel system. One architecture holds.

---

## Non-duplication: warn by default, fail-closed only on real collision

Two formulas can be byte-identical and *mean* different things (domain, grain, currency,
audience, timing, inclusion rules). Hard-failing on AST match alone makes experienced
teams fight the tool. So duplicate detection is **warn by default**, and only escalates
to fail-closed when the project opts in OR when collision is unambiguous:

```
strict fail-closed ONLY when:
  same expression  AND  same grain  AND  same filters
  AND (same domain OR overlapping certified lifecycle)
otherwise: warn with a choice.
```

The teaching finding:

```
Possible duplicate detected:
  metric.sales.revenue and metric.finance.net_revenue — 94% formula similarity.
Choose:
  1. reuse existing metric
  2. create alias
  3. mark intentionally separate (with reason)
```

"No duplicates" stays a guarantee of *identity* (structural, impossible to violate) and a
*guided* property of *meaning* (warn, user decides) — never a blunt fail on content.

---

## Layer 3 — Policy (flexible content, one engine, honest enforcement)

You ship the **vocabulary** (policy kinds) and the **evaluation engine** plus safe seed
defaults. The org authors the **rules** and can wipe every seed; the engine still works.
You never ship verdicts. Policy-as-data:
`decision = f(identity_attributes, node_attributes, org_rules)`.

Wiping the seeds removes the example **rules**, not the **floor**: with zero rules a node
is invisible (deny-by-default, security-floor item 5), never public. And policy
evaluation that errors or is undetermined returns DENY (floor item 3), never allow. Users
open access explicitly; they cannot wipe their way into an open default.

Policy kinds: `RBAC` · `RLS` · `masking` · `AI-permission` · `export`. Fixed kinds,
user-authored rules. **Flexibility axis #2 — users define every permission.**

### Three enforcement modes (never claim universal enforcement)

```
Native enforcement   compiled INTO the target — Snowflake / BigQuery row policies,
                     Postgres RLS, OPA bundle. Actually enforced at the data.
Runtime enforcement  the ClearMetric query / projection / AI-context API.
                     Enforced IF the consumer uses your runtime.
Advisory             docs, catalog annotations, generated-but-unapplied configs.
                     NOT enforced.
```

Honest claim: **all ClearMetric-native authorization is layer 3; external authorization is
enforced only when compiled into the target or routed through the runtime.** A consumer
that exports the graph into Power BI or a custom frontend bypasses runtime policy unless
policy was compiled native into the warehouse. Stated plainly — in a governance tool,
claiming enforcement you do not have is a liability.

---

## Layer 4 — Projection (personas are filters, not forks)

A view = a contract/query over the graph + a persona lens, evaluated through the policy
filter for the asking identity. Same graph, different lens.

- "Full catalog" = projection selecting all kinds, admin identity.
- "Full lineage" = projection traversing lineage edges, no depth limit.
- "Custom AI context" = scope (projection) + permission (policy) + shape (serialization),
  BYO-model, BYO-key. The product produces the pack; the user's AI consumes it.

A per-role BI view and a per-role AI context are the *same operation*. Users define their
own personas, views, serializations. **Flexibility axis #3.**

---

## The extension axes (this is what "everything extensible" means)

Four orthogonal axes, none touching the others, because identity-filtering lives in one
place (layer 3) and truth in one place (layer 2):

1. **Graph kind** — new node / edge / aspect → layer 2 grows; others just see new nodes.
2. **Policy kind / rule** — new role / masking rule → layer 3 grows; filter resolves
   differently.
3. **Projection kind** — new persona / view / AI pack → layer 4 grows; a new lens.
4. **Check** — new built-in-style or user check → runs in the cleaner pass; reads the
   graph, reports through the tier system. No new pipeline.

Any "what if they want X" resolves to one of these. If it cannot, that is the only signal
the core is genuinely missing something.

---

## Opinionation — a rule-tier system, with a hard floor

Every rule AND every check declares a tier. Tiers are the mechanism; posture presets are
the user-facing setting.

```
structural   the bad state is IMPOSSIBLE to represent.
             (one logical node per real thing; edges must resolve)
             requires zero discipline; NEVER part of any setting. The floor.
error        expressible but the compiler FAILS CLOSED, no outputs until fixed.
             (completeness; unambiguous duplicate; user error-tier checks)
warn         usually wrong, sometimes right → warn, proceed.
             (formula similarity by default; hygiene findings)
off          disabled.
```

Map onto the derived/authored line: hard-enforce **structure** (always) and
**completeness** (error at strict); **guide** on **content judgment** (warn). Force the
floor, guide the ceiling.

### Teaching findings

Every error/warn finding states *what is wrong, why it matters, and the one fix*. The
defaults and scaffolding embody best practice (`init` produces the right layout; node
templates pre-stamp required fields; policy is deny-by-default), so doing nothing yields
correct structure and the findings teach the rest. The inexperienced user falls into the
pit of success.

### Posture is a setting — structural floor is not

```
strict      (default for init) completeness at error · full teaching cleaner
standard    structural + security floor (always) · completeness as warnings
permissive  structural + security floor ONLY · all style/completeness off ·
            get out of the way — but the security floor still holds
```

Project-level posture with explicit, **recorded** per-rule and per-check overrides.
**Structural integrity AND the security floor are never part of the setting** — both are
impossible to violate in every posture, including `permissive`. The dial governs *opinion
and hygiene*, never *integrity or security*. Even `permissive` cannot corrupt the core or
open a data hole; it only silences style and completeness nagging.

---

## Why opinionated and flexible coexist

| Concern | Rigid (opinionated) | Flexible (user-defined) |
|---|---|---|
| Identity | one logical node per thing — structural, always | IDs / domains / names / bindings are yours |
| Provenance | every fact stamped derived/authored — structural | what you author is yours |
| Completeness | owner/classification/policy required at strict — error | the values are yours |
| Non-duplication | identity dup impossible (structural); formula dup warns | reuse/alias/separate is your call |
| Checks | run through one engine + tier system | write any check you want (axis #4) |
| Node/aspect kinds | must use node base + attach by ID — structural | invent any aspect/kind (axis #1) |
| Policy | one engine, three honest modes — mechanism | every rule and role is yours (axis #2) |
| Projection | must route through policy — structural | every persona/view is yours (axis #3) |
| Posture | structural + security floor non-negotiable | error/warn/off is your setting |
| Security | floor is structural — cannot expose ungoverned data, ever | every role, rule, and classification value is yours |

Rigidity is always about *shape, identity, integrity, and not leaking data*. Flexibility
is always about *content, meaning, access rules, and the checks you run*. They never touch
the same layer.

---

## The MVP — core plus two modules, built interleaved

A core validated against zero modules is a hypothesis. Build the two modules *with* the
core so each hardens it; fix the core whenever a module makes it awkward, while cheap.

### Core (free, local — engine source-protected; formats open)
```
project schema · logical IDs + bindings · compiler · graph store ·
node/edge/aspect model · contract primitive · provenance + derivation-state ·
cleaner (check engine: built-in + user checks) · rule-tier validator · graph query API
```

### Module A — Live query primitive (proves the graph is buildable)
```
metric definition · query definition · contract ·
compiled SQL · query endpoint · result schema · frontend binding contract
```
Proves the graph can compile/execute live queries a frontend binds to. Not a renderer.

### Module B — Derived lineage / catalog (proves the graph holds derived truth)
```
dbt manifest ingestion · raw SQL ingestion · information_schema ingestion ·
model/column lineage (with derivation state) · metric dependency graph ·
impact analysis · minimal catalog projection
```

Both read the same nodes by the same canonical IDs. One executes, one traverses, on one
graph — turning "extensible" from promise into demonstrated fact.

### Brutally simple I/O
```
Input:   dbt manifest · SQL folder · information_schema · YAML metrics & queries
Output:  compiled graph JSON · impact CLI · query endpoint ·
         minimal catalog JSON · frontend contract JSON · cleaner report
```

### First demo
```bash
clearmetric scan
clearmetric compile
clearmetric clean                       # built-in + any user checks
clearmetric impact column.fct_orders.net_revenue
clearmetric serve
clearmetric query query.executive.revenue_by_month
```
Then show the same metric powering: live query result · lineage traversal · catalog
projection. That proves the thesis.

### Explicitly NOT in the MVP (keep attachment placeholders)
```
full RLS · full RBAC · full AI agent · full dashboard builder ·
full policy compiler · full usage analytics · full catalog UI · approvals
```
```yaml
security: { classification: internal, policy_refs: [] }
ai:       { allowed: true, notes: [] }
usage:    { tracking_enabled: false }
```

---

## The four invariants (non-negotiable, every posture)

1. **One logical node per real thing**, with physical bindings — the same node to
   lineage, policy, usage, and BI.
2. **The graph never forks per persona** — personas are projections, never copies. The
   graph stores ownership refs but makes no authorization decisions.
3. **All ClearMetric-native authorization is layer 3**; external is enforced only when
   compiled to target or routed through runtime — stated honestly.
4. **Provenance + derivation state stamped on every fact** — derived vs authored explicit;
   derived facts carry status/confidence; the compiler requires only the authored half.
5. **The security floor is structural** — no unclassified exposure, no ungoverned PII,
   policy fails closed, security checks cannot be disabled, deny-by-default, and user
   extensions inherit all of it. No posture and no extension can lower it.

---

## Deployment & input flexibility — the core is portable by design

The core must not assume *where* it runs or *what* it reads from. Both are kept flexible by
the same move that keeps everything else flexible: **the compiled graph artifact is the
contract, and everything around it is interchangeable.** One compiler, one graph format;
the inputs that feed it and the runtimes that host it are pluggable.

### Input flexibility — adapters in, one graph out

The compiler never hard-codes a source. Every source is an **ingestion adapter** that
produces graph fragments in the canonical format; the compiler merges them. Core ships the
common adapters; new sources are added as adapters without touching the core.

```
INGESTION ADAPTERS (pluggable)              →  one canonical graph
  warehouse INFORMATION_SCHEMA (Snowflake,
    BigQuery, Postgres, Databricks, ...)
  dbt manifest
  raw SQL folder (sqlglot)
  query logs
  authored intent (YAML)
  <user / future adapter>
```

Consequences that matter:
- A team on **dbt** and a team on **raw SQL with no dbt** both produce the same graph —
  the wedge segment (non-dbt shops) is served by an adapter, not a different product.
- Adding a warehouse or a source is an adapter, not a core change. **Input is an extension
  axis, governed by the same derivation-state honesty** (each adapter stamps
  status/confidence/source so a weak source degrades visibly, never silently).
- The graph format is the same regardless of what fed it, so downstream
  (cleaner, policy, projection, consumers) never knows or cares about the source.

### Deployment flexibility — one artifact, many runtimes

The same compiled graph runs in every deployment shape because the artifact is identical;
only the runtime around it changes.

```
COMPILE (open engine, runs anywhere)
  clearmetric compile  →  graph.json  (the portable deploy unit)

RUN IT (pick any — same artifact):
  local        clearmetric serve            (laptop / CI — single player, ephemeral)
  self-hosted  deploy graph.json to your own infra (air-gapped / federal-friendly)
  managed      clearmetric deploy --to clearmetric.ai
                                            (paid: persisted history, team, SSO, audit)
```

Rules that keep this from forking into two products:
- **One compiler, never two.** Compilation runs the same open engine whether local, in
  CI, or invoked by the hosted instance. The hosted product does **not** reinterpret the
  graph — it persists, serves, and wraps it with the multiplayer layer. No separate hosted
  compiler, ever.
- **The artifact is the only contract between local and hosted.** As long as the open
  engine emits a stable graph format and the hosted instance consumes that same format,
  "deploy" is a push, the two halves upgrade independently, and a user can run fully local,
  fully self-hosted, or compile-local-then-host-serve with nothing about the graph
  changing.
- **Compile-anywhere, source-of-truth-is-what-was-deployed.** Users may compile locally
  and push (CI / dev-first motion) **or** connect a repo and let the managed instance
  compile on commit (managed motion) — same engine binary in both. The hosted instance's
  truth is whatever artifact was deployed to it.
- **Portable in and out.** The artifact a user deploys is the artifact they can leave with
  (open formats, the anti-lock-in guarantee). Deployment flexibility and the no-lock-in
  promise are the same property.

### Why this is "core enough"

Flexibility of input and deployment is not a feature bolted on later — it falls out of the
artifact-as-contract design the rest of the architecture already rests on. The graph does
not know its source (adapters absorb that) and does not know its runtime (the artifact is
identical everywhere). So the core stays small and stable while *where it reads from* and
*where it runs* both extend freely — federal air-gapped self-host, a developer's laptop,
and the paid managed instance are the same engine and the same graph, differing only in
the runtime wrapped around the artifact.

---



## Distribution — open spec, free engine, paid history

Three layers, each treated according to where its value comes from. The mistake to avoid
is calling the whole thing "open source": only one layer is, and claiming more than that
is a false claim the audience will catch.

### Layer 1 — Open formats (real OSS, Apache 2.0)

The value of the formats is in being *adopted*, so they are genuinely open. Published as a
separate `clearmetric-spec` repo under Apache 2.0:

```
graph schema · node / edge / aspect schema · contract schema ·
metric & query YAML format · derivation-state format · finding / cleaner-report format ·
policy-as-data format · projection / AI-context-pack format ·
OpenAPI spec for the local + runtime API · example projects · reference fixtures
```

This is the part you may truthfully call open source. It does all the work openness needs
to do: it makes every artifact **portable**, and it backs the anti-lock-in promise —
*even if ClearMetric disappears, your graph, contracts, lineage, policy intent, findings,
and AI-context packs are documented JSON/YAML you own.* That value holds at any adoption
level and the formats cost nothing to keep open; publishing them is near-free and
effectively one-way, so traction does not change whether opening them was correct.

Artifacts emit in these open formats plus established standards — **OpenLineage, JSON
Schema, OpenAPI, OPA bundles** (note: OSI is a *semantic spec*, not an artifact format).

### Layer 2 — Free engine (source-protected, not OSS)

The value of the engine is in being *hard*, so it is protected. Free to run, not free to
fork-and-host. This is the **product**: identity resolver, SQL/dbt lineage compiler,
metric/query compiler, duplicate detector, cleaner runtime, policy *evaluator*, projection
engine, warehouse adapters, runtime query execution. A competitor reading the open formats
still has to build all of this.

The formats are the contract; the engine is the product. Open the contract, protect the
product.

Engine-license dial (a separate, deferrable, one-directional decision — start protective,
loosen later if adoption justifies it; never the reverse):
- **closed binary** — best protection, lower trust;
- **source-available / fair-source** (FSL-style, converts to OSS after ~2 years) — better
  trust, still blocks a hosted competitor;
- **full OSS engine** — only once distribution, hosted history, and momentum make the
  protection unnecessary.

Whatever the dial, **say "open formats, free engine," never "open-source product"** unless
and until the engine itself is under an OSI-approved license.

### Layer 3 — Paid managed (the business and the moat)

The value of the hosted layer is *accumulated*, so it is paid and it is durable. Hosted
graph **history** (the persisted, time-versioned graph — what a metric meant last quarter,
who changed what, the decision trail), collaboration, SSO/RBAC at team scale, audit,
managed runtime, policy *deployment* to warehouses, enterprise connectors.

Why this is distribution-resistant: the moat is not the code, it is the history living in
*customers'* hosted instances. A better-distributed player can fork the free engine, but
cannot fork the accumulated graph history your customers depend on. **The engine is the
commodity you give away; the history is the moat you keep** — and it is precisely the part
frontier models cannot reconstruct, so it is also the part that does not compress as models
improve. Moat, paid tier, and model-resistance are the same thing.

### Repo structure (makes the boundary physical, not a policy to remember)

```
clearmetric-spec      Apache 2.0 · public · schemas · OpenAPI · examples · fixtures
clearmetric-cli       free binary · source-protected · compile · clean · impact · query
clearmetric-engine    private · resolver · lineage · compiler internals · check runtime
clearmetric-cloud     paid · hosted history · collaboration · audit · policy deployment
```

Separate repos with separate licenses so the boundary cannot erode by gradual blur — the
engine physically cannot leak into the open repo.

### What the docs/site should say

> ClearMetric uses open, documented artifact formats. Your analytics graph, contracts,
> lineage, policy intent, findings, and AI-context packs are portable JSON/YAML artifacts
> that you own. The local compiler is free to use; the managed platform is optional.

Not: *"ClearMetric is open source"* — unless the engine is under an OSI-approved license.

---

## Positioning

**For buyers:**
> A compiled analytics graph that turns code-defined metrics, queries, lineage, metadata,
> and policy intent into reusable infrastructure for BI, AI, and governance.

**For the first developers (the wedge):**
> Live analytics primitives and derived lineage from the same codebase.

Central concrete phrase:
> ClearMetric turns analytics definitions into queryable graph nodes and bindable
> contracts.

---

## The five hard constraints (obey or it fails)

1. Do not build the giant platform first — core plus two modules, interleaved.
2. Do not claim perfect derivation — track coverage, confidence, gaps.
3. Do not claim universal policy enforcement — native / runtime / advisory, stated.
4. Do not tell buyers to build their own BI tool — they get frontend control over
   governed analytics primitives.
5. Do not separate core from modules — live query and lineage from day one.