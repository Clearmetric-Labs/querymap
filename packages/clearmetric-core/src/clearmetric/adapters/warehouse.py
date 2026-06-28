"""Warehouse metadata ingestion adapter."""

from __future__ import annotations

import json
from pathlib import Path

from clearmetric.core import CatalogArtifact, Evidence, Node, PhysicalBinding
from clearmetric.core.errors import AdapterError
from clearmetric.core.ids import column_id, table_id
from clearmetric.core.models import DerivationState
from clearmetric.core.project import ClearMetricProject, WarehouseSource
from pydantic import BaseModel, Field, ValidationError


class WarehouseMetadataColumn(BaseModel):
    name: str
    data_type: str | None = None
    nullable: bool | None = None
    ordinal_position: int | None = None
    comment: str | None = None


class WarehouseMetadataTable(BaseModel):
    database: str | None = None
    schema_name: str | None = Field(default=None, alias="schema")
    name: str
    columns: list[WarehouseMetadataColumn] = Field(default_factory=list)


class WarehouseMetadataDocument(BaseModel):
    warehouse: str = "information_schema"
    tables: list[WarehouseMetadataTable] = Field(default_factory=list)


def ingest_warehouse(project: ClearMetricProject) -> CatalogArtifact:
    source = project.sources.warehouse
    if source is None:
        raise AdapterError("warehouse source is not configured")
    return _ingest_information_schema(source, warehouse_name="information_schema")


def _ingest_information_schema(
    source: WarehouseSource,
    *,
    warehouse_name: str,
) -> CatalogArtifact:
    path = Path(source.path)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise AdapterError(f"warehouse metadata is not valid JSON: {path}") from exc
    try:
        document = WarehouseMetadataDocument.model_validate(payload)
    except ValidationError as exc:
        raise AdapterError(f"warehouse metadata schema invalid: {path}: {exc}") from exc

    nodes: list[Node] = []
    for table in document.tables:
        qualified = _table_qualified_name(table)
        binding = PhysicalBinding(
            warehouse=document.warehouse or warehouse_name,
            database=table.database,
            schema=table.schema_name,
            table=table.name,
        )
        table_node = Node(
            id=table_id(qualified),
            kind="table",
            name=table.name,
            qualified_name=qualified,
            schema=table.schema_name,
            evidence=[
                Evidence(
                    file=str(path),
                    expression=qualified,
                    confidence="high",
                )
            ],
            derivation=DerivationState(
                status="complete",
                confidence="high",
                source="information_schema",
            ),
            bindings=[binding],
            aspects={
                "warehouse_metadata": {
                    "database": table.database,
                    "schema": table.schema_name,
                }
            },
        )
        nodes.append(table_node)
        for column in table.columns:
            column_binding = PhysicalBinding(
                warehouse=document.warehouse or warehouse_name,
                database=table.database,
                schema=table.schema_name,
                table=table.name,
                column=column.name,
            )
            nodes.append(
                Node(
                    id=column_id(qualified, column.name),
                    kind="column",
                    name=column.name,
                    qualified_name=f"{qualified}.{column.name}",
                    schema=table.schema_name,
                    evidence=[
                        Evidence(
                            file=str(path),
                            expression=f"{qualified}.{column.name}",
                            confidence="high",
                        )
                    ],
                    derivation=DerivationState(
                        status="complete",
                        confidence="high",
                        source="information_schema",
                    ),
                    bindings=[column_binding],
                    aspects={
                        "warehouse_metadata": {
                            "data_type": column.data_type,
                            "nullable": column.nullable,
                            "ordinal_position": column.ordinal_position,
                            "comment": column.comment,
                        }
                    },
                )
            )

    return CatalogArtifact(nodes=nodes, edges=[], warnings=[])


def _table_qualified_name(table: WarehouseMetadataTable) -> str:
    parts = [part for part in (table.database, table.schema_name, table.name) if part]
    if len(parts) == 1:
        return parts[0]
    if table.schema_name:
        return f"{table.schema_name}.{table.name}"
    return table.name
