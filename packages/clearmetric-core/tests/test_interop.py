"""Tests for cross-graph interop helpers."""

from __future__ import annotations

from clearmetric.core import (
    apply_alias_map,
    merge,
    normalize_fqn_for_matching,
    resolve_table_match,
    warehouse_table_fqn_candidates,
    warehouse_table_fqn_candidates_from_name,
)
from clearmetric.core.models import CatalogArtifact, Edge, Node


def test_normalize_fqn_for_matching_handles_quotes_and_case():
    left = normalize_fqn_for_matching('"SalesDB"."dbo"."Orders"')
    right = normalize_fqn_for_matching("salesdb.dbo.orders")
    assert left == right == "salesdb.dbo.orders"


def test_warehouse_table_fqn_candidates_returns_specific_to_general():
    candidates = warehouse_table_fqn_candidates(
        database="SalesDB",
        schema="dbo",
        table="Orders",
    )
    assert candidates == ["salesdb.dbo.orders", "dbo.orders", "orders"]


def test_apply_alias_map_resolves_dbt_model_alias():
    alias_map = {"orders": "salesdb.dbo.orders"}
    assert apply_alias_map("Orders", alias_map) == "salesdb.dbo.orders"


def test_resolve_table_match_resolved():
    target_ids = {"table:salesdb.dbo.orders", "table:analytics.customers"}
    matched_id, status = resolve_table_match(
        ["dbo.orders"],
        target_ids,
        alias_map={"dbo.orders": "salesdb.dbo.orders"},
    )
    assert matched_id == "table:salesdb.dbo.orders"
    assert status == "resolved"


def test_resolve_table_match_ambiguous():
    target_ids = {"table:dbo.orders", "table:sales.orders"}
    matched_id, status = resolve_table_match(["orders"], target_ids)
    assert status == "ambiguous"
    assert matched_id in target_ids


def test_resolve_table_match_unresolved():
    matched_id, status = resolve_table_match(["missing.table"], {"table:other.table"})
    assert matched_id is None
    assert status == "unresolved"


def test_warehouse_table_fqn_candidates_from_name_expands_to_general_candidates():
    candidates = warehouse_table_fqn_candidates_from_name("salesmart.dbo.orders")
    assert candidates == ["salesmart.dbo.orders", "dbo.orders", "orders"]


def test_merge_preserves_match_status_on_edges():
    left = CatalogArtifact(
        nodes=[Node(id="table:a", kind="table", name="a")],
        edges=[
            Edge(
                kind="feeds",
                source_id="table:warehouse.orders",
                target_id="table:a",
                match_status="resolved",
            )
        ],
    )
    right = CatalogArtifact(
        nodes=[Node(id="table:a", kind="table", name="a")],
        edges=[
            Edge(
                kind="feeds",
                source_id="table:warehouse.orders",
                target_id="table:a",
                evidence=[],
            )
        ],
    )
    merged = merge(left, right)
    assert merged.edges[0].match_status == "resolved"
