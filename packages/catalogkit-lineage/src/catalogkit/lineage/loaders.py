"""Project input loaders for catalogkit-lineage."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from catalogkit.core import normalize_identifier

from .errors import LineageInputError
from .sql_analyzer import list_table_references

ProjectDatasetKind = Literal["local", "root"]
InputKind = Literal["dbt_manifest", "sql_folder"]


@dataclass(frozen=True)
class ProjectDataset:
    name: str
    kind: ProjectDatasetKind
    sql: str | None
    dependency_names: tuple[str, ...]
    declared_columns: tuple[str, ...]
    evidence_file: str | None


@dataclass(frozen=True)
class ProjectInput:
    input_kind: InputKind
    label: str
    datasets: dict[str, ProjectDataset]

    def local_dataset_names(self) -> set[str]:
        return {
            dataset.name
            for dataset in self.datasets.values()
            if dataset.kind == "local"
        }

    def root_schema(self) -> dict[str, dict[str, str]]:
        schema: dict[str, dict[str, str]] = {}
        for dataset in self.datasets.values():
            if dataset.kind != "root" or not dataset.declared_columns:
                continue
            schema[dataset.name] = {
                column_name: "text" for column_name in dataset.declared_columns
            }
        return schema

    def sources_for(self, dataset_name: str) -> dict[str, str]:
        local_names = self.local_dataset_names()
        visited: set[str] = set()
        stack = list(self.datasets[dataset_name].dependency_names)
        while stack:
            dependency_name = stack.pop()
            if dependency_name not in local_names or dependency_name in visited:
                continue
            visited.add(dependency_name)
            stack.extend(self.datasets[dependency_name].dependency_names)
        return {
            dependency_name: self.datasets[dependency_name].sql or ""
            for dependency_name in sorted(visited)
        }


def load_project(path: str | Path, *, dialect: str) -> ProjectInput:
    target = Path(path).expanduser().resolve()
    if not target.exists():
        raise LineageInputError(f"Project input does not exist: {target}")
    if target.is_file():
        if target.name != "manifest.json":
            raise LineageInputError(
                "catalogkit-lineage file input must be a dbt manifest.json."
            )
        return _load_manifest_project(target)
    if target.is_dir():
        return _load_sql_folder_project(target, dialect=dialect)
    raise LineageInputError(f"Unsupported project input path: {target}")


def _load_manifest_project(path: Path) -> ProjectInput:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise LineageInputError(f"Manifest is not valid JSON: {path}") from exc
    raw_nodes = payload.get("nodes")
    if not isinstance(raw_nodes, dict):
        raise LineageInputError(f"Manifest is missing a nodes object: {path}")

    datasets: dict[str, ProjectDataset] = {}
    for node_payload in raw_nodes.values():
        if not isinstance(node_payload, dict):
            raise LineageInputError(
                f"Manifest contains a non-object node payload: {path}"
            )
        resource_type = str(node_payload.get("resource_type") or "").strip().lower()
        name = str(node_payload.get("name") or "").strip()
        if not name:
            continue

        if resource_type == "model":
            sql = _read_compiled_sql(path, node_payload)
            depends_on: list[str] = []
            for dependency in node_payload.get("depends_on", {}).get("nodes", []):
                normalized_dependency = _normalize_dependency_name(dependency)
                if normalized_dependency:
                    depends_on.append(normalized_dependency)
            datasets[name] = ProjectDataset(
                name=name,
                kind="local",
                sql=sql,
                dependency_names=tuple(depends_on),
                declared_columns=_columns_from_manifest_node(node_payload),
                evidence_file=_compiled_path_label(node_payload),
            )
        elif resource_type in {"seed", "source"}:
            datasets[name] = ProjectDataset(
                name=name,
                kind="root",
                sql=None,
                dependency_names=(),
                declared_columns=_columns_from_manifest_node(node_payload),
                evidence_file=None,
            )

    if not datasets:
        raise LineageInputError(f"Manifest produced no usable datasets: {path}")

    project_name = str(payload.get("metadata", {}).get("project_name") or "").strip()
    label = project_name or path.parent.name
    return ProjectInput(input_kind="dbt_manifest", label=label, datasets=datasets)


def _read_compiled_sql(manifest_path: Path, node_payload: dict) -> str:
    compiled_code = str(node_payload.get("compiled_code") or "").strip()
    if compiled_code:
        return compiled_code
    compiled_sql = str(node_payload.get("compiled_sql") or "").strip()
    if compiled_sql:
        return compiled_sql

    compiled_path = str(node_payload.get("compiled_path") or "").strip()
    if compiled_path:
        candidate = _resolve_manifest_relative_path(manifest_path, compiled_path)
        if not candidate.is_file():
            raise LineageInputError(
                f"Manifest compiled_path does not exist for {node_payload.get('name')!r}: {candidate}"
            )
        sql = candidate.read_text(encoding="utf-8").strip()
        if sql:
            return sql

    raise LineageInputError(
        f"Manifest model {node_payload.get('name')!r} is missing compiled SQL."
    )


def _compiled_path_label(node_payload: dict) -> str | None:
    compiled_path = str(node_payload.get("compiled_path") or "").strip()
    if compiled_path:
        return compiled_path
    name = str(node_payload.get("name") or "").strip()
    return f"{name}.sql" if name else None


def _resolve_manifest_relative_path(manifest_path: Path, relative_path: str) -> Path:
    manifest_root = manifest_path.parent.resolve()
    candidate = (manifest_root / relative_path).resolve()
    if manifest_root == candidate or manifest_root not in candidate.parents:
        raise LineageInputError(
            f"Manifest compiled_path escapes the manifest directory: {relative_path!r}"
        )
    return candidate


def _columns_from_manifest_node(node_payload: dict) -> tuple[str, ...]:
    columns = node_payload.get("columns", {})
    if not isinstance(columns, dict):
        return ()
    return tuple(
        str(column_payload.get("name") or "").strip()
        for column_payload in columns.values()
        if str(column_payload.get("name") or "").strip()
    )


def _normalize_dependency_name(unique_id: str) -> str | None:
    parts = str(unique_id or "").strip().split(".")
    if len(parts) < 3:
        return None
    return parts[-1]


def _load_sql_folder_project(path: Path, *, dialect: str) -> ProjectInput:
    sql_files = sorted(path.rglob("*.sql"))
    if not sql_files:
        raise LineageInputError(f"SQL folder contains no .sql files: {path}")

    datasets: dict[str, ProjectDataset] = {}
    raw_sql_by_name: dict[str, str] = {}
    for sql_file in sql_files:
        relative_parts = sql_file.relative_to(path).with_suffix("").parts
        dataset_name = normalize_identifier(".".join(relative_parts))
        if dataset_name in datasets:
            raise LineageInputError(
                f"SQL folder produced duplicate dataset name {dataset_name!r}."
            )
        sql = sql_file.read_text(encoding="utf-8").strip()
        if not sql:
            raise LineageInputError(f"SQL file is empty: {sql_file}")
        raw_sql_by_name[dataset_name] = sql
        datasets[dataset_name] = ProjectDataset(
            name=dataset_name,
            kind="local",
            sql=sql,
            dependency_names=(),
            declared_columns=(),
            evidence_file=str(sql_file.relative_to(path)),
        )

    local_names = set(raw_sql_by_name)
    for dataset_name, sql in raw_sql_by_name.items():
        try:
            dependency_names = sorted(
                {
                    normalize_identifier(reference)
                    for reference in list_table_references(sql, dialect=dialect)
                    if normalize_identifier(reference) in local_names
                }
            )
        except LineageInputError:
            dependency_names = []
        current = datasets[dataset_name]
        datasets[dataset_name] = ProjectDataset(
            name=current.name,
            kind=current.kind,
            sql=current.sql,
            dependency_names=tuple(dependency_names),
            declared_columns=current.declared_columns,
            evidence_file=current.evidence_file,
        )

    return ProjectInput(
        input_kind="sql_folder",
        label=path.name,
        datasets=datasets,
    )
