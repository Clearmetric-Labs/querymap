from __future__ import annotations

from pathlib import Path

from clearmetric.core import load_table_alias_map, merge
from clearmetric.lineage import build_catalog_artifact as build_warehouse
from clearmetric.powerbi import build_catalog_artifact as build_powerbi
from clearmetric.powerbi import merge_with_warehouse

REPO_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = REPO_ROOT / "packages" / "clearmetric-core"
JAFFLE_MANIFEST = (
    PACKAGE_ROOT
    / "tests"
    / "fixtures"
    / "lineage"
    / "projects"
    / "jaffle_shop"
    / "manifest.json"
)
PBIP_FIXTURE = (
    PACKAGE_ROOT / "tests" / "fixtures" / "powerbi" / "minimal_pbip" / "minimal.pbip"
)
GOLDEN_ALIAS_FILE = REPO_ROOT / "tests" / "fixtures" / "golden_merge" / "aliases.yaml"


def test_lineage_and_query_artifacts_merge_on_shared_ids():
    from clearmetric.query import build_catalog_artifact as build_query_catalog_artifact

    customers_sql = (JAFFLE_MANIFEST.parent / "compiled" / "customers.sql").read_text(
        encoding="utf-8"
    )

    lineage_artifact = build_warehouse(JAFFLE_MANIFEST, dialect="postgres")
    query_artifact = build_query_catalog_artifact(customers_sql, dialect="postgres")
    merged = merge(lineage_artifact, query_artifact)

    stg_orders_nodes = [node for node in merged.nodes if node.id == "table:stg_orders"]
    raw_payments_nodes = [
        node for node in merged.nodes if node.id == "table:raw_payments"
    ]

    assert len(stg_orders_nodes) == 1
    assert len(raw_payments_nodes) == 1


def test_lineage_and_powerbi_artifacts_merge():
    warehouse = build_warehouse(JAFFLE_MANIFEST, dialect="postgres")
    powerbi = build_powerbi(PBIP_FIXTURE)
    merged = merge(warehouse, powerbi)

    assert any(node.kind == "table" for node in merged.nodes)
    assert any(node.kind == "visual" for node in merged.nodes)


def test_golden_lineage_powerbi_merge_resolves_orders_without_alias():
    warehouse = build_warehouse(JAFFLE_MANIFEST, dialect="postgres")
    powerbi = build_powerbi(PBIP_FIXTURE)
    merged = merge_with_warehouse(powerbi, warehouse)

    feed_edges = [
        edge
        for edge in merged.edges
        if edge.kind == "feeds"
        and edge.target_id == "table:minimal.semantic_model.orders"
    ]
    assert len(feed_edges) == 1
    edge = feed_edges[0]
    assert edge.source_id == "table:orders"
    assert edge.match_status == "resolved"


def test_golden_lineage_powerbi_merge_loads_alias_file():
    warehouse = build_warehouse(JAFFLE_MANIFEST, dialect="postgres")
    powerbi = build_powerbi(PBIP_FIXTURE)
    alias_map = load_table_alias_map(GOLDEN_ALIAS_FILE)
    merged = merge_with_warehouse(powerbi, warehouse, alias_map=alias_map)

    feed_edges = [edge for edge in merged.edges if edge.kind == "feeds"]
    assert feed_edges
    assert all(edge.match_status == "resolved" for edge in feed_edges)


def test_standalone_powerbi_leaves_unresolved_feeds():
    powerbi = build_powerbi(PBIP_FIXTURE)
    feed_edges = [edge for edge in powerbi.edges if edge.kind == "feeds"]
    assert feed_edges
    assert all(edge.match_status == "unresolved" for edge in feed_edges)
