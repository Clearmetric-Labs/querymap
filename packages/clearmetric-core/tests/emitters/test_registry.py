from __future__ import annotations

import json
from pathlib import Path

from clearmetric.compiler.compile import compile as compile_project
from clearmetric.emitters.registry import emit_compile

from tests.wedge.helpers import setup_wedge_project


def test_compile_returns_merged_graph(tmp_path: Path):
    compiled = compile_project(setup_wedge_project(tmp_path))
    assert compiled.sources_run == ["warehouse", "dbt"]
    assert any(node for node in compiled.artifact.nodes if node.bindings)


def test_emit_compile_json(tmp_path: Path):
    compiled = compile_project(setup_wedge_project(tmp_path))
    payload = json.loads(emit_compile("json", compiled))
    assert payload["version"] == "1"
    assert payload["nodes"]


def test_emit_compile_catalog_excludes_non_assets(tmp_path: Path):
    compiled = compile_project(setup_wedge_project(tmp_path))
    payload = json.loads(emit_compile("catalog", compiled))
    kinds = {node["kind"] for node in payload["nodes"]}
    assert kinds.issubset({"table", "column", "model"})
    assert "report" not in kinds
    assert "visual" not in kinds
