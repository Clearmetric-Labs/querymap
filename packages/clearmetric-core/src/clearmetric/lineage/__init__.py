"""Public package surface for clearmetric-core."""

from __future__ import annotations

from clearmetric.core import CatalogArtifact

from ._version import __version__
from .api import (
    build_catalog_artifact,
    build_lineage_map,
    build_openlineage_export,
    render_json,
    render_text,
    trace_downstream,
    trace_upstream,
)
from .errors import LineageContractError, LineageError, LineageInputError
from .models import LineageMap, LineageSummary, TraversalResult

__all__ = [
    "__version__",
    "build_catalog_artifact",
    "build_lineage_map",
    "build_openlineage_export",
    "CatalogArtifact",
    "LineageContractError",
    "LineageError",
    "LineageInputError",
    "LineageMap",
    "LineageSummary",
    "render_json",
    "render_text",
    "trace_downstream",
    "trace_upstream",
    "TraversalResult",
]
