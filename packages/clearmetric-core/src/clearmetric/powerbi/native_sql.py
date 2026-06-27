"""Extract table references from native SQL in M Value.NativeQuery bodies."""

from __future__ import annotations

import re

_NATIVE_SQL_TABLE_PATTERN = re.compile(
    r"(?:from|join)\s+(?:\[?(\w+)\]?\.)?\[?(\w+)\]?",
    re.IGNORECASE,
)


def native_sql_table_refs(sql: str) -> list[tuple[str | None, str]]:
    """
    Best-effort extraction of schema.table references from native SQL text.

    Returns ordered (schema, table) pairs. Used only by clearmetric-core to
    build warehouse FQN candidates via clearmetric-core interop helpers.
    """
    if not sql or not sql.strip():
        return []

    results: list[tuple[str | None, str]] = []
    seen: set[tuple[str | None, str]] = set()
    for match in _NATIVE_SQL_TABLE_PATTERN.finditer(sql):
        if match.group(1):
            schema, table = match.group(1), match.group(2)
        else:
            schema, table = None, match.group(2)
        key = (schema, table.lower())
        if key in seen:
            continue
        seen.add(key)
        results.append(key)
    return results
