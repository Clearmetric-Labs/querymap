from __future__ import annotations

import pytest

from querymap import build_query_map
from querymap.errors import QueryMapContractError, QueryMapParseError


def test_invalid_sql_fails_loudly():
    with pytest.raises(QueryMapParseError):
        build_query_map("NOT VALID SQL AT ALL !!!", dialect="postgres")


def test_multiple_statements_fail_loudly():
    sql = "SELECT * FROM customers; SELECT * FROM orders;"

    with pytest.raises(QueryMapContractError):
        build_query_map(sql, dialect="postgres")
