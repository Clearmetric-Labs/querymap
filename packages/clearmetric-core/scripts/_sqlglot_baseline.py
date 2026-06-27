from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sqlglot.lineage import Node as LineageNode
from sqlglot.lineage import lineage


@dataclass(frozen=True)
class FixtureNode:
    unique_id: str
    resource_type: str
    name: str
    depends_on: tuple[str, ...]
    columns: tuple[str, ...]


def load_fixture(
    manifest_path: Path,
) -> tuple[dict[str, Any], dict[str, FixtureNode], dict[str, str]]:
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    nodes: dict[str, FixtureNode] = {}
    sql_by_name: dict[str, str] = {}
    for unique_id, node_payload in payload["nodes"].items():
        depends_on = tuple(node_payload.get("depends_on", {}).get("nodes", []))
        columns = tuple(
            column_payload["name"]
            for column_payload in node_payload.get("columns", {}).values()
        )
        nodes[unique_id] = FixtureNode(
            unique_id=unique_id,
            resource_type=node_payload["resource_type"],
            name=node_payload["name"],
            depends_on=depends_on,
            columns=columns,
        )
        compiled_code = str(node_payload.get("compiled_code") or "").strip()
        compiled_sql = str(node_payload.get("compiled_sql") or "").strip()
        compiled_path = str(node_payload.get("compiled_path") or "").strip()
        if compiled_code:
            sql_by_name[node_payload["name"]] = compiled_code
        elif compiled_sql:
            sql_by_name[node_payload["name"]] = compiled_sql
        elif compiled_path:
            sql_by_name[node_payload["name"]] = (
                manifest_path.parent / compiled_path
            ).read_text(encoding="utf-8")
    return payload, nodes, sql_by_name


def build_sources_by_name(
    nodes: dict[str, FixtureNode], sql_by_name: dict[str, str]
) -> dict[str, str]:
    return {
        node.name: sql_by_name[node.name]
        for node in nodes.values()
        if node.resource_type == "model" and node.name in sql_by_name
    }


def build_root_schema(nodes: dict[str, FixtureNode]) -> dict[str, dict[str, str]]:
    schema: dict[str, dict[str, str]] = {}
    for node in nodes.values():
        if node.resource_type not in {"seed", "source"}:
            continue
        schema[node.name] = {column_name: "text" for column_name in node.columns}
    return schema


def build_upstream_model_names(
    nodes: dict[str, FixtureNode], *, target_unique_id: str
) -> set[str]:
    discovered: set[str] = set()
    stack = list(nodes[target_unique_id].depends_on)
    while stack:
        dependency_unique_id = stack.pop()
        dependency_node = nodes.get(dependency_unique_id)
        if dependency_node is None or dependency_node.resource_type != "model":
            continue
        if dependency_node.name in discovered:
            continue
        discovered.add(dependency_node.name)
        stack.extend(dependency_node.depends_on)
    return discovered


def sources_for_target(
    nodes: dict[str, FixtureNode],
    sources_by_name: dict[str, str],
    *,
    target_unique_id: str,
) -> dict[str, str]:
    allowed_names = build_upstream_model_names(nodes, target_unique_id=target_unique_id)
    return {
        source_name: sql
        for source_name, sql in sources_by_name.items()
        if source_name in allowed_names
    }


def build_raw_downstream_index(
    *,
    nodes: dict[str, FixtureNode],
    sql_by_name: dict[str, str],
    root_schema: dict[str, dict[str, str]],
    sources_by_name: dict[str, str],
    dialect: str,
) -> dict[str, list[str]]:
    downstream: dict[str, set[str]] = {}
    for node in nodes.values():
        if node.resource_type != "model" or node.name not in sql_by_name:
            continue
        for column_name in node.columns:
            root = lineage(
                column_name,
                sql_by_name[node.name],
                schema=root_schema,
                sources=sources_for_target(
                    nodes,
                    sources_by_name,
                    target_unique_id=node.unique_id,
                ),
                dialect=dialect,
            )
            for leaf_ref in collect_leaf_refs(root):
                downstream.setdefault(leaf_ref, set()).add(f"{node.name}.{column_name}")
    return {
        key: sorted(values)
        for key, values in sorted(downstream.items(), key=lambda item: item[0])
    }


def collect_leaf_refs(node: LineageNode) -> set[str]:
    if not node.downstream:
        return {node.name}
    refs: set[str] = set()
    for child in node.downstream:
        refs.update(collect_leaf_refs(child))
    return refs
