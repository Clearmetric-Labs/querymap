"""Cross-graph interop: FQN matching, alias maps, and match status."""

from __future__ import annotations

from .errors import CanonicalIdError
from .ids import normalize_identifier, split_qualified_identifier
from .models import CatalogArtifact, MatchStatus, Node, PhysicalBinding, Warning

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


def physical_binding_key(binding: PhysicalBinding) -> tuple[str, str, str, str, str]:
    """Normalize a physical binding into a hashable key."""
    return (
        binding.warehouse or "",
        binding.database or "",
        binding.schema_name or "",
        binding.table or "",
        binding.column or "",
    )


def _is_warehouse_native(node: Node) -> bool:
    return (
        node.derivation is not None and node.derivation.source == "information_schema"
    )


def _has_bindings(node: Node) -> bool:
    return bool(node.bindings)


def _warehouse_column_index(
    warehouse_artifact: CatalogArtifact,
) -> dict[tuple[str, str], Node]:
    index: dict[tuple[str, str], Node] = {}
    table_ids = {node.id for node in warehouse_artifact.nodes if node.kind == "table"}
    for node in warehouse_artifact.nodes:
        if node.kind != "column" or not node.qualified_name:
            continue
        parts = split_qualified_identifier(node.qualified_name)
        if len(parts) < 2:
            continue
        parent_qn = ".".join(parts[:-1])
        parent_id = f"table:{normalize_fqn_for_matching(parent_qn)}"
        if parent_id not in table_ids:
            continue
        column_name = parts[-1]
        index[(parent_id, column_name)] = node
    return index


def attach_warehouse_bindings(
    *,
    merged: CatalogArtifact,
    warehouse_artifact: CatalogArtifact,
    alias_map: AliasMap | None = None,
) -> CatalogArtifact:
    """Attach warehouse physical bindings to lineage nodes without inventing matches."""
    warehouse_table_ids = {
        node.id for node in warehouse_artifact.nodes if node.kind == "table"
    }
    warehouse_nodes = {node.id: node for node in warehouse_artifact.nodes}
    warehouse_columns = _warehouse_column_index(warehouse_artifact)

    new_warnings: list[Warning] = []
    updated_nodes: dict[str, Node] = {node.id: node for node in merged.nodes}
    cleared_binding_ids: set[str] = set()

    for node_id, node in list(updated_nodes.items()):
        if node.kind not in {"table", "column"}:
            continue
        if _is_warehouse_native(node) or _has_bindings(node):
            continue
        if not node.qualified_name:
            new_warnings.append(
                Warning(
                    code="warehouse_bind_unresolved",
                    message=(
                        f"{node.id} has no qualified_name and cannot be bound to "
                        "warehouse metadata"
                    ),
                    subject_id=node.id,
                )
            )
            continue

        if node.kind == "table":
            updated_node, warnings, source_ids = _attach_table_binding(
                node,
                warehouse_table_ids=warehouse_table_ids,
                warehouse_nodes=warehouse_nodes,
                alias_map=alias_map,
            )
        else:
            updated_node, warnings, source_ids = _attach_column_binding(
                node,
                warehouse_table_ids=warehouse_table_ids,
                warehouse_columns=warehouse_columns,
                alias_map=alias_map,
            )
        new_warnings.extend(warnings)
        updated_nodes[node_id] = updated_node
        for source_id in source_ids:
            cleared_binding_ids.add(source_id)

    if cleared_binding_ids:
        for source_id in cleared_binding_ids:
            source = updated_nodes.get(source_id)
            if source is None:
                continue
            updated_nodes[source_id] = source.model_copy(update={"bindings": None})

    final_nodes = list(updated_nodes.values())

    if not new_warnings and not cleared_binding_ids:
        return merged

    return merged.model_copy(
        update={
            "nodes": final_nodes,
            "warnings": [*merged.warnings, *new_warnings],
        }
    )


def _attach_table_binding(
    node: Node,
    *,
    warehouse_table_ids: set[str],
    warehouse_nodes: dict[str, Node],
    alias_map: AliasMap | None,
) -> tuple[Node, list[Warning], list[str]]:
    assert node.qualified_name is not None
    candidates = warehouse_table_fqn_candidates_from_name(node.qualified_name)
    matched_id, status = resolve_table_match(
        candidates,
        warehouse_table_ids,
        alias_map=alias_map,
    )
    if status == "resolved" and matched_id is not None:
        warehouse_node = warehouse_nodes.get(matched_id)
        if warehouse_node and warehouse_node.bindings:
            return (
                node.model_copy(update={"bindings": warehouse_node.bindings}),
                [],
                [matched_id] if matched_id != node.id else [],
            )
    warning_code = (
        "warehouse_bind_ambiguous"
        if status == "ambiguous"
        else "warehouse_bind_unresolved"
    )
    return (
        node,
        [
            Warning(
                code=warning_code,
                message=(
                    f"{node.id} could not be uniquely bound to warehouse metadata "
                    f"(match_status={status})"
                ),
                subject_id=node.id,
            )
        ],
        [],
    )


def _attach_column_binding(
    node: Node,
    *,
    warehouse_table_ids: set[str],
    warehouse_columns: dict[tuple[str, str], Node],
    alias_map: AliasMap | None,
) -> tuple[Node, list[Warning], list[str]]:
    assert node.qualified_name is not None
    parts = split_qualified_identifier(node.qualified_name)
    if len(parts) < 2:
        return (
            node,
            [
                Warning(
                    code="warehouse_bind_unresolved",
                    message=f"{node.id} has invalid column qualified_name for binding",
                    subject_id=node.id,
                )
            ],
            [],
        )

    parent_qn = ".".join(parts[:-1])
    column_name = parts[-1]
    candidates = warehouse_table_fqn_candidates_from_name(parent_qn)
    matched_table_id, table_status = resolve_table_match(
        candidates,
        warehouse_table_ids,
        alias_map=alias_map,
    )
    if table_status != "resolved" or matched_table_id is None:
        warning_code = (
            "warehouse_bind_ambiguous"
            if table_status == "ambiguous"
            else "warehouse_bind_unresolved"
        )
        return (
            node,
            [
                Warning(
                    code=warning_code,
                    message=(
                        f"{node.id} parent table could not be uniquely bound to warehouse "
                        f"metadata (match_status={table_status})"
                    ),
                    subject_id=node.id,
                )
            ],
            [],
        )

    warehouse_column = warehouse_columns.get((matched_table_id, column_name))
    if warehouse_column is None or not warehouse_column.bindings:
        return (
            node,
            [
                Warning(
                    code="warehouse_bind_unresolved",
                    message=(
                        f"{node.id} parent matched {matched_table_id} but column "
                        f"{column_name!r} was not found in warehouse metadata"
                    ),
                    subject_id=node.id,
                )
            ],
            [],
        )

    source_ids = [warehouse_column.id] if warehouse_column.id != node.id else []
    return (
        node.model_copy(update={"bindings": warehouse_column.bindings}),
        [],
        source_ids,
    )


__all__ = [
    "AliasMap",
    "MatchStatus",
    "apply_alias_map",
    "attach_warehouse_bindings",
    "normalize_fqn_for_matching",
    "physical_binding_key",
    "resolve_table_match",
    "warehouse_table_fqn_candidates",
    "warehouse_table_fqn_candidates_from_name",
]
