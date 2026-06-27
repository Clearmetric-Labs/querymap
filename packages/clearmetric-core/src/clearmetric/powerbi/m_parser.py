"""Power Query M source extraction via pbi_parsers."""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from pbi_parsers.pq import to_ast
from pbi_parsers.pq.exprs import (
    FunctionExpression,
    IdentifierExpression,
    LiteralStringExpression,
    RecordExpression,
    RowExpression,
    RowIndexExpression,
    StatementExpression,
    VariableExpression,
)

from .errors import PowerBIStructureError
from .models import MSourceReference

DATABASE_CONNECTORS = {
    "Sql.Database",
    "Sql.Databases",
    "PostgreSQL.Database",
    "Oracle.Database",
    "MySQL.Database",
    "Snowflake.Databases",
    "GoogleBigQuery.Database",
    "AmazonRedshift.Database",
    "Databricks.Catalogs",
    "Teradata.Database",
}


def extract_m_sources(m_expression: str) -> list[MSourceReference]:
    """Extract upstream source references from one M expression."""
    if not m_expression or not m_expression.strip():
        return []

    try:
        ast = to_ast(m_expression)
    except Exception as exc:
        raise PowerBIStructureError(f"Failed to parse M expression: {exc}") from exc

    if not isinstance(ast, StatementExpression):
        return []

    step_map = _build_step_map(ast)
    sources = _extract_from_expression(ast.let_expr, step_map)
    for step_name, step_expr in step_map.items():
        for source in _extract_from_expression(step_expr, step_map):
            sources.append(replace(source, step_name=step_name))
    return _dedupe_sources(sources)


def _build_step_map(ast: StatementExpression) -> dict[str, Any]:
    step_map: dict[str, Any] = {}
    for statement in ast.statements or []:
        if isinstance(statement, VariableExpression):
            step_map[statement.var_name.text_slice.get_text()] = statement.statement
    return step_map


def _extract_from_expression(
    expr: Any,
    step_map: dict[str, Any],
    *,
    seen: set[str] | None = None,
) -> list[MSourceReference]:
    seen = seen or set()
    if expr is None:
        return []

    if isinstance(expr, IdentifierExpression):
        step_name = _identifier_name(expr)
        if not step_name or step_name in seen:
            return []
        seen.add(step_name)
        return _extract_from_expression(step_map.get(step_name), step_map, seen=seen)

    if isinstance(expr, FunctionExpression):
        function_name = _identifier_name(expr.name)
        if not function_name:
            return []
        if function_name in DATABASE_CONNECTORS:
            return _database_sources(function_name, expr, step_map)
        if function_name == "Value.NativeQuery":
            return _native_query_sources(expr, step_map)
        nested: list[MSourceReference] = []
        for arg in expr.args or []:
            nested.extend(_extract_from_expression(arg, step_map, seen=set(seen)))
        return nested

    if isinstance(expr, RowIndexExpression):
        return _navigation_sources(expr, step_map)

    return []


def _database_sources(
    function_name: str,
    expr: FunctionExpression,
    step_map: dict[str, Any],
) -> list[MSourceReference]:
    args = list(expr.args or [])
    server = _resolve_string(args[0], step_map) if args else None
    database = _resolve_string(args[1], step_map) if len(args) > 1 else None
    if function_name == "GoogleBigQuery.Database" and args:
        server = _record_value(args[0], "ProjectId", step_map) or server
    return [
        MSourceReference(
            source_type="database",
            connector=function_name,
            server=server,
            database=database,
        )
    ]


def _native_query_sources(
    expr: FunctionExpression,
    step_map: dict[str, Any],
) -> list[MSourceReference]:
    args = list(expr.args or [])
    if len(args) < 2:
        return []
    upstream = _extract_from_expression(args[0], step_map)
    sql = _resolve_string(args[1], step_map)
    base = (
        upstream[0]
        if upstream
        else MSourceReference(
            source_type="database",
            connector="Value.NativeQuery",
        )
    )
    return [
        replace(
            base,
            connector="Value.NativeQuery",
            native_sql=sql,
        )
    ]


def _navigation_sources(
    expr: RowIndexExpression,
    step_map: dict[str, Any],
) -> list[MSourceReference]:
    base_step, navigation = _navigation_parts(expr)
    upstream = (
        _extract_from_expression(step_map.get(base_step), step_map) if base_step else []
    )
    if not upstream:
        upstream = [
            MSourceReference(
                source_type="database",
                connector="navigation",
                schema=navigation.get("Schema"),
                table=navigation.get("Item") or navigation.get("Name"),
            )
        ]
    enriched: list[MSourceReference] = []
    for source in upstream:
        enriched.append(
            replace(
                source,
                schema=navigation.get("Schema") or source.schema,
                table=navigation.get("Item") or navigation.get("Name") or source.table,
            )
        )
    return enriched


def _navigation_parts(expr: RowIndexExpression) -> tuple[str | None, dict[str, str]]:
    navigation: dict[str, str] = {}
    base_step: str | None = None
    table_expr = getattr(expr, "table", None)
    if isinstance(table_expr, RowExpression):
        identifier = getattr(table_expr, "table", None)
        if isinstance(identifier, IdentifierExpression):
            base_step = _identifier_name(identifier)
        record_expr = getattr(table_expr, "indexer", None)
        if isinstance(record_expr, RecordExpression):
            for key_expr, value_expr in record_expr.args or []:
                key = _identifier_name(key_expr)
                value = _resolve_string(value_expr, {})
                if key and value:
                    navigation[key] = value
    return base_step, navigation


def _identifier_name(expr: Any) -> str | None:
    if isinstance(expr, IdentifierExpression):
        return expr.name()
    return None


def _resolve_string(
    expr: Any, step_map: dict[str, Any], seen: set[str] | None = None
) -> str | None:
    seen = seen or set()
    if isinstance(expr, LiteralStringExpression):
        return expr.value.text_slice.get_text().strip('"')
    if isinstance(expr, IdentifierExpression):
        step_name = _identifier_name(expr)
        if not step_name or step_name in seen:
            return None
        seen.add(step_name)
        return _resolve_string(step_map.get(step_name), step_map, seen)
    return None


def _record_value(expr: Any, key_name: str, step_map: dict[str, Any]) -> str | None:
    if not isinstance(expr, RecordExpression):
        return None
    for key_expr, value_expr in expr.args or []:
        if _identifier_name(key_expr) == key_name:
            return _resolve_string(value_expr, step_map)
    return None


def _dedupe_sources(sources: list[MSourceReference]) -> list[MSourceReference]:
    seen: set[tuple[Any, ...]] = set()
    deduped: list[MSourceReference] = []
    for source in sources:
        key = (
            source.connector,
            source.server,
            source.database,
            source.schema,
            source.table,
            source.native_sql,
            source.step_name,
        )
        if key in seen:
            continue
        seen.add(key)
        deduped.append(source)
    return deduped
