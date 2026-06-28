"""Project discovery."""

from __future__ import annotations

from pathlib import Path

from clearmetric.core.project import load_project_config

from .models import DiscoverReport, ResolvedSource


def discover(project_dir: Path) -> DiscoverReport:
    project = load_project_config(project_dir)
    sources: list[ResolvedSource] = []
    if project.sources.warehouse is not None:
        sources.append(
            ResolvedSource(
                kind="warehouse",
                path=project.sources.warehouse.path,
            )
        )
    if project.aliases is not None:
        sources.append(ResolvedSource(kind="aliases", path=project.aliases))
    if project.sources.dbt is not None and project.sources.dbt.manifest:
        sources.append(ResolvedSource(kind="dbt", path=project.sources.dbt.manifest))
    if project.sources.sql is not None:
        for path in project.sources.sql.paths:
            sources.append(ResolvedSource(kind="sql", path=path))
    return DiscoverReport(
        config_path=str((project_dir / "clearmetric.yaml").resolve()),
        dialect=project.dialect,
        sources=sources,
    )
