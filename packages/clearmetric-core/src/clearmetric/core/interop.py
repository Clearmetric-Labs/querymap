"""Cross-graph interop: FQN matching, alias maps, and match status."""

from __future__ import annotations

from .errors import CanonicalIdError
from .ids import normalize_identifier
from .models import MatchStatus

AliasMap = dict[str, str]


def normalize_fqn_for_matching(value: str) -> str:
    """Normalize a fully-qualified name for case-insensitive cross-graph comparison."""
    return normalize_identifier(value)


def warehouse_table_fqn_candidates(
    *,
    database: str | None = None,
    schema: str | None = None,
    table: str,
) -> list[str]:
    """Build ordered FQN candidates for matching a warehouse table reference."""
    if not str(table).strip():
        raise CanonicalIdError(
            "Table name is required to build warehouse FQN candidates."
        )

    parts: list[str] = []
    if database and str(database).strip():
        parts.append(str(database).strip())
    if schema and str(schema).strip():
        parts.append(str(schema).strip())
    parts.append(str(table).strip())

    candidates: list[str] = []
    if len(parts) == 3:
        candidates.append(normalize_fqn_for_matching(".".join(parts)))
    if len(parts) >= 2:
        candidates.append(normalize_fqn_for_matching(".".join(parts[-2:])))
    candidates.append(normalize_fqn_for_matching(parts[-1]))

    seen: set[str] = set()
    ordered: list[str] = []
    for candidate in candidates:
        if candidate in seen:
            continue
        seen.add(candidate)
        ordered.append(candidate)
    return ordered


def warehouse_table_fqn_candidates_from_name(normalized_fqn: str) -> list[str]:
    """Rebuild ordered warehouse FQN candidates from one normalized dotted name."""
    parts = normalized_fqn.split(".")
    if len(parts) == 3:
        return warehouse_table_fqn_candidates(
            database=parts[0],
            schema=parts[1],
            table=parts[2],
        )
    if len(parts) == 2:
        return warehouse_table_fqn_candidates(schema=parts[0], table=parts[1])
    if len(parts) == 1:
        return warehouse_table_fqn_candidates(table=parts[0])
    raise CanonicalIdError(
        f"Cannot derive warehouse FQN candidates from name: {normalized_fqn!r}"
    )


def apply_alias_map(name: str, alias_map: AliasMap | None) -> str:
    """Resolve a name through the alias map, returning normalized form."""
    normalized = normalize_fqn_for_matching(name)
    if not alias_map:
        return normalized
    mapped = alias_map.get(normalized)
    if mapped is None:
        return normalized
    return normalize_fqn_for_matching(mapped)


def resolve_table_match(
    source_candidates: list[str],
    target_table_ids: set[str],
    *,
    alias_map: AliasMap | None = None,
) -> tuple[str | None, MatchStatus]:
    """
    Match source FQN candidates against canonical ``table:`` node IDs.

    Returns the matched ``table:...`` ID and match status.
    """
    if not source_candidates:
        return None, "unresolved"

    target_by_normalized = {
        normalize_fqn_for_matching(tid.removeprefix("table:")): tid
        for tid in target_table_ids
    }

    matches: list[str] = []
    for raw_candidate in source_candidates:
        candidate = apply_alias_map(raw_candidate, alias_map)
        for normalized_target, table_id in target_by_normalized.items():
            if candidate == normalized_target or normalized_target.endswith(
                f".{candidate}"
            ):
                matches.append(table_id)

    unique_matches = sorted(set(matches))
    if len(unique_matches) == 1:
        return unique_matches[0], "resolved"
    if len(unique_matches) > 1:
        return unique_matches[0], "ambiguous"
    return None, "unresolved"


__all__ = [
    "AliasMap",
    "MatchStatus",
    "apply_alias_map",
    "normalize_fqn_for_matching",
    "resolve_table_match",
    "warehouse_table_fqn_candidates",
    "warehouse_table_fqn_candidates_from_name",
]
