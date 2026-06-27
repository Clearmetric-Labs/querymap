"""PBIP project discovery."""

from __future__ import annotations

import json
from pathlib import Path

from .errors import PowerBIInputError, PowerBIStructureError
from .models import DiscoveredProject
from .tmdl import extract_tables_from_semantic_model


def discover_project(project_input: str | Path) -> DiscoveredProject:
    """Discover semantic model and report folders from a PBIP root or folder."""
    path = Path(project_input).expanduser().resolve()
    if not path.exists():
        raise PowerBIInputError(f"Project input does not exist: {path}")

    if path.is_file() and path.suffix.lower() == ".pbip":
        return _discover_from_pbip_file(path)

    if path.is_dir():
        pbip_files = sorted(path.glob("*.pbip"))
        if len(pbip_files) == 1:
            return _discover_from_pbip_file(pbip_files[0])
        if _looks_like_semantic_model(path) or _looks_like_report(path):
            return _discover_from_folder(path, project_name=path.name)
        raise PowerBIStructureError(
            f"Directory is not a PBIP root or recognizable Power BI project: {path}"
        )

    raise PowerBIInputError(
        f"Expected a .pbip file or project directory, got: {project_input}"
    )


def _discover_from_pbip_file(pbip_file: Path) -> DiscoveredProject:
    try:
        payload = json.loads(pbip_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise PowerBIStructureError(f"Invalid PBIP JSON: {pbip_file}") from exc

    root = pbip_file.parent
    project_name = pbip_file.stem
    semantic_model_path: str | None = None
    report_path: str | None = None

    for artifact in payload.get("artifacts", []) or []:
        if isinstance(artifact, dict):
            if "dataset" in artifact:
                semantic_model_path = str(
                    (root / artifact["dataset"]["path"]).resolve()
                )
            if "report" in artifact:
                report_path = str((root / artifact["report"]["path"]).resolve())

    if not semantic_model_path and not report_path:
        raise PowerBIStructureError(
            f"PBIP file does not reference a semantic model or report: {pbip_file}"
        )

    project = DiscoveredProject(
        root=str(root),
        project_name=project_name,
        semantic_model_path=semantic_model_path,
        report_path=report_path,
    )
    if semantic_model_path:
        project.tables = extract_tables_from_semantic_model(semantic_model_path)
    return project


def _discover_from_folder(path: Path, *, project_name: str) -> DiscoveredProject:
    semantic_model_path = None
    report_path = None
    if _looks_like_semantic_model(path):
        semantic_model_path = str(path)
    elif _looks_like_report(path):
        report_path = str(path)
    else:
        for child in path.iterdir():
            if not child.is_dir():
                continue
            if child.name.endswith(".SemanticModel") and _looks_like_semantic_model(
                child
            ):
                semantic_model_path = str(child.resolve())
            if child.name.endswith(".Report") and _looks_like_report(child):
                report_path = str(child.resolve())

    project = DiscoveredProject(
        root=str(path),
        project_name=project_name,
        semantic_model_path=semantic_model_path,
        report_path=report_path,
    )
    if semantic_model_path:
        project.tables = extract_tables_from_semantic_model(semantic_model_path)
    return project


def _looks_like_semantic_model(path: Path) -> bool:
    definition = path / "definition"
    return definition.is_dir() and (definition / "tables").is_dir()


def _looks_like_report(path: Path) -> bool:
    definition = path / "definition"
    return definition.is_dir()
