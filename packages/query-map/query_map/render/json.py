"""JSON renderer for query-map."""

from __future__ import annotations

from ..models import QueryMap


def render_json(query_map: QueryMap) -> dict:
    """Return the canonical JSON-serializable query-map artifact."""
    return query_map.model_dump(mode="json", by_alias=True)
