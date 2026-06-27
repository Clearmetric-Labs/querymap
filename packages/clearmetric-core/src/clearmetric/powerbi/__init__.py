"""Public package surface for clearmetric-core."""

from __future__ import annotations

from clearmetric.core import CatalogArtifact

from ._version import __version__
from .api import (
    build_catalog_artifact,
    build_powerbi_map,
    merge_with_warehouse,
    render_json,
    render_text,
)
from .errors import PowerBIError, PowerBIInputError, PowerBIStructureError

__all__ = [
    "__version__",
    "build_catalog_artifact",
    "build_powerbi_map",
    "CatalogArtifact",
    "merge_with_warehouse",
    "PowerBIError",
    "PowerBIInputError",
    "PowerBIStructureError",
    "render_json",
    "render_text",
]
