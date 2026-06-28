"""Build ClearMetric Core artifacts from discovered Power BI projects."""

from __future__ import annotations

from dataclasses import dataclass

from clearmetric.core import (
    AliasMap,
    CatalogArtifact,
    Edge,
    Evidence,
    Node,
    Warning,
    merge,
    normalize_identifier_parts,
    page_id,
    report_id,
    resolve_table_match,
    table_id,
    visual_id,
    warehouse_table_fqn_candidates,
    warehouse_table_fqn_candidates_from_name,
)

from .errors import PowerBIStructureError
from .m_parser import extract_m_sources
from .models import DiscoveredProject, PowerBIMap, PowerBISummary
from .native_sql import native_sql_table_refs
from .report_parser import parse_report_folder


@dataclass(frozen=True)
class BuiltPowerBI:
    artifact: CatalogArtifact
    summary: PowerBISummary


def build_catalog_artifact_from_project(
    project: DiscoveredProject,
    *,
    alias_map: AliasMap | None = None,
    warehouse_table_ids: set[str] | None = None,
) -> CatalogArtifact:
    return _build_powerbi(
        project,
        alias_map=alias_map,
        warehouse_table_ids=warehouse_table_ids,
    ).artifact


def build_powerbi_map_from_project(
    project: DiscoveredProject,
    *,
    alias_map: AliasMap | None = None,
    warehouse_table_ids: set[str] | None = None,
) -> PowerBIMap:
    built = _build_powerbi(
        project,
        alias_map=alias_map,
        warehouse_table_ids=warehouse_table_ids,
    )
    return PowerBIMap(
        version=built.artifact.version,
        summary=built.summary,
        nodes=built.artifact.nodes,
        edges=built.artifact.edges,
        warnings=built.artifact.warnings,
    )


def merge_with_warehouse(
    powerbi_artifact: CatalogArtifact,
    warehouse_artifact: CatalogArtifact,
    *,
    alias_map: AliasMap | None = None,
) -> CatalogArtifact:
    """Merge Power BI and warehouse artifacts, resolving cross-graph table joins."""
    warehouse_tables = {
        node.id for node in warehouse_artifact.nodes if node.kind == "table"
    }
    enriched = _resolve_cross_graph_edges(powerbi_artifact, warehouse_tables, alias_map)
    return merge(warehouse_artifact, enriched)


def _build_powerbi(
    project: DiscoveredProject,
    *,
    alias_map: AliasMap | None,
    warehouse_table_ids: set[str] | None,
) -> BuiltPowerBI:
    nodes: dict[str, Node] = {}
    edges: list[Edge] = []
    warnings: list[Warning] = []

    model_prefix_parts = [project.project_name, "semantic_model"]

    for table in project.tables:
        table_qualified = normalize_identifier_parts([*model_prefix_parts, table.name])
        table_node_id = table_id(table_qualified)
        nodes[table_node_id] = Node(
            id=table_node_id,
            kind="table",
            name=table.name,
            qualified_name=table_qualified,
            evidence=[
                Evidence(
                    file=table.file,
                    location=table.name,
                    expression=table.m_expression[:500],
                    confidence="high",
                )
            ],
        )

        try:
            sources = extract_m_sources(table.m_expression)
        except PowerBIStructureError as exc:
            warnings.append(
                Warning(
                    code="m_parse_failed",
                    message=str(exc),
                    location=table.file,
                    subject_id=table_node_id,
                )
            )
            continue

        if not sources:
            warnings.append(
                Warning(
                    code="m_no_sources",
                    message="No upstream sources detected in M expression.",
                    location=table.file,
                    subject_id=table_node_id,
                )
            )

        for source in sources:
            if source.native_sql:
                for schema, sql_table in native_sql_table_refs(source.native_sql):
                    candidates = warehouse_table_fqn_candidates(
                        database=source.database,
                        schema=schema,
                        table=sql_table,
                    )
                    if warehouse_table_ids:
                        upstream_id, match_status = resolve_table_match(
                            candidates,
                            warehouse_table_ids,
                            alias_map=alias_map,
                        )
                    else:
                        upstream_id, match_status = None, "unresolved"
                    edges.append(
                        Edge(
                            kind="feeds",
                            source_id=upstream_id or f"table:{candidates[0]}",
                            target_id=table_node_id,
                            label="native_sql",
                            confidence="medium" if upstream_id else "low",
                            match_status=match_status,
                            evidence=[
                                Evidence(
                                    file=table.file,
                                    expression=source.native_sql[:500],
                                    confidence="medium",
                                )
                            ],
                        )
                    )
                continue

            if not source.table:
                continue

            candidates = warehouse_table_fqn_candidates(
                database=source.database,
                schema=source.schema,
                table=source.table,
            )
            if warehouse_table_ids:
                upstream_id, match_status = resolve_table_match(
                    candidates,
                    warehouse_table_ids,
                    alias_map=alias_map,
                )
            else:
                upstream_id, match_status = None, "unresolved"
            edges.append(
                Edge(
                    kind="feeds",
                    source_id=upstream_id or f"table:{candidates[0]}",
                    target_id=table_node_id,
                    label=source.connector,
                    confidence="high" if match_status == "resolved" else "low",
                    match_status=match_status,
                    evidence=[
                        Evidence(
                            file=table.file,
                            location=source.step_name,
                            confidence="high",
                        )
                    ],
                )
            )

    if project.report_path:
        report = parse_report_folder(project.report_path)
        report_qualified = normalize_identifier_parts(
            [project.project_name, report.report_name]
        )
        report_node_id = report_id(report_qualified)
        nodes[report_node_id] = Node(
            id=report_node_id,
            kind="report",
            name=report.report_name,
            qualified_name=report_qualified,
        )

        for page_key, page_info in report.pages.items():
            page_node = page_id(report_qualified, page_key)
            nodes[page_node] = Node(
                id=page_node,
                kind="page",
                name=page_key,
                qualified_name=f"{report_qualified}.{page_key}",
            )
            edges.append(
                Edge(
                    kind="references",
                    source_id=report_node_id,
                    target_id=page_node,
                    label="contains_page",
                )
            )

        for binding in report.bindings:
            visual_node = visual_id(
                report_qualified, binding.page_id or "", binding.visual_id
            )
            nodes[visual_node] = Node(
                id=visual_node,
                kind="visual",
                name=binding.visual_id,
                qualified_name=f"{report_qualified}.{binding.page_id}.{binding.visual_id}",
            )
            if binding.page_id:
                edges.append(
                    Edge(
                        kind="references",
                        source_id=page_id(report_qualified, binding.page_id),
                        target_id=visual_node,
                        label="contains_visual",
                    )
                )

            if binding.table_name:
                target_table = table_id(
                    normalize_identifier_parts(
                        [*model_prefix_parts, binding.table_name]
                    )
                )
                edges.append(
                    Edge(
                        kind="references",
                        source_id=visual_node,
                        target_id=target_table,
                        label=f"{binding.field_kind}:{binding.field_name}",
                        confidence="high",
                    )
                )
                if binding.field_kind == "measure":
                    warnings.append(
                        Warning(
                            code="dax_deferred",
                            message=(
                                f"Measure '{binding.field_name}' binding recorded; "
                                "DAX lineage deferred in V1."
                            ),
                            subject_id=visual_node,
                        )
                    )

        for message in report.warnings:
            warnings.append(
                Warning(
                    code="report_parse_warning",
                    message=message,
                    location=project.report_path,
                )
            )

    artifact = CatalogArtifact(
        nodes=sorted(nodes.values(), key=lambda node: node.id),
        edges=sorted(
            edges, key=lambda edge: (edge.kind, edge.source_id, edge.target_id)
        ),
        warnings=sorted(
            warnings,
            key=lambda warning: (warning.code, warning.message, warning.location or ""),
        ),
    )
    unresolved = sum(
        1 for edge in artifact.edges if edge.match_status in ("unresolved", "ambiguous")
    )
    summary = PowerBISummary(
        project_name=project.project_name,
        table_count=sum(1 for node in artifact.nodes if node.kind == "table"),
        visual_count=sum(1 for node in artifact.nodes if node.kind == "visual"),
        upstream_source_count=sum(
            1
            for edge in artifact.edges
            if edge.kind == "feeds" and edge.source_id.startswith("table:")
        ),
        unresolved_join_count=unresolved,
    )
    return BuiltPowerBI(artifact=artifact, summary=summary)


def _resolve_unresolved_feeds_edge(
    edge: Edge,
    warehouse_table_ids: set[str],
    alias_map: AliasMap | None,
) -> Edge:
    if edge.kind != "feeds" or edge.match_status == "resolved":
        return edge
    placeholder = edge.source_id.removeprefix("table:")
    candidates = warehouse_table_fqn_candidates_from_name(placeholder)
    matched_id, status = resolve_table_match(
        candidates,
        warehouse_table_ids,
        alias_map=alias_map,
    )
    return Edge(
        kind=edge.kind,
        source_id=matched_id or edge.source_id,
        target_id=edge.target_id,
        label=edge.label,
        confidence="high" if status == "resolved" else edge.confidence,
        match_status=status,
        evidence=edge.evidence,
    )


def _resolve_cross_graph_edges(
    artifact: CatalogArtifact,
    warehouse_table_ids: set[str],
    alias_map: AliasMap | None,
) -> CatalogArtifact:
    updated_edges = [
        _resolve_unresolved_feeds_edge(edge, warehouse_table_ids, alias_map)
        for edge in artifact.edges
    ]
    return CatalogArtifact(
        version=artifact.version,
        nodes=artifact.nodes,
        edges=updated_edges,
        warnings=artifact.warnings,
    )
