"""CTE and dependency edge extraction for querymap."""

from __future__ import annotations

from dataclasses import dataclass

from sqlglot import exp

from .ast_utils import cte_name, iter_ctes, iter_table_nodes, iter_table_nodes_skipping_ctes, qualified_table_name
from .models import RelationEdge, WarningEntry
from .relations import RelationExtraction


@dataclass(frozen=True)
class DependencyExtraction:
    edges: list[RelationEdge]
    warnings: list[WarningEntry]


def extract_dependency_edges(
    root_expression: exp.Expression,
    *,
    relation_extraction: RelationExtraction,
    dialect: str,
) -> DependencyExtraction:
    """Extract relation-level dependency edges for root query and CTEs."""
    edges: list[RelationEdge] = []
    warnings: list[WarningEntry] = []

    for cte in iter_ctes(root_expression):
        cte_name_value = cte_name(cte)
        if not cte_name_value:
            continue
        source_id = f"cte:{cte_name_value.lower()}"
        for table in iter_table_nodes(cte.this):
            target_id = _resolve_relation_id(table, relation_extraction=relation_extraction)
            if target_id is None:
                continue
            if target_id == source_id:
                warnings.append(
                    WarningEntry(
                        code="unsupported_construct",
                        message=f"Recursive CTE {cte_name_value!r} is not modeled explicitly in the MVP.",
                        location=table.sql(dialect=dialect),
                    )
                )
                continue
            edges.append(
                RelationEdge(
                    kind="depends_on",
                    source_id=source_id,
                    target_id=target_id,
                    label="depends_on",
                    confidence="high",
                    sql=table.sql(dialect=dialect),
                    normalized_sql=table.sql(dialect=dialect),
                )
            )

    for table in iter_table_nodes_skipping_ctes(root_expression):
        target_id = _resolve_relation_id(table, relation_extraction=relation_extraction)
        if target_id is None:
            continue
        edges.append(
            RelationEdge(
                kind="depends_on",
                source_id="query:root",
                target_id=target_id,
                label="depends_on",
                confidence="high",
                sql=table.sql(dialect=dialect),
                normalized_sql=table.sql(dialect=dialect),
            )
        )

    return DependencyExtraction(edges=_dedupe_edges(edges), warnings=_dedupe_warnings(warnings))


def _resolve_relation_id(
    table: exp.Table,
    *,
    relation_extraction: RelationExtraction,
) -> str | None:
    name = str(table.name or "").strip()
    if not name:
        return None

    cte_relation = relation_extraction.cte_relations.get(name.lower())
    if cte_relation is not None:
        return cte_relation.id

    qualified = qualified_table_name(table).lower()
    table_relation = relation_extraction.table_relations.get(qualified)
    if table_relation is None:
        return None
    return table_relation.id


def _dedupe_edges(edges: list[RelationEdge]) -> list[RelationEdge]:
    seen: set[tuple[str, str, str | None]] = set()
    deduped: list[RelationEdge] = []
    for edge in edges:
        key = (edge.source_id, edge.target_id, edge.sql)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(edge)
    return deduped


def _dedupe_warnings(warnings: list[WarningEntry]) -> list[WarningEntry]:
    seen: set[tuple[str, str, str | None]] = set()
    deduped: list[WarningEntry] = []
    for warning in warnings:
        key = (warning.code, warning.message, warning.location)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(warning)
    return deduped
