"""Projection filtering."""

from __future__ import annotations

from clearmetric.core.models import CatalogArtifact, Edge, Node
from clearmetric.policy.evaluate import evaluate
from clearmetric.policy.models import PolicyRulesFile

CATALOG_ASSET_KINDS = frozenset({"table", "column", "model"})


def project_catalog_assets(artifact: CatalogArtifact) -> CatalogArtifact:
    """Admin unfiltered asset slice for catalog output (no policy filter)."""
    nodes = [node for node in artifact.nodes if node.kind in CATALOG_ASSET_KINDS]
    allowed_ids = {node.id for node in nodes}
    edges = [
        edge
        for edge in artifact.edges
        if edge.source_id in allowed_ids and edge.target_id in allowed_ids
    ]
    return CatalogArtifact(
        version=artifact.version,
        nodes=nodes,
        edges=edges,
        warnings=[],
    )


def project_graph(
    artifact: CatalogArtifact,
    *,
    identity: str,
    rules: PolicyRulesFile,
) -> CatalogArtifact:
    allowed_ids = {
        node.id
        for node in artifact.nodes
        if evaluate(node=node, identity=identity, rules=rules) != "deny"
    }
    nodes: list[Node] = [node for node in artifact.nodes if node.id in allowed_ids]
    edges: list[Edge] = [
        edge
        for edge in artifact.edges
        if edge.source_id in allowed_ids and edge.target_id in allowed_ids
    ]
    return CatalogArtifact(
        version=artifact.version,
        nodes=nodes,
        edges=edges,
        warnings=artifact.warnings,
    )
