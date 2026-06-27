"""PBIR report definition parsing for visual bindings."""

from __future__ import annotations

import base64
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

from .errors import PowerBIStructureError
from .models import VisualBinding


@dataclass
class ParsedReport:
    report_name: str
    pages: dict[str, dict[str, Any]] = field(default_factory=dict)
    bindings: list[VisualBinding] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def parse_report_folder(report_path: str) -> ParsedReport:
    root = Path(report_path)
    definition = root / "definition"
    if not definition.is_dir():
        raise PowerBIStructureError(f"Report missing definition folder: {report_path}")

    report_name = root.name.removesuffix(".Report")
    result = ParsedReport(report_name=report_name)

    report_json = definition / "report.json"
    if report_json.is_file():
        payload = _load_json_file(report_json)
        result.bindings.extend(_parse_legacy_report(payload, report_name))

    pages_dir = definition / "pages"
    if pages_dir.is_dir():
        pages_manifest = pages_dir / "pages.json"
        if pages_manifest.is_file():
            manifest = _load_json_file(pages_manifest)
            for page_id in manifest.get("pageOrder", []) or []:
                result.pages.setdefault(page_id, {"page_id": page_id})

        for visual_file in pages_dir.rglob("visual.json"):
            page_id = visual_file.parent.name
            page_info = result.pages.setdefault(page_id, {"page_id": page_id})
            payload = _load_json_file(visual_file)
            result.bindings.extend(
                _parse_visual_payload(
                    payload,
                    report_name=report_name,
                    page_id=page_id,
                    page_info=page_info,
                )
            )

    pbir_file = definition / "report.pbir"
    if pbir_file.is_file():
        raw = _load_json_file(pbir_file)
        _, decoded = _decode_report_parts(raw)
        for path, payload in decoded.items():
            if path.startswith("definition/pages/") and path.endswith("/visual.json"):
                page_id = path.split("/")[2]
                page_info = result.pages.setdefault(page_id, {"page_id": page_id})
                if isinstance(payload, dict):
                    result.bindings.extend(
                        _parse_visual_payload(
                            payload,
                            report_name=report_name,
                            page_id=page_id,
                            page_info=page_info,
                        )
                    )

    return result


def _load_json_file(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise PowerBIStructureError(f"Invalid report JSON: {path}") from exc


def _decode_report_parts(
    raw_definition: dict[str, Any],
) -> tuple[str | None, dict[str, Any]]:
    definition = raw_definition.get("definition", raw_definition) or {}
    fmt = definition.get("format")
    decoded: dict[str, Any] = {}
    for part in definition.get("parts", []) or []:
        path = part.get("path")
        if not path:
            continue
        payload = part.get("payload", "")
        payload_type = part.get("payloadType")
        if payload_type == "InlineBase64":
            padding = "=" * (-len(payload) % 4)
            try:
                payload = base64.b64decode(f"{payload}{padding}").decode("utf-8")
            except (ValueError, UnicodeDecodeError) as exc:
                raise PowerBIStructureError(
                    f"Invalid base64 report payload in {path!s}"
                ) from exc
        decoded[path] = _json_or_text(payload)
    return fmt, decoded


def _json_or_text(payload: str | None) -> Any:
    if payload is None:
        return None
    try:
        return json.loads(payload)
    except json.JSONDecodeError:
        return payload


def _parse_legacy_report(
    payload: dict[str, Any], report_name: str
) -> list[VisualBinding]:
    bindings: list[VisualBinding] = []
    for index, section in enumerate(payload.get("sections") or []):
        if not isinstance(section, dict):
            continue
        page_id = section.get("name") or f"section-{index}"
        for visual_index, container in enumerate(section.get("visualContainers") or []):
            if not isinstance(container, dict):
                continue
            config = container.get("config")
            if isinstance(config, str):
                config = _json_or_text(config)
            if not isinstance(config, dict):
                continue
            visual_id = config.get("name") or f"{page_id}-visual-{visual_index}"
            single_visual = config.get("singleVisual") or {}
            visual_payload = {
                "name": visual_id,
                "visual": single_visual,
            }
            bindings.extend(
                _parse_visual_payload(
                    visual_payload,
                    report_name=report_name,
                    page_id=page_id,
                    page_info={"page_id": page_id},
                )
            )
    return bindings


def _parse_visual_payload(
    payload: dict[str, Any],
    *,
    report_name: str,
    page_id: str,
    page_info: dict[str, Any],
) -> list[VisualBinding]:
    visual_root = payload.get("visual", {}) or {}
    visual_id = payload.get("name") or page_info.get("page_id", page_id)
    visual_type = visual_root.get("visualType")
    bindings: list[VisualBinding] = []
    source_alias_map: dict[str, str] = {}

    for _path, node in _walk(payload):
        if isinstance(node, list):
            for item in node:
                if isinstance(item, dict):
                    alias = item.get("Name")
                    entity = item.get("Entity")
                    if isinstance(alias, str) and isinstance(entity, str):
                        source_alias_map[alias] = entity

    for path, node in _walk(payload):
        if not isinstance(node, dict):
            continue
        candidate = node.get("field") if isinstance(node.get("field"), dict) else node

        measure = candidate.get("Measure") if isinstance(candidate, dict) else None
        if isinstance(measure, dict) and measure.get("Property"):
            bindings.append(
                VisualBinding(
                    visual_id=visual_id,
                    page_id=page_id,
                    visual_type=visual_type,
                    table_name=_source_entity(
                        measure.get("Expression", {}), source_alias_map
                    ),
                    field_name=str(measure.get("Property")),
                    field_kind="measure",
                    role=_role_from_path(path, is_measure=True),
                )
            )

        column = candidate.get("Column") if isinstance(candidate, dict) else None
        if isinstance(column, dict) and column.get("Property"):
            bindings.append(
                VisualBinding(
                    visual_id=visual_id,
                    page_id=page_id,
                    visual_type=visual_type,
                    table_name=_source_entity(
                        column.get("Expression", {}), source_alias_map
                    ),
                    field_name=str(column.get("Property")),
                    field_kind="column",
                    role=_role_from_path(path, is_measure=False),
                )
            )

    return bindings


def _walk(
    value: Any, path: tuple[str, ...] = ()
) -> Iterable[tuple[tuple[str, ...], Any]]:
    yield path, value
    if isinstance(value, dict):
        for key, child in value.items():
            yield from _walk(child, path + (str(key),))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _walk(child, path + (str(index),))


def _source_entity(expression: dict[str, Any], alias_map: dict[str, str]) -> str | None:
    source_ref = expression.get("SourceRef") or {}
    entity = source_ref.get("Entity")
    if isinstance(entity, str) and entity:
        return entity
    source = source_ref.get("Source")
    if isinstance(source, str):
        return alias_map.get(source)
    return None


def _role_from_path(path: tuple[str, ...], *, is_measure: bool) -> str:
    measure_roles = {"y", "values", "value", "series", "legend", "tooltips", "tooltip"}
    for part in reversed(path):
        key = part.lower()
        if is_measure and key in measure_roles:
            return "primary" if key in {"y", "values", "value"} else "secondary"
        if not is_measure and key in {"filters", "filter", "slicer"}:
            return "filter"
    return "primary" if is_measure else "dimension"
