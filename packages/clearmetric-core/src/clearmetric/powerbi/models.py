"""Internal models for clearmetric-core."""

from __future__ import annotations

from dataclasses import dataclass, field

from clearmetric.core import Edge, Node, Warning
from pydantic import BaseModel, Field


@dataclass(frozen=True)
class MSourceReference:
    source_type: str
    connector: str
    server: str | None = None
    database: str | None = None
    schema: str | None = None
    table: str | None = None
    native_sql: str | None = None
    step_name: str | None = None


@dataclass(frozen=True)
class SemanticTableDefinition:
    name: str
    m_expression: str
    file: str


@dataclass(frozen=True)
class VisualBinding:
    visual_id: str
    page_id: str | None
    visual_type: str | None
    table_name: str | None
    field_name: str
    field_kind: str  # measure | column
    role: str


@dataclass
class DiscoveredProject:
    root: str
    project_name: str
    semantic_model_path: str | None = None
    report_path: str | None = None
    tables: list[SemanticTableDefinition] = field(default_factory=list)


class PowerBISummary(BaseModel):
    project_name: str
    table_count: int = 0
    visual_count: int = 0
    upstream_source_count: int = 0
    unresolved_join_count: int = 0


class PowerBIMap(BaseModel):
    version: str = "1"
    summary: PowerBISummary
    nodes: list[Node] = Field(default_factory=list)
    edges: list[Edge] = Field(default_factory=list)
    warnings: list[Warning] = Field(default_factory=list)
