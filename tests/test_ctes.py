from pathlib import Path

from querymap import build_query_map


def _read_example(name: str) -> str:
    return (Path(__file__).resolve().parents[1] / "examples" / name).read_text(
        encoding="utf-8"
    )


def test_extracts_nested_cte_dependencies():
    query_map = build_query_map(_read_example("nested_ctes.sql"), dialect="postgres")

    edge_pairs = {(edge.source_id, edge.target_id) for edge in query_map.edges}
    assert ("cte:raw_orders", "table:analytics.orders") in edge_pairs
    assert ("cte:customer_totals", "cte:raw_orders") in edge_pairs
    assert ("query:root", "cte:customer_totals") in edge_pairs


def test_ugly_query_maps_relations_and_warnings():
    query_map = build_query_map(_read_example("ugly_real_world.sql"), dialect="postgres")

    relation_ids = {relation.id for relation in query_map.relations}
    assert "table:analytics.orders" in relation_ids
    assert "table:analytics.customers" in relation_ids
    assert "cte:base_orders" in relation_ids
    assert "cte:customer_rollup" in relation_ids
    assert "cte:ranked_customers" in relation_ids

    warning_codes = {warning.code for warning in query_map.warnings}
    assert "select_star" in warning_codes
