from querymap import build_query_map


def test_extracts_simple_table_relation():
    query_map = build_query_map("SELECT * FROM public.customers", dialect="postgres")

    assert len(query_map.relations) == 1
    assert query_map.relations[0].kind == "table"
    assert query_map.relations[0].qualified_name == "public.customers"
    assert query_map.edges[0].source_id == "query:root"
    assert query_map.edges[0].target_id == "table:public.customers"


def test_extracts_root_and_cte_relation_usages():
    sql = """
    WITH temp AS (
        SELECT *
        FROM raw.orders o
    )
    SELECT *
    FROM temp t
    """
    query_map = build_query_map(sql, dialect="postgres")

    relation_ids = {relation.id for relation in query_map.relations}
    assert "cte:temp" in relation_ids
    assert "table:raw.orders" in relation_ids

    usage_aliases = {(usage.relation_id, usage.alias, usage.context) for usage in query_map.relation_usages}
    assert ("table:raw.orders", "o", "cte_body") in usage_aliases
    assert ("cte:temp", "t", "from") in usage_aliases
