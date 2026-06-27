"""Tests for M source extraction."""

from __future__ import annotations

from clearmetric.powerbi.m_parser import extract_m_sources


def test_extract_sql_database_and_native_query():
    m_query = """
    let
        Source = Sql.Database("warehouse.company.net", "SalesMart"),
        Query = Value.NativeQuery(Source, "SELECT o.OrderID FROM dbo.Orders o")
    in
        Query
    """
    sources = extract_m_sources(m_query)
    connectors = {source.connector for source in sources}
    assert "Sql.Database" in connectors
    assert "Value.NativeQuery" in connectors
    assert any(source.native_sql for source in sources)


def test_empty_expression_returns_empty_list():
    assert extract_m_sources("") == []
