"""Public API for querymap."""

from __future__ import annotations

from .build import build_query_map_from_parsed
from .models import QueryMap
from .parser import parse_statement
from .render.json import render_json
from .render.text import render_text


def build_query_map(
    sql: str,
    *,
    dialect: str,
) -> QueryMap:
    """Build the public query artifact for one SQL statement."""
    parsed = parse_statement(sql, dialect=dialect)
    return build_query_map_from_parsed(parsed)


__all__ = [
    "build_query_map",
    "render_json",
    "render_text",
]
