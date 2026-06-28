from __future__ import annotations

from clearmetric.cleaner import run_compile_checks
from clearmetric.cleaner.posture import resolve_severity, warnings_to_findings
from clearmetric.core.models import CatalogArtifact, DerivationState, Node, Warning


def test_resolve_severity_matrix():
    assert resolve_severity("structural", "strict") == "error"
    assert resolve_severity("error", "strict") == "error"
    assert resolve_severity("warn", "strict") == "warn"
    assert resolve_severity("error", "standard") == "warn"
    assert resolve_severity("warn", "standard") == "warn"
    assert resolve_severity("error", "permissive") is None
    assert resolve_severity("warn", "permissive") is None


def test_unknown_warning_code_becomes_finding():
    findings = warnings_to_findings(
        [Warning(code="custom_warning", message="something", subject_id="column:x.y")],
        posture="strict",
    )
    assert len(findings) == 1
    assert findings[0].severity == "warn"
    assert findings[0].check_id == "check.custom_warning"


def test_partial_derivation_warns_under_strict():
    artifact = CatalogArtifact(
        nodes=[
            Node(
                id="column:orders.amount",
                kind="column",
                name="amount",
                qualified_name="orders.amount",
                derivation=DerivationState(
                    status="partial",
                    confidence="low",
                    source="sqlglot",
                ),
            )
        ]
    )
    strict = run_compile_checks(artifact, posture="strict")
    permissive = run_compile_checks(artifact, posture="permissive")
    assert any(
        f.check_id == "check.partial_derivation" and f.severity == "warn"
        for f in strict.findings
    )
    assert not any(
        f.check_id == "check.partial_derivation" for f in permissive.findings
    )


def test_failed_derivation_errors_under_strict():
    artifact = CatalogArtifact(
        nodes=[
            Node(
                id="column:orders.amount",
                kind="column",
                name="amount",
                qualified_name="orders.amount",
                derivation=DerivationState(
                    status="failed",
                    confidence="low",
                    source="sqlglot",
                ),
            )
        ]
    )
    strict = run_compile_checks(artifact, posture="strict")
    assert any(
        f.check_id == "check.failed_derivation" and f.severity == "error"
        for f in strict.findings
    )
