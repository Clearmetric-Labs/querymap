"""Public artifact models for clearmetric-core."""

from __future__ import annotations

from typing import Literal

from clearmetric.core import Edge, Node, Warning
from pydantic import BaseModel, Field

InputKind = Literal["dbt_manifest", "sql_folder"]


class LineageSummary(BaseModel):
    dialect: str
    input_kind: InputKind
    dataset_count: int
    root_dataset_count: int
    column_count: int
    warning_count: int


class TraversalResult(BaseModel):
    selection: str
    selection_id: str
    related_ids: list[str] = Field(default_factory=list)
    warnings: list[Warning] = Field(default_factory=list)


class LineageMap(BaseModel):
    version: str = "1"
    summary: LineageSummary
    nodes: list[Node] = Field(default_factory=list)
    edges: list[Edge] = Field(default_factory=list)
    warnings: list[Warning] = Field(default_factory=list)
