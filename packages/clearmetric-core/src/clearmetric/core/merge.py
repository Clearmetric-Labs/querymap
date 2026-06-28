"""Artifact merge utilities."""

from __future__ import annotations

from typing import Any

from .errors import MergeConflictError
from .interop import physical_binding_key
from .models import (
    CatalogArtifact,
    DerivationState,
    Edge,
    Evidence,
    Node,
    PhysicalBinding,
    Warning,
)


def merge(*artifacts: CatalogArtifact) -> CatalogArtifact:
    """Merge multiple artifacts under the shared clearmetric-core rules."""
    merged_nodes: dict[str, Node] = {}
    merged_edges: dict[tuple[str, str, str], Edge] = {}
    merged_warnings: dict[tuple[str, str, str | None, str | None], Warning] = {}
    disagreement_warnings: list[Warning] = []

    for artifact in artifacts:
        for warning in artifact.warnings:
            merged_warnings[
                (
                    warning.code,
                    warning.message,
                    warning.location,
                    warning.subject_id,
                )
            ] = warning

        for node in artifact.nodes:
            existing = merged_nodes.get(node.id)
            if existing is None:
                merged_nodes[node.id] = node
                continue
            merged_node, warnings = _merge_node(existing, node)
            merged_nodes[node.id] = merged_node
            disagreement_warnings.extend(warnings)

        for edge in artifact.edges:
            key = (edge.kind, edge.source_id, edge.target_id)
            existing = merged_edges.get(key)
            if existing is None:
                merged_edges[key] = edge
                continue
            merged_edge, warnings = _merge_edge(existing, edge)
            merged_edges[key] = merged_edge
            disagreement_warnings.extend(warnings)

    for warning in disagreement_warnings:
        merged_warnings[
            (warning.code, warning.message, warning.location, warning.subject_id)
        ] = warning

    return CatalogArtifact(
        version=_merge_versions([artifact.version for artifact in artifacts]),
        nodes=sorted(merged_nodes.values(), key=lambda node: node.id),
        edges=sorted(
            merged_edges.values(),
            key=lambda edge: (edge.kind, edge.source_id, edge.target_id),
        ),
        warnings=sorted(
            merged_warnings.values(),
            key=lambda warning: (
                warning.code,
                warning.message,
                warning.location or "",
                warning.subject_id or "",
            ),
        ),
    )


def _merge_versions(versions: list[str]) -> str:
    unique_versions = {version for version in versions if version}
    if not unique_versions:
        return "1"
    if len(unique_versions) != 1:
        raise MergeConflictError(
            f"Cannot merge artifacts with different schema versions: {sorted(unique_versions)}"
        )
    return unique_versions.pop()


def _merge_node(left: Node, right: Node) -> tuple[Node, list[Warning]]:
    warnings: list[Warning] = []
    if left.kind != right.kind:
        raise MergeConflictError(
            f"Conflicting node.kind values for {left.id!r}: {left.kind!r} != {right.kind!r}"
        )

    name = left.name
    if left.name != right.name:
        warnings.append(
            Warning(
                code="source_disagreement",
                message=(
                    f"Sources disagree on node.name for {left.id!r}: "
                    f"{left.name!r} vs {right.name!r}"
                ),
                subject_id=left.id,
            )
        )

    qualified_name = _merge_optional_value(
        left.qualified_name,
        right.qualified_name,
        left.id,
        "node.qualified_name",
        warnings,
    )
    schema_name = _merge_optional_value(
        left.schema_name,
        right.schema_name,
        left.id,
        "node.schema",
        warnings,
    )

    return (
        Node(
            id=left.id,
            kind=left.kind,
            name=name,
            qualified_name=qualified_name,
            schema=schema_name,
            evidence=_merge_evidence(left.evidence, right.evidence),
            derivation=_merge_derivation(
                left.derivation, right.derivation, left.id, warnings
            ),
            bindings=_merge_bindings(left.bindings, right.bindings, left.id, warnings),
            aspects=_merge_aspects(left.aspects, right.aspects, left.id, warnings),
        ),
        warnings,
    )


def _merge_edge(left: Edge, right: Edge) -> tuple[Edge, list[Warning]]:
    warnings: list[Warning] = []
    if left.kind != right.kind:
        raise MergeConflictError(
            f"Conflicting edge.kind for {left.source_id!r}->{left.target_id!r}"
        )

    label = _merge_optional_value(
        left.label,
        right.label,
        f"{left.source_id}->{left.target_id}",
        "edge.label",
        warnings,
    )
    confidence = left.confidence
    if left.confidence != right.confidence:
        warnings.append(
            Warning(
                code="source_disagreement",
                message=(
                    f"Sources disagree on edge.confidence for "
                    f"{left.kind}:{left.source_id}->{left.target_id}: "
                    f"{left.confidence!r} vs {right.confidence!r}"
                ),
                subject_id=left.source_id,
            )
        )

    match_status = _merge_optional_value(
        left.match_status,
        right.match_status,
        f"{left.source_id}->{left.target_id}",
        "edge.match_status",
        warnings,
    )

    return (
        Edge(
            kind=left.kind,
            source_id=left.source_id,
            target_id=left.target_id,
            label=label,
            confidence=confidence,
            match_status=match_status,
            evidence=_merge_evidence(left.evidence, right.evidence),
            derivation=_merge_derivation(
                left.derivation,
                right.derivation,
                left.source_id,
                warnings,
            ),
        ),
        warnings,
    )


def _merge_optional_value(
    left: Any,
    right: Any,
    owner: str,
    field_name: str,
    warnings: list[Warning],
) -> Any:
    if left in (None, ""):
        return right
    if right in (None, ""):
        return left
    if left != right:
        warnings.append(
            Warning(
                code="source_disagreement",
                message=(
                    f"Sources disagree on {field_name} for {owner!r}: "
                    f"{left!r} vs {right!r}"
                ),
                subject_id=owner if owner.startswith(("column:", "table:")) else None,
            )
        )
    return left


def _merge_derivation(
    left: DerivationState | None,
    right: DerivationState | None,
    subject_id: str,
    warnings: list[Warning],
) -> DerivationState | None:
    if left is None:
        return right
    if right is None:
        return left
    if left.status == right.status and left.confidence == right.confidence:
        return left
    warnings.append(
        Warning(
            code="source_disagreement",
            message=(
                f"Sources disagree on derivation for {subject_id!r}: "
                f"{left.status}/{left.confidence} vs {right.status}/{right.confidence}"
            ),
            subject_id=subject_id,
        )
    )
    return left


def _merge_bindings(
    left: list[PhysicalBinding] | None,
    right: list[PhysicalBinding] | None,
    node_id: str,
    warnings: list[Warning],
) -> list[PhysicalBinding] | None:
    merged: dict[tuple[str, str, str, str, str], PhysicalBinding] = {}
    for binding in [*(left or []), *(right or [])]:
        key = physical_binding_key(binding)
        existing = merged.get(key)
        if existing is not None and existing != binding:
            warnings.append(
                Warning(
                    code="schema_drift",
                    message=(
                        f"Conflicting physical bindings for {node_id!r} at {key!r}"
                    ),
                    subject_id=node_id,
                )
            )
            continue
        merged[key] = binding
    return list(merged.values()) or None


def _merge_aspects(
    left: dict[str, Any] | None,
    right: dict[str, Any] | None,
    node_id: str,
    warnings: list[Warning],
) -> dict[str, Any] | None:
    if not left and not right:
        return None
    merged = dict(left or {})
    for key, value in (right or {}).items():
        if key not in merged:
            merged[key] = value
            continue
        if merged[key] != value:
            warnings.append(
                Warning(
                    code="source_disagreement",
                    message=(f"Sources disagree on aspect {key!r} for {node_id!r}"),
                    subject_id=node_id,
                )
            )
    return merged or None


def _merge_evidence(left: list[Evidence], right: list[Evidence]) -> list[Evidence]:
    seen: set[tuple[str | None, str | None, str | None, str]] = set()
    merged: list[Evidence] = []

    for evidence in [*left, *right]:
        key = (
            evidence.file,
            evidence.location,
            evidence.expression,
            evidence.confidence,
        )
        if key in seen:
            continue
        seen.add(key)
        merged.append(evidence)

    return merged
