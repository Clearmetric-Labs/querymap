from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from catalogkit.core import merge
from catalogkit.lineage import (
    build_catalog_artifact,
    build_lineage_map,
    trace_downstream,
)
from catalogkit.query import build_catalog_artifact as build_query_catalog_artifact


def _manifest_root() -> Path:
    return Path(__file__).resolve().parent / "fixtures" / "projects" / "jaffle_shop"


def _sql_folder_root() -> Path:
    return Path(__file__).resolve().parent / "fixtures" / "projects" / "sql_folder"


def test_bad_sql_file_warns_without_killing_valid_sibling(tmp_path: Path):
    (tmp_path / "valid.sql").write_text(
        "select amount from raw_orders", encoding="utf-8"
    )
    (tmp_path / "broken.sql").write_text("select from", encoding="utf-8")

    lineage_map = build_lineage_map(tmp_path, dialect="postgres")

    warning_codes = [warning.code for warning in lineage_map.warnings]
    derives_from = {
        (edge.source_id, edge.target_id)
        for edge in lineage_map.edges
        if edge.kind == "derives_from"
    }

    assert "lineage_resolution_failed" in warning_codes
    assert ("column:valid.amount", "column:raw_orders.amount") in derives_from


def test_cli_and_api_match_for_downstream_json_output():
    fixture_root = _sql_folder_root()
    api_result = trace_downstream(
        fixture_root,
        dialect="postgres",
        selection="orders_base.amount",
    )

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "catalogkit.lineage",
            "--dialect",
            "postgres",
            "--format",
            "json",
            "--downstream",
            "orders_base.amount",
            str(fixture_root),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["related_ids"] == api_result.related_ids


def test_lineage_and_query_artifacts_merge_on_shared_ids():
    example_root = _manifest_root()
    manifest_path = example_root / "manifest.json"
    customers_sql = (example_root / "compiled" / "customers.sql").read_text(
        encoding="utf-8"
    )

    lineage_artifact = build_catalog_artifact(manifest_path, dialect="postgres")
    query_artifact = build_query_catalog_artifact(customers_sql, dialect="postgres")
    merged = merge(lineage_artifact, query_artifact)

    stg_orders_nodes = [node for node in merged.nodes if node.id == "table:stg_orders"]
    raw_payments_nodes = [
        node for node in merged.nodes if node.id == "table:raw_payments"
    ]

    assert len(stg_orders_nodes) == 1
    assert len(raw_payments_nodes) == 1
