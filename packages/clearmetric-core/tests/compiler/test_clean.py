from __future__ import annotations

from pathlib import Path

import pytest
from clearmetric.compiler.clean import clean
from clearmetric.core.errors import StructuralCheckError
from clearmetric.core.models import CatalogArtifact, Edge, Node

from tests.wedge.helpers import setup_wedge_project


def test_clean_reports_without_failing_on_warnings(tmp_path: Path):
    project_dir = setup_wedge_project(tmp_path)
    report, _compiled = clean(project_dir)
    assert isinstance(report.findings, list)
    errors = [f for f in report.findings if f.severity == "error"]
    assert not errors


def test_compile_raises_on_structural_error():
    bad = CatalogArtifact(
        nodes=[
            Node(
                id="column:orders.amount",
                kind="column",
                name="amount",
                qualified_name="orders.amount",
            )
        ],
        edges=[
            Edge(
                kind="derives_from",
                source_id="column:missing",
                target_id="column:orders.amount",
                label="derives_from",
            )
        ],
    )
    from clearmetric.compiler.validate import enforce_graph

    with pytest.raises(StructuralCheckError):
        enforce_graph(bad, posture="strict")
