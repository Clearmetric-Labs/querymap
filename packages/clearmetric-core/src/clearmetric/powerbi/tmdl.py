"""Minimal TMDL table/source extraction for V1."""

from __future__ import annotations

import re
from pathlib import Path

from .errors import PowerBIStructureError
from .models import SemanticTableDefinition

_TABLE_HEADER = re.compile(r"^table\s+(\S+)", re.MULTILINE)
_SOURCE_BLOCK = re.compile(
    r"source\s*=\s*\n((?:[ \t]+.*\n)+?)(?=\n[^\s]|\Z)",
    re.MULTILINE,
)


def extract_tables_from_semantic_model(
    semantic_model_path: str,
) -> list[SemanticTableDefinition]:
    """Extract table names and M source expressions from TMDL files."""
    root = Path(semantic_model_path)
    tables_dir = root / "definition" / "tables"
    if not tables_dir.is_dir():
        raise PowerBIStructureError(
            f"Semantic model missing definition/tables directory: {semantic_model_path}"
        )

    tables: list[SemanticTableDefinition] = []
    for tmdl_file in sorted(tables_dir.glob("*.tmdl")):
        content = tmdl_file.read_text(encoding="utf-8")
        table_match = _TABLE_HEADER.search(content)
        if not table_match:
            continue
        table_name = table_match.group(1).strip().strip('"')
        source_match = _SOURCE_BLOCK.search(content)
        if not source_match:
            continue
        m_expression = _dedent_m_block(source_match.group(1))
        tables.append(
            SemanticTableDefinition(
                name=table_name,
                m_expression=m_expression,
                file=str(tmdl_file),
            )
        )
    return tables


def _dedent_m_block(block: str) -> str:
    lines = block.splitlines()
    if not lines:
        return ""
    indents = [len(line) - len(line.lstrip(" ")) for line in lines if line.strip()]
    min_indent = min(indents) if indents else 0
    dedented = [
        line[min_indent:] if len(line) >= min_indent else line for line in lines
    ]
    return "\n".join(dedented).strip()
