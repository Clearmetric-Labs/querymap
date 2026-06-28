"""Impact orchestration."""

from __future__ import annotations

from pathlib import Path

from clearmetric.lineage import (
    trace_downstream_from_artifact,
    trace_upstream_from_artifact,
)
from clearmetric.lineage.graph import TraversalDirection
from clearmetric.lineage.models import TraversalResult

from .compile import compile
from .models import CompiledGraph


def impact(
    project_dir: Path,
    *,
    selection: str,
    direction: TraversalDirection,
) -> tuple[CompiledGraph, TraversalResult]:
    # compile (not build_graph): impact requires an enforced-valid graph for traversal.
    compiled = compile(project_dir)
    if direction == "upstream":
        result = trace_upstream_from_artifact(compiled.artifact, selection=selection)
    else:
        result = trace_downstream_from_artifact(compiled.artifact, selection=selection)
    return compiled, result
