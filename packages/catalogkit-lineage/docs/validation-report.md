# catalogkit-lineage validation report

## Verdict

**PASS** for the launch claim:

> Correct where resolvable, explicit where not, no credentials. Column and dataset impact analysis for dbt Core / SQL projects — headless and CI-ready.

This PASS is based on the trustworthiness invariant, not on probe count alone:

- zero silent columns across the committed fixture corpus
- zero bogus `source_leaf` classifications across the committed fixture corpus
- deterministic JSON output across every committed fixture
- recoverable bad-file behavior, CLI/API parity, and artifact merge coverage all passing
- exact ground-truth probes and adversarial fixtures still passing as regression oracles

The main caution is no longer "silent wrong output" on the current corpus. The
remaining caution is **coverage depth and oracle quality** for future probes.
Only fully enumerated, independently checked truth sets should be committed.

## Fixture results

| Fixture | Input kind | Dialect | Probes | Columns | Resolved | Flagged | Silent | Notes |
|---|---|---:|---:|---:|---:|---:|---:|---|
| `jaffle_shop` | dbt manifest | `postgres` | 4 | 38 | 27 | 0 | 0 | Baseline dbt fixture; value-lineage probes on `raw_payments.amount` and `raw_payments.payment_method`. |
| `loom_finance` | dbt manifest | `duckdb` | 3 | 10 | 4 | 0 | 0 | Public cross-project dbt slice with exact probes on `orders.amount`, `customer_name`, and `total_revenue`. |
| `loom_marketing` | dbt manifest | `duckdb` | 3 | 11 | 4 | 0 | 0 | Public cross-project dbt slice with exact probes on `campaign_events.clicks`, `customer_tier`, and `total_clicks`. |
| `shopify` | dbt manifest | `postgres` | 3 | 436 | 138 | 298 | 0 | Expanded 30-model dependency closure from anchor models; warning-rich but no silent columns. |
| `sql_folder` | SQL folder | `postgres` | 2 | 7 | 7 | 0 | 0 | Validates the non-dbt path. |

### Ground-truth summary

- Total committed probes: `15`
- False negatives: `0`
- False positives: `0`
- Exact downstream impact is now committed for:
  - `raw_payments.amount` in `jaffle_shop`
  - `raw_payments.payment_method` in `jaffle_shop`
  - `orders.amount` in `loom_finance`
  - `campaign_events.clicks` in `loom_marketing`
  - `orders_base.amount` in the plain SQL fixture
- Explicit warning behavior is now committed for:
  - `shopify__customers.lifetime_total_spent` when unresolved behavior changes
  - `stg_shopify__order.order_id` on the expanded Shopify closure

## Adversarial matrix

| Case | Result | Notes |
|---|---|---|
| `case_predicate_only` | Pass | Predicate column excluded; value column preserved. |
| `cte_column_realias` | Pass | Preserved lineage across two CTE alias hops. |
| `union_all_branches` | Pass | Merged lineage across both branches. |
| `window_function_derived` | Pass | Derived column traced to aggregated input only; partition key intentionally excluded from value-lineage. |
| `subquery_from` | Pass | Inner select lineage preserved. |
| `subquery_select` | Pass | Scalar subquery lineage preserved. |
| `ambiguous_join_column` | Pass | Correct branch chosen for selected output columns. |
| `nested_cte` | Pass | Multi-layer CTE aliasing preserved. |
| `select_star_no_schema` | Pass with warnings | Emits `select_star` + `unresolved_star_source`, no invented edges. |
| `select_star_with_schema` | Pass | Resolves `SELECT *` exactly when schema is known. |
| `table_star_alias` | Pass with warnings | Warns with `unresolved_output_source` plus final `unresolved_lineage` flags instead of inventing alias-root lineage like `column:r.amount`. |
| `dialect_postgres` | Pass | Cast syntax traced correctly. |
| `dialect_snowflake` | Pass | Cast syntax traced correctly. |
| `dialect_bigquery` | Pass | Cast syntax traced correctly. |
| `unparseable_sibling` | Pass with warnings | Broken file emits `lineage_resolution_failed`; valid sibling still resolves. |

## Robustness results

- **Determinism:** `render_json(build_lineage_map(...))` is byte-stable across every committed fixture, not only `jaffle_shop`.
- **Recoverability:** one bad SQL file in a folder no longer aborts the whole run during dependency inference or star detection; it emits `lineage_resolution_failed` and preserves valid sibling lineage.
- **CLI/API parity:** JSON downstream output from the CLI matches the Python API for the same selection.
- **Artifact validity:** lineage artifacts still merge cleanly with `catalogkit-query` on shared canonical IDs.
- **Output legibility:** traversal output is now a tree by default, with Mermaid export available for `--upstream` / `--downstream`.

## Trustworthiness change

The disqualifying bug class at the start of validation was: **manifest-declared
column node exists, sqlglot cannot resolve it, and the result is empty with no
warning.**

That class is now closed by construction:

- every local-model column is classified as `resolved`, `flagged`, or invalid
  under the corpus invariant
- every unresolved local-model column receives a column-scoped warning with
  `subject_id`
- the invariant is enforced in CI across the full fixture corpus

This does **not** mean every column resolves. It means unresolved columns are no
longer silent.

## Comparison baseline

### vs raw `sqlglot.lineage`

- Raw sqlglot required manual assembly of `5` model SQL sources and `3` root schema tables before asking one downstream impact question on `jaffle_shop`.
- Raw sqlglot has no project-level downstream API, so the baseline had to reverse-scan every modeled output column to answer `raw_payments.amount`.
- Raw reverse scan returned:
  - `customers.customer_lifetime_value`
  - `orders.amount`
  - `orders.bank_transfer_amount`
  - `orders.coupon_amount`
  - `orders.credit_card_amount`
  - `orders.gift_card_amount`
  - `stg_payments.amount`
- `catalogkit-lineage` returned the same impact set through one project-level traversal over stable `column:` IDs.

### vs dbt manifest lineage

- dbt `child_map` for `seed.jaffle_shop.raw_payments` yields model descendants:
  - `stg_payments`
  - `orders`
  - `customers`
- `catalogkit-lineage` resolves the affected **columns** instead:
  - `stg_payments.amount`
  - `customers.customer_lifetime_value`
  - `orders.amount`
  - `orders.bank_transfer_amount`
  - `orders.coupon_amount`
  - `orders.credit_card_amount`
  - `orders.gift_card_amount`

### vs Canva `dbt-column-lineage-extractor`

- Canva’s extractor uses a two-step workflow:
  - `dbt_column_lineage_direct` builds lineage JSON files from `--manifest` plus `--catalog`
  - `dbt_column_lineage_recursive` answers one `--model` + `--column` query from those generated files
- `catalogkit-lineage` answers the impact question in one headless command against a manifest **or a plain SQL folder**, and emits a mergeable `CatalogArtifact` rather than tool-specific intermediate files.
- Concrete CLI difference observed from the installed extractor help:
  - direct command: `usage: cli_direct.py [-h] [--manifest MANIFEST] [--catalog CATALOG]`
  - recursive command: `usage: cli_recursive.py [-h] --model MODEL --column COLUMN`

## What changed during validation

Validation found and fixed several real robustness issues:

- wildcard output names from `sqlglot` (`*`) no longer crash canonical ID creation; they warn with `unresolved_star_source`
- alias-only `table.*` leaves no longer create fake root datasets such as `column:r.amount`; they warn with `unresolved_output_source`
- malformed SQL files in a folder no longer abort dependency inference or star detection before the per-file recoverable warning path can run
- manifest-declared columns that fall outside sqlglot's resolved output map no longer disappear silently; they reconcile to explicit column-scoped warnings
- traversal output is now readable as a tree, with Mermaid export for inspection without a UI

## Launch recommendation

Launch `catalogkit-lineage` on the impact-analysis claim now that the
trustworthiness invariant is green on the expanded Shopify closure.

Frame it with the current committed limitations stated plainly:

- it is strong on exact impact traversal for committed probe shapes
- it is honest on unresolved star-heavy or alias-heavy SQL by warning instead of inventing lineage
- the public Shopify closure is still warning-rich, so it should be framed as partially resolvable complex SQL rather than universal exact coverage
- `derives_from` is **value-lineage**, not universal reference-lineage for every predicate use

Do **not** claim universal exact column lineage on arbitrary warehouse-compiled dbt SQL. Claim **headless, CI-ready impact analysis with exact results on committed probe shapes and honest warnings on unresolved cases**.
