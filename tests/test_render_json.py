from __future__ import annotations

from querymap import build_query_map, render_json


def test_render_json_keeps_forward_compatible_shape():
    query_map = build_query_map(
        """
        WITH temp AS (
            SELECT *
            FROM public.orders
        )
        SELECT *
        FROM temp
        """,
        dialect="postgres",
    )

    payload = render_json(query_map)

    assert payload["version"] == "1"
    assert "summary" in payload
    assert "relations" in payload
    assert "relation_usages" in payload
    assert "edges" in payload
    assert "outputs" in payload
    assert "warnings" in payload
    assert payload["outputs"] == []
    assert any(relation["kind"] == "cte" for relation in payload["relations"])
