from __future__ import annotations

import ast
from pathlib import Path


FORBIDDEN_PREFIXES = (
    "apps",
    "services",
    "models",
    "utils",
    "shared_config",
    "definition_foundation",
)


def test_querymap_has_no_enterprise_imports():
    package_root = Path(__file__).resolve().parents[1] / "querymap"
    violations: list[str] = []

    for path in package_root.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.startswith(FORBIDDEN_PREFIXES):
                        violations.append(f"{path}: import {alias.name}")
            elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
                if node.module.startswith(FORBIDDEN_PREFIXES):
                    violations.append(f"{path}: from {node.module} import ...")

    assert violations == []
