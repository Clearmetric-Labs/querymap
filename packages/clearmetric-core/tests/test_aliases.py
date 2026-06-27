"""Tests for table alias file loading."""

from __future__ import annotations

from pathlib import Path

import pytest
from clearmetric.core import load_table_alias_map
from clearmetric.core.errors import AliasMapError


def test_load_table_alias_map_normalizes_entries(tmp_path: Path):
    alias_file = tmp_path / "aliases.yaml"
    alias_file.write_text(
        """version: 1
table_aliases:
  SalesMart.dbo.Orders: Orders
  dbo.stg_orders: stg_orders
""",
        encoding="utf-8",
    )

    aliases = load_table_alias_map(alias_file)

    assert aliases["salesmart.dbo.orders"] == "orders"
    assert aliases["dbo.stg_orders"] == "stg_orders"


def test_load_table_alias_map_rejects_unsupported_version(tmp_path: Path):
    alias_file = tmp_path / "aliases.yaml"
    alias_file.write_text(
        """version: 2
table_aliases:
  a: b
""",
        encoding="utf-8",
    )

    with pytest.raises(AliasMapError, match="Unsupported alias file version"):
        load_table_alias_map(alias_file)


def test_load_table_alias_map_rejects_missing_sections(tmp_path: Path):
    alias_file = tmp_path / "aliases.yaml"
    alias_file.write_text("version: 1\n", encoding="utf-8")

    with pytest.raises(AliasMapError, match="Missing 'table_aliases:'"):
        load_table_alias_map(alias_file)


def test_load_table_alias_map_rejects_duplicate_conflicting_keys(tmp_path: Path):
    alias_file = tmp_path / "aliases.yaml"
    alias_file.write_text(
        """version: 1
table_aliases:
  orders: a
  Orders: b
""",
        encoding="utf-8",
    )

    with pytest.raises(AliasMapError, match="Duplicate alias key"):
        load_table_alias_map(alias_file)
