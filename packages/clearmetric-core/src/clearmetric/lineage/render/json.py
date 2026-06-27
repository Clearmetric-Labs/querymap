"""JSON renderer for clearmetric-core."""

from __future__ import annotations

from ..models import LineageMap


def render_json(lineage_map: LineageMap) -> dict:
    """Return the canonical JSON-serializable clearmetric-core artifact."""
    return lineage_map.model_dump(mode="json", by_alias=True)
