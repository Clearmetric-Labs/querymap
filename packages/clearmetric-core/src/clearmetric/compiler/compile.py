"""Compile orchestration."""

from __future__ import annotations

from pathlib import Path

from clearmetric.adapters.registry import enabled_sources, ingest_all
from clearmetric.core import attach_warehouse_bindings, merge
from clearmetric.core.project import load_project_aliases, load_project_config

from .models import CompiledGraph
from .validate import enforce_graph


def build_graph(project_dir: Path) -> CompiledGraph:
    """Ingest, merge, and bind warehouse metadata without enforcing checks."""
    root = project_dir.expanduser().resolve()
    project = load_project_config(root)
    alias_map = load_project_aliases(project)

    ingested = ingest_all(project)
    artifacts = [artifact for _kind, artifact in ingested]
    merged = merge(*artifacts) if len(artifacts) > 1 else artifacts[0]

    warehouse_artifact = next(
        (artifact for kind, artifact in ingested if kind == "warehouse"),
        None,
    )
    if warehouse_artifact is not None:
        merged = attach_warehouse_bindings(
            merged=merged,
            warehouse_artifact=warehouse_artifact,
            alias_map=alias_map,
        )

    return CompiledGraph(
        artifact=merged,
        project=project,
        project_dir=root,
        sources_run=enabled_sources(project),
    )


def compile(project_dir: Path) -> CompiledGraph:
    """Build and enforce a valid compiled graph."""
    compiled = build_graph(project_dir)
    enforce_graph(compiled.artifact, posture=compiled.project.posture)
    return compiled
