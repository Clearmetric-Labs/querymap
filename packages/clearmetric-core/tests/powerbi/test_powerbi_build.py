"""Tests for clearmetric-core build pipeline."""

from __future__ import annotations

from pathlib import Path

import pytest
from clearmetric.powerbi import build_catalog_artifact
from clearmetric.powerbi.errors import PowerBIInputError, PowerBIStructureError

FIXTURE_ROOT = (
    Path(__file__).resolve().parent.parent / "fixtures" / "powerbi" / "minimal_pbip"
)


def test_build_catalog_artifact_from_minimal_pbip():
    artifact = build_catalog_artifact(str(FIXTURE_ROOT / "minimal.pbip"))

    table_ids = {node.id for node in artifact.nodes if node.kind == "table"}
    assert any(node_id.endswith(".orders") for node_id in table_ids)
    assert any(node.kind == "visual" for node in artifact.nodes)
    assert any(edge.kind == "feeds" for edge in artifact.edges)
    assert any(
        edge.match_status == "unresolved"
        for edge in artifact.edges
        if edge.kind == "feeds"
    )


def test_unresolved_join_does_not_fail_whole_build():
    artifact = build_catalog_artifact(str(FIXTURE_ROOT / "minimal.pbip"))
    assert artifact.nodes
    assert any(warning.code == "dax_deferred" for warning in artifact.warnings)


def test_missing_project_raises_input_error(tmp_path: Path):
    with pytest.raises(PowerBIInputError):
        build_catalog_artifact(str(tmp_path / "missing.pbip"))


def test_invalid_pbip_json_raises_structure_error(tmp_path: Path):
    bad = tmp_path / "bad.pbip"
    bad.write_text("{not json", encoding="utf-8")
    with pytest.raises(PowerBIStructureError):
        build_catalog_artifact(str(bad))
