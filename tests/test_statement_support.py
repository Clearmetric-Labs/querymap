from __future__ import annotations

import pytest

from querymap import build_query_map
from querymap.errors import QueryMapContractError


def test_create_as_select_is_supported():
    sql = """
    CREATE TABLE analytics.customer_totals AS
    SELECT customer_id, SUM(amount) AS total_amount
    FROM analytics.orders
    GROUP BY customer_id
    """

    query_map = build_query_map(sql, dialect="postgres")

    assert query_map.summary.statement_type == "create"
    relation_ids = {relation.id for relation in query_map.relations}
    assert "table:analytics.orders" in relation_ids
    assert ("query:root", "table:analytics.orders") in {
        (edge.source_id, edge.target_id) for edge in query_map.edges
    }


def test_insert_select_is_supported():
    sql = """
    INSERT INTO analytics.customer_totals
    SELECT customer_id, SUM(amount) AS total_amount
    FROM analytics.orders
    GROUP BY customer_id
    """

    query_map = build_query_map(sql, dialect="postgres")

    assert query_map.summary.statement_type == "insert"
    relation_ids = {relation.id for relation in query_map.relations}
    assert "table:analytics.orders" in relation_ids
    assert ("query:root", "table:analytics.orders") in {
        (edge.source_id, edge.target_id) for edge in query_map.edges
    }


def test_unsupported_statement_fails_loudly():
    with pytest.raises(QueryMapContractError):
        build_query_map("UPDATE analytics.orders SET status = 'closed'", dialect="postgres")
