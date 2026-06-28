"""Report-only clean orchestration."""

from __future__ import annotations

from pathlib import Path

from clearmetric.cleaner.models import CleanerReport

from .compile import build_graph
from .models import CompiledGraph
from .validate import check_graph


def clean(project_dir: Path) -> tuple[CleanerReport, CompiledGraph]:
    # build_graph (not compile): clean must report warnings without enforce failing first.
    compiled = build_graph(project_dir)
    report = check_graph(compiled.artifact, posture=compiled.project.posture)
    return report, compiled
