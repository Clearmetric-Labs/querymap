"""JSON rendering for clearmetric-core."""

from __future__ import annotations

from clearmetric.core import CatalogArtifact
from clearmetric.core import render_json as core_render_json

from ..models import PowerBIMap


def render_json(value: CatalogArtifact | PowerBIMap) -> dict:
    """Return a JSON-serializable clearmetric-core artifact payload."""
    if isinstance(value, CatalogArtifact):
        return core_render_json(value)
    return value.model_dump(mode="json", by_alias=True)
