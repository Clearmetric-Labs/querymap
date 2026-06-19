"""Relation discovery and usage extraction for querymap."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from sqlglot import exp

from .ast_utils import (
    cte_name,
    has_join_ancestor,
    iter_ctes,
    iter_table_nodes,
    iter_table_nodes_skipping_ctes,
    qualified_table_name,
    table_schema_name,
)
from .models import Relation, RelationUsage


@dataclass(frozen=True)
class RelationExtraction:
    relations: list[Relation]
    relation_usages: list[RelationUsage]
    cte_relations: dict[str, Relation]
    table_relations: dict[str, Relation]


def extract_relations(root_expression: exp.Expression, *, dialect: str) -> RelationExtraction:
    """Extract canonical relations and relation usages from the parsed query."""
    cte_relations = _extract_cte_relations(root_expression)
    table_relations: dict[str, Relation] = {}
    relation_usages: list[RelationUsage] = []

    for cte in iter_ctes(root_expression):
        for table in iter_table_nodes(cte.this):
            relation = _resolve_relation(table, cte_relations=cte_relations, table_relations=table_relations)
            if relation is None:
                continue
            relation_usages.append(
                _build_usage(
                    relation_id=relation.id,
                    table=table,
                    context="join" if has_join_ancestor(table, stop_node=cte.this) else "cte_body",
                    dialect=dialect,
                )
            )

    for table in iter_table_nodes_skipping_ctes(root_expression):
        relation = _resolve_relation(table, cte_relations=cte_relations, table_relations=table_relations)
        if relation is None:
            continue
        context = "join" if has_join_ancestor(table, stop_node=root_expression) else "from"
        relation_usages.append(
            _build_usage(
                relation_id=relation.id,
                table=table,
                context=context,
                dialect=dialect,
            )
        )

    relations = sorted(
        [*table_relations.values(), *cte_relations.values()],
        key=lambda relation: relation.id,
    )

    return RelationExtraction(
        relations=relations,
        relation_usages=_dedupe_usages(relation_usages),
        cte_relations=cte_relations,
        table_relations=table_relations,
    )


def _extract_cte_relations(root_expression: exp.Expression) -> dict[str, Relation]:
    relations: dict[str, Relation] = {}
    for cte in iter_ctes(root_expression):
        name = cte_name(cte)
        if not name:
            continue
        relation = Relation(
            id=f"cte:{name.lower()}",
            kind="cte",
            name=name,
        )
        relations[name.lower()] = relation
    return relations


def _resolve_relation(
    table: exp.Table,
    *,
    cte_relations: dict[str, Relation],
    table_relations: dict[str, Relation],
) -> Relation | None:
    table_name = str(table.name or "").strip()
    if not table_name:
        return None

    cte_relation = cte_relations.get(table_name.lower())
    if cte_relation is not None:
        return cte_relation

    qualified_name = qualified_table_name(table)
    key = qualified_name.lower()
    relation = table_relations.get(key)
    if relation is None:
        schema = table_schema_name(table)
        relation = Relation(
            id=f"table:{key}",
            kind="table",
            name=table_name,
            qualified_name=qualified_name,
            schema=schema,
        )
        table_relations[key] = relation
    return relation


def _build_usage(
    *,
    relation_id: str,
    table: exp.Table,
    context: str,
    dialect: str,
) -> RelationUsage:
    alias = str(table.alias or "").strip() or None
    sql = table.sql(dialect=dialect)
    return RelationUsage(
        relation_id=relation_id,
        alias=alias,
        context=context,  # type: ignore[arg-type]
        sql=sql,
        normalized_sql=sql,
    )


def _dedupe_usages(usages: Iterable[RelationUsage]) -> list[RelationUsage]:
    seen: set[tuple[str, str | None, str, str]] = set()
    deduped: list[RelationUsage] = []
    for usage in usages:
        key = (usage.relation_id, usage.alias, usage.context, usage.sql)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(usage)
    return deduped
