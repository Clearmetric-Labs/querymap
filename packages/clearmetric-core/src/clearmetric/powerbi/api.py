"""Public API for clearmetric-core."""

from __future__ import annotations

from pathlib import Path

from clearmetric.core import AliasMap, CatalogArtifact

from .build import (
    build_catalog_artifact_from_project,
    build_powerbi_map_from_project,
    merge_with_warehouse,
)
from .discovery import discover_project
from .models import PowerBIMap
from .render.json import render_json
from .render.text import render_text

__all__ = [
    "build_catalog_artifact",
    "build_powerbi_map",
    "merge_with_warehouse",
    "render_json",
    "render_text",
]


def build_catalog_artifact(
    project_input: str | Path,
    *,
    alias_map: AliasMap | None = None,
    warehouse_table_ids: set[str] | None = None,
) -> CatalogArtifact:
    """Build a shared ClearMetric Core artifact for one PBIP project."""
    project = discover_project(project_input)
    return build_catalog_artifact_from_project(
        project,
        alias_map=alias_map,
        warehouse_table_ids=warehouse_table_ids,
    )


def build_powerbi_map(
    project_input: str | Path,
    *,
    alias_map: AliasMap | None = None,
    warehouse_table_ids: set[str] | None = None,
) -> PowerBIMap:
    """Build the public clearmetric-core artifact for one PBIP project."""
    project = discover_project(project_input)
    return build_powerbi_map_from_project(
        project,
        alias_map=alias_map,
        warehouse_table_ids=warehouse_table_ids,
    )
