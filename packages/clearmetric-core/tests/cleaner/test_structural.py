from __future__ import annotations

import pytest
from clearmetric.cleaner import enforce_checks, run_compile_checks
from clearmetric.core.errors import StructuralCheckError
from clearmetric.core.models import CatalogArtifact, Edge, Node, PhysicalBinding


def test_run_compile_checks_reports_dangling_edge():
    artifact = CatalogArtifact(
        edges=[
            Edge(
                kind="derives_from",
                source_id="column:missing.x",
                target_id="column:present.y",
                label="derives_from",
            )
        ]
    )
    report = run_compile_checks(artifact, posture="strict")
    assert any(
        finding.check_id == "check.edges_resolve" and finding.severity == "error"
        for finding in report.findings
    )


def test_enforce_checks_raises():
    artifact = CatalogArtifact(
        edges=[
            Edge(
                kind="derives_from",
                source_id="column:missing.x",
                target_id="column:present.y",
                label="derives_from",
            )
        ]
    )
    with pytest.raises(StructuralCheckError):
        enforce_checks(artifact, posture="strict")


def test_duplicate_bindings_fail_enforce():
    binding = PhysicalBinding(
        warehouse="jaffle",
        schema="analytics",
        table="orders",
        column="amount",
    )
    artifact = CatalogArtifact(
        nodes=[
            Node(
                id="column:orders.amount",
                kind="column",
                name="amount",
                qualified_name="orders.amount",
                bindings=[binding],
            ),
            Node(
                id="column:marts.orders.amount",
                kind="column",
                name="amount",
                qualified_name="marts.orders.amount",
                bindings=[binding],
            ),
        ]
    )
    with pytest.raises(StructuralCheckError, match="duplicate_bindings"):
        enforce_checks(artifact, posture="strict")
