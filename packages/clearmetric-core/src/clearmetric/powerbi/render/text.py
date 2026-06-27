"""Text rendering for clearmetric-core."""

from __future__ import annotations

from clearmetric.core import CatalogArtifact

from ..models import PowerBIMap


def render_text(value: CatalogArtifact | PowerBIMap) -> str:
    if isinstance(value, PowerBIMap):
        summary = value.summary
        lines = [
            "clearmetric-core",
            f"project: {summary.project_name}",
            f"tables: {summary.table_count}",
            f"visuals: {summary.visual_count}",
            f"upstream_sources: {summary.upstream_source_count}",
            f"unresolved_joins: {summary.unresolved_join_count}",
        ]
        return "\n".join(lines)

    lines = [
        "clearmetric-core artifact",
        f"nodes: {len(value.nodes)}",
        f"edges: {len(value.edges)}",
    ]
    for warning in value.warnings:
        location = f" ({warning.location})" if warning.location else ""
        lines.append(f"warning[{warning.code}]{location}: {warning.message}")
    return "\n".join(lines)
