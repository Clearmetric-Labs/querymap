"""sqlglot parsing helpers for clearmetric-core."""

from __future__ import annotations

from dataclasses import dataclass
from typing import cast

import sqlglot
from sqlglot import exp

from .ast_utils import SqlglotExpression, is_sqlglot_expression
from .errors import QueryMapContractError, QueryMapParseError


@dataclass(frozen=True)
class ParsedStatement:
    statement: SqlglotExpression
    root_expression: SqlglotExpression
    dialect: str


def parse_statement(sql: str, *, dialect: str) -> ParsedStatement:
    """Parse exactly one SQL statement into a supported AST."""
    cleaned = (sql or "").strip()
    if not cleaned:
        raise QueryMapParseError("SQL input is empty.")

    try:
        statements = [
            stmt for stmt in sqlglot.parse(cleaned, read=dialect) if stmt is not None
        ]
    except Exception as exc:
        raise QueryMapParseError(
            f"Failed to parse SQL with dialect {dialect!r}: {exc}"
        ) from exc

    if not statements:
        raise QueryMapParseError("SQL input produced no parseable statements.")
    if len(statements) != 1:
        raise QueryMapContractError(
            "clearmetric-core accepts exactly one SQL statement per invocation."
        )

    statement = cast(SqlglotExpression, statements[0])
    root_expression = _unwrap_root_expression(statement)
    if not isinstance(root_expression, exp.Query):
        raise QueryMapContractError(
            "clearmetric-core supports exactly one SELECT, INSERT ... SELECT, or CREATE ... AS SELECT statement per invocation."
        )
    return ParsedStatement(
        statement=statement, root_expression=root_expression, dialect=dialect
    )


def _unwrap_root_expression(statement: SqlglotExpression) -> SqlglotExpression:
    """Return the query-like root expression used for structure mapping."""
    if isinstance(statement, exp.Create):
        expression = statement.args.get("expression")
        if is_sqlglot_expression(expression):
            return expression

    if isinstance(statement, exp.Insert):
        expression = statement.args.get("expression")
        if is_sqlglot_expression(expression):
            return expression

    return statement
