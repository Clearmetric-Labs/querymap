from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from clearmetric.lineage import (
    build_lineage_map,
    trace_downstream,
)


def _manifest_root() -> Path:
    return (
        Path(__file__).resolve().parent.parent
        / "fixtures"
        / "lineage"
        / "projects"
        / "jaffle_shop"
    )


def _sql_folder_root() -> Path:
    return (
        Path(__file__).resolve().parent.parent
        / "fixtures"
        / "lineage"
        / "projects"
        / "sql_folder"
    )


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
            "clearmetric.cli",
            "impact",
            "orders_base.amount",
            str(fixture_root),
            "--dialect",
            "postgres",
            "--downstream",
            "--format",
            "json",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["related_ids"] == api_result.related_ids
