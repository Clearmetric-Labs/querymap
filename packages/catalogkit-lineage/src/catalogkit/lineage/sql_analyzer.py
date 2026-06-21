"""Small sqlglot helpers local to catalogkit-lineage."""

from __future__ import annotations

from typing import Any

import sqlglot
from catalogkit.core import normalize_identifier, normalize_identifier_part
from sqlglot import exp
from sqlglot.lineage import Node as SqlglotLineageNode

from .errors import LineageContractError, LineageInputError


def parse_single_statement(sql: str, *, dialect: str) -> Any:
    """Parse exactly one SQL statement for lineage package analysis."""
    cleaned = (sql or "").strip()
    if not cleaned:
        raise LineageInputError("SQL input is empty.")

    try:
        statements = [
            statement
            for statement in sqlglot.parse(cleaned, read=dialect)
            if statement is not None
        ]
    except Exception as exc:  # pragma: no cover - exercised by caller failure paths
        raise LineageInputError(
            f"Failed to parse SQL with dialect {dialect!r}: {exc}"
        ) from exc

    if not statements:
        raise LineageInputError("SQL input produced no parseable statements.")
    if len(statements) != 1:
        raise LineageContractError(
            "catalogkit-lineage accepts exactly one SQL statement per project file."
        )
    return statements[0]


def list_table_references(sql: str, *, dialect: str) -> list[str]:
    """Return normalized table references while excluding local CTE names."""
    statement = parse_single_statement(sql, dialect=dialect)
    cte_names = {
        normalize_identifier(cte.alias_or_name)
        for cte in statement.find_all(exp.CTE)
        if cte.alias_or_name
    }
    references: list[str] = []
    seen: set[str] = set()
    for table in statement.find_all(exp.Table):
        reference = normalize_identifier(table.sql(dialect=dialect))
        if reference in cte_names or reference in seen:
            continue
        seen.add(reference)
        references.append(reference)
    return references


def detect_select_star(sql: str, *, dialect: str) -> bool:
    """Return True when the statement includes any star projection."""
    statement = parse_single_statement(sql, dialect=dialect)
    return any(isinstance(node, exp.Star) for node in statement.walk())


def defining_value_expression(root: SqlglotLineageNode) -> Any:
    """Return the shallowest downstream expression that requires value filtering."""
    filter_expr = _value_filter_expression(root)
    if filter_expr is not None:
        return filter_expr
    expression = root.expression
    if expression is not None and hasattr(expression, "args"):
        return _unwrap_alias(expression)
    raise LineageContractError("Lineage root is missing a defining expression.")


def filter_value_lineage_refs(
    root: SqlglotLineageNode,
    selected_refs: set[str],
    *,
    dialect: str,
) -> set[str]:
    """Filter lineage refs down to value-carrying columns only."""
    del dialect  # reserved for future dialect-specific filtering
    filter_expr = _value_filter_expression(root)
    if filter_expr is None:
        return selected_refs
    allowed_refs = {
        normalize_identifier(column.sql())
        for column in _value_columns(filter_expr)
        if _is_qualified_column(column)
    }
    allowed_column_names = {
        normalize_identifier_part(column.name)
        for column in _value_columns(filter_expr)
        if column.name
    }
    return {
        ref
        for ref in selected_refs
        if ref != "*"
        if _matches_value_ref(
            ref,
            allowed_refs=allowed_refs,
            allowed_column_names=allowed_column_names,
        )
    }


def _value_filter_expression(root: SqlglotLineageNode) -> Any:
    """Return the shallowest value-defining expression that needs predicate filtering."""
    best: Any = None
    best_depth = float("inf")

    def visit(node: SqlglotLineageNode, depth: int) -> None:
        nonlocal best, best_depth
        expression = node.expression
        if expression is None or not hasattr(expression, "args"):
            return
        unwrapped = _unwrap_alias(expression)
        if _is_value_defining_expression(expression) and _needs_value_filter(unwrapped):
            if depth < best_depth:
                best = expression
                best_depth = depth
        for child in node.downstream:
            visit(child, depth + 1)

    visit(root, 0)
    return _unwrap_alias(best) if best is not None else None


def _value_columns(node: Any) -> set[exp.Column]:
    columns: set[exp.Column] = set()
    if node is None or not hasattr(node, "args"):
        return columns
    if isinstance(node, exp.Column):
        columns.add(node)
        return columns
    if isinstance(node, exp.Case):
        for branch in node.args.get("ifs") or []:
            if isinstance(branch, exp.If):
                columns.update(_value_columns(branch.args.get("true")))
            else:
                columns.update(_value_columns(branch))
        columns.update(_value_columns(node.args.get("default")))
        return columns
    if isinstance(node, exp.If):
        columns.update(_value_columns(node.args.get("true")))
        columns.update(_value_columns(node.args.get("false")))
        return columns
    if isinstance(node, exp.Join):
        columns.update(_value_columns(node.args.get("this")))
        return columns
    if isinstance(node, (exp.Where, exp.Having)):
        return columns
    if isinstance(node, exp.Window):
        columns.update(_value_columns(node.args.get("this")))
        return columns
    for child in node.args.values():
        if isinstance(child, list):
            for item in child:
                columns.update(_value_columns(item))
            continue
        columns.update(_value_columns(child))
    return columns


def _is_qualified_column(node: exp.Column) -> bool:
    table = node.args.get("table")
    return isinstance(table, exp.Identifier) and bool(table.this)


def _matches_value_ref(
    reference: str,
    *,
    allowed_refs: set[str],
    allowed_column_names: set[str],
) -> bool:
    normalized_ref = normalize_identifier(reference)
    if normalized_ref in allowed_refs:
        return True
    parts = normalized_ref.split(".")
    if not parts:
        return False
    return parts[-1] in allowed_column_names


def _needs_value_filter(node: Any) -> bool:
    if node is None or not hasattr(node, "iter_expressions"):
        return False
    if isinstance(node, (exp.Case, exp.Where, exp.Having)):
        return True
    if isinstance(node, exp.Window):
        return bool(node.args.get("partition_by"))
    return any(_needs_value_filter(child) for child in node.iter_expressions())


def _unwrap_alias(node: Any) -> Any:
    if node is None or not hasattr(node, "args"):
        return node
    if isinstance(node, exp.Alias):
        return _unwrap_alias(node.this)
    return node


def _is_value_defining_expression(node: Any) -> bool:
    if node is None or not hasattr(node, "args"):
        return False
    expression = _unwrap_alias(node)
    if isinstance(
        expression,
        (exp.Select, exp.Subquery, exp.Query, exp.Union, exp.Join, exp.Star, exp.Table),
    ):
        return False
    if isinstance(expression, exp.Column):
        return False
    if isinstance(expression, exp.AggFunc):
        return True
    if isinstance(expression, (exp.Case, exp.If, exp.Coalesce, exp.Nullif)):
        return True
    if isinstance(expression, (exp.Add, exp.Sub, exp.Mul, exp.Div, exp.Mod)):
        return True
    if isinstance(expression, exp.Cast):
        return _is_value_defining_expression(expression.this)
    return _needs_value_filter(expression)
