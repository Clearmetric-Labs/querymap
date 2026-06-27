"""Tests for native SQL table reference extraction."""

from __future__ import annotations

from clearmetric.powerbi.native_sql import native_sql_table_refs


def test_native_sql_table_refs_extracts_schema_and_table():
    refs = native_sql_table_refs("SELECT OrderID FROM dbo.Orders")
    assert refs == [("dbo", "orders")]


def test_native_sql_table_refs_extracts_unqualified_table():
    refs = native_sql_table_refs("SELECT * FROM raw_orders")
    assert refs == [(None, "raw_orders")]


def test_native_sql_table_refs_deduplicates():
    sql = "SELECT * FROM dbo.Orders JOIN dbo.Orders AS o2 ON 1=1"
    refs = native_sql_table_refs(sql)
    assert refs == [("dbo", "orders")]
