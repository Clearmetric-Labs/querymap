"""Verify each ClearMetric Core module builds artifacts without requiring other modules."""

from __future__ import annotations

from pathlib import Path

from clearmetric.lineage import build_catalog_artifact as build_lineage_artifact
from clearmetric.powerbi import build_catalog_artifact as build_powerbi_artifact
from clearmetric.query import build_catalog_artifact as build_query_artifact

REPO_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = REPO_ROOT / "packages" / "clearmetric-core"
JAFFLE_MANIFEST = (
    PACKAGE_ROOT
    / "tests"
    / "fixtures"
    / "lineage"
    / "projects"
    / "jaffle_shop"
    / "manifest.json"
)
PBIP_FIXTURE = (
    PACKAGE_ROOT / "tests" / "fixtures" / "powerbi" / "minimal_pbip" / "minimal.pbip"
)
SIMPLE_SQL = PACKAGE_ROOT / "tests" / "examples" / "query" / "simple.sql"


def test_query_module_builds_artifact_standalone():
    sql = SIMPLE_SQL.read_text(encoding="utf-8")
    artifact = build_query_artifact(sql, dialect="postgres")
    assert artifact.version == "1"
    assert artifact.nodes


def test_lineage_module_builds_artifact_standalone():
    artifact = build_lineage_artifact(JAFFLE_MANIFEST, dialect="postgres")
    assert artifact.version == "1"
    assert any(node.kind == "column" for node in artifact.nodes)


def test_powerbi_module_builds_artifact_standalone():
    artifact = build_powerbi_artifact(PBIP_FIXTURE)
    assert artifact.version == "1"
    assert any(node.kind == "visual" for node in artifact.nodes)
