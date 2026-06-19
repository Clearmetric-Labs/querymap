from querymap import QueryMap, QuerySummary


def test_query_map_contract_is_forward_compatible():
    query_map = QueryMap(
        summary=QuerySummary(
            dialect="postgres",
            statement_type="select",
            has_ctes=False,
            relation_count=0,
            cte_count=0,
            output_count=0,
        )
    )

    payload = query_map.model_dump(mode="json")

    assert payload["version"] == "1"
    assert payload["relations"] == []
    assert payload["relation_usages"] == []
    assert payload["edges"] == []
    assert payload["outputs"] == []
    assert payload["warnings"] == []
